"""PDB adapter for integrating with MicroPython's trace system."""

import os
import sys
import time

from micropython import const  # type: ignore[import-untyped]

from ..common.constants import (
    SCOPE_GLOBALS,
    SCOPE_LOCALS,
    STEP_INTO,
    STEP_OUT,
    STEP_OVER,
    TRACE_CALL,
    TRACE_EXCEPTION,
    TRACE_LINE,
    TRACE_RETURN,
)

Any = object

VARREF_LOCALS = const(1)
VARREF_GLOBALS = const(2)
VARREF_LOCALS_SPECIAL = const(3)
VARREF_GLOBALS_SPECIAL = const(4)

# New constants for complex variable references
VARREF_COMPLEX_BASE = const(10000)  # Base for complex variable references
MAX_CACHE_SIZE = const(50)  # Limit cache size for memory constraints


class VariableReferenceCache:
    """Lightweight cache for complex variable references optimized for MicroPython."""

    def __init__(self, max_size: int = MAX_CACHE_SIZE):
        self.cache: dict[int, Any] = {}
        self.insertion_order: list[int] = []  # Track insertion order for proper FIFO
        self.next_ref: int = VARREF_COMPLEX_BASE
        self.max_size: int = max_size

    def add_variable(self, value: Any) -> int:
        """Add a complex variable and return its reference ID."""
        # Clean cache if approaching limit
        if len(self.cache) >= self.max_size:
            self._cleanup_oldest()

        ref_id = self.next_ref
        self.cache[ref_id] = value
        self.insertion_order.append(ref_id)
        self.next_ref += 1
        return ref_id

    def get_variable(self, ref_id: int):  # -> Optional[Any]
        """Get variable by reference ID."""
        return self.cache.get(ref_id)

    def _cleanup_oldest(self) -> None:
        """Remove oldest entries to free memory - optimized for MicroPython."""
        if not self.cache or not self.insertion_order:
            return
        to_remove = max(1, len(self.cache) // 3)
        # Direct list slicing is more memory efficient than iteration
        keys_to_remove = self.insertion_order[:to_remove]
        # Batch delete for efficiency
        for key in keys_to_remove:
            self.cache.pop(key, None)  # Use pop with default to avoid KeyError
        # Update insertion order in one operation
        self.insertion_order = self.insertion_order[to_remove:]

    def clear(self) -> None:
        """Clear all cached variables."""
        self.cache.clear()
        self.insertion_order.clear()


# Also try checking by basename for path mismatches
def basename(path: str):
    return path.split("/")[-1] if "/" in path else path


# Check if this might be a relative path match
def ends_with_path(full_path: str, relative_path: str):
    """Check if full_path ends with relative_path components."""
    full_parts = full_path.replace("\\", "/").split("/")
    rel_parts = relative_path.replace("\\", "/").split("/")
    if len(rel_parts) > len(full_parts):
        return False
    return full_parts[-len(rel_parts) :] == rel_parts


# Augmented-assignment operators checked longest-first so e.g. "**=" is not
# mistaken for "*=" followed by stray text.
_AUG_ASSIGN_OPS = ("**=", "//=", ">>=", "<<=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "=")


def _is_ident_char(ch: str) -> bool:
    """True for `[A-Za-z0-9_]` - MicroPython's `str` has no `.isalnum()`."""
    return ch.isalpha() or ch.isdigit() or ch == "_"


def _assigned_name(statement: str):
    """Return the target name of a simple top-level assignment, or None.

    Recognises only `<identifier><op>...` where the identifier is the very
    first token and `<op>` is `=` or an augmented-assignment operator. This
    is a deliberately narrow, best-effort check - it does NOT catch:
    multi-target assignment (`a = b = 1`, only `a` is seen), tuple/list
    unpacking (`a, b = 1, 2`), attribute/subscript targets (`obj.x = 1`,
    `d[k] = 1`), `def`/`class` statements (which also bind a name), a
    `for`/`with ... as` binding, or an assignment that is not the first
    statement on the line (e.g. after `;`). Those forms pass through
    undetected; callers must treat a `None` result as "not proven safe",
    never as "proven no shadowing".
    """
    stripped = statement.strip()
    if not stripped or stripped[0].isdigit() or not _is_ident_char(stripped[0]):
        return None
    i = 1
    n = len(stripped)
    while i < n and _is_ident_char(stripped[i]):
        i += 1
    name = stripped[:i]
    rest = stripped[i:].lstrip()
    for op in _AUG_ASSIGN_OPS:
        if rest.startswith(op):
            if op == "=" and rest[1:2] == "=":
                return None  # `==`, a comparison, not an assignment
            return name
    return None


def _shadowed_local_warning(statement: str, locals_dict):
    """Build the honesty-rule warning for `statement`, or None if it doesn't apply.

    Fires when `_assigned_name` recognises a top-level assignment whose
    target name is also a key in `locals_dict` (the paused frame's
    `f_locals` snapshot): that name is about to be rebound in `f_globals`
    only, so the LOCAL of the same name stays exactly as it was. On
    firmware without local-name capture (`save_names` capability False),
    `locals_dict` keys are synthetic `local_N` placeholders rather than
    real identifiers, so a real name can never match and this warning
    silently cannot fire there - a known limitation, not a bug.
    """
    name = _assigned_name(statement)
    if name and name in locals_dict:
        return (
            f"Warning: '{name}' also exists as a LOCAL in this frame; "
            "the local is unchanged (statement ran against globals only)."
        )
    return None


class PdbAdapter:
    """Adapter between DAP protocol and MicroPython's sys.settrace functionality."""

    def __init__(self):
        self.breakpoints: dict[str, dict[int, dict]] = {}
        # filename -> {line_no: breakpoint_info}                # todo - simplify
        self.current_frame = None
        self.step_mode = None  # None, 'over', 'into', 'out'
        self.step_frame = None
        self.step_depth = 0
        self.paused = False
        self.hit_breakpoint = False
        self.continue_event = False
        self.variables_cache = {}  # frameId -> variables
        self.var_cache = VariableReferenceCache()  # Enhanced variable reference cache
        self.frame_id_counter = 1
        self.path_mappings: list[tuple[str, str]] = []
        # list of [runtime_path -> vscode_path mapping]
        self.file_mappings: dict[str, str] = {}
        # runtime_path -> vscode_path mapping                   # todo : merge with .breakpoints
        self.capabilities: dict = {}
        # set by DebugSession at session start (see DebugSession.probe_capabilities);
        # empty dict here means "not yet probed", treated as no set_local support

    def _debug_print(self, message):
        """Print debug message only if debug logging is enabled."""
        if hasattr(self, "_debug_session") and self._debug_session.debug_logging:  # type: ignore[attr-defined]
            print(message)

    def _normalize_path(self, path: str):
        """Normalize a file path for consistent comparisons."""
        # Convert to absolute path if possible
        try:
            if hasattr(os.path, "abspath"):
                path = os.path.abspath(path)
            elif hasattr(os.path, "realpath"):
                path = os.path.realpath(path)
        except:
            pass
        # Ensure consistent separators
        path = path.replace("\\", "/")
        return path

    def set_trace_function(self, trace_func):
        """Install the trace function."""
        if hasattr(sys, "settrace"):
            sys.settrace(trace_func)
        else:
            raise RuntimeError("sys.settrace not available")

    def _filename_as_debugee(self, path: str):
        """Translate an IDE-side (vscode) path to the runtime's own path.

        The first mapping whose `vscode_path` names `path` itself or a
        directory containing it wins - matched on a path-separator boundary,
        not a bare string prefix, so a sibling directory that merely shares
        the root's name (`/home/dev/src-old` against root `/home/dev/src`)
        is left untranslated instead of being rewritten into a device path
        that cannot exist. First-match-wins makes this the exact inverse of
        `_filename_as_debugger` below.
        """
        # check if we have a 1:1 file mapping for this path
        if self.file_mappings.get(path):
            return self.file_mappings[path]
        for runtime_path, vscode_path in self.path_mappings:
            if path == vscode_path or path.startswith(vscode_path + "/"):
                path = runtime_path + path[len(vscode_path) :]
                if path.startswith("//"):
                    path = path[1:]
                return path
        # If no mapping found, return the original path
        return path

    def _filename_as_debugger(self, path: str):
        """Translate a runtime path (`frame.f_code.co_filename`) to the IDE's path.

        Inverse of `_filename_as_debugee`: same first-match, boundary-aware
        rule, applied in the other direction.
        """
        path = path or ""
        if not path:
            return path
        if path.startswith("<"):
            # Special case for <stdin> or similar
            return path
        for runtime_path, vscode_path in self.path_mappings:
            if path == runtime_path or path.startswith(runtime_path + "/"):
                path = vscode_path + path[len(runtime_path) :]
                if path.startswith("//"):
                    path = path[1:]
                return path
        # If no mapping found, return the original path
        return path

    def set_breakpoints(self, filename: str, breakpoints: list[dict]):
        """Replace the breakpoint set for one file.

        DAP sends the whole set for a source on every request, so this
        replaces rather than adds, and an empty list is how a client removes
        every breakpoint in a file.

        The set is stored under both the path the client used and the name
        the debuggee knows the same file by, because `should_stop` matches
        whatever `frame.f_code.co_filename` reports. Both are replaced
        together: clearing only one leaves the other still armed.
        """
        local_name = self._filename_as_debugee(filename)
        self.file_mappings[local_name] = filename
        self.breakpoints[filename] = {}
        self.breakpoints[local_name] = {}

        actual_breakpoints = []
        self._debug_print(f"[PDB] Setting breakpoints for file: {filename} (as {local_name})")

        for bp in breakpoints:
            line = bp.get("line")
            if line:
                self.breakpoints[filename][line] = {}
                self.breakpoints[local_name][line] = {}
                actual_breakpoints.append(
                    {"line": line, "verified": True, "source": {"path": filename}}
                )

        self._debug_print(f"[PDB] Breakpoints set : {self.breakpoints}")

        return actual_breakpoints

    def should_stop(self, frame, event: str, arg):
        """Determine if execution should stop at this point."""
        # HOT path - no debug printing here
        self.current_frame = frame
        self.hit_breakpoint = False

        # Cache frame attributes to reduce lookup overhead
        _frame_code = frame.f_code
        _filename = _frame_code.co_filename
        _lineno = frame.f_lineno

        # Optimize dictionary lookups - use .get() to avoid double lookup
        file_breakpoints = self.breakpoints.get(_filename)
        if file_breakpoints and _lineno in file_breakpoints:
            # Only an event that is about to run this line counts as a hit.
            # `return` reports the last line the frame executed, so a breakpoint
            # on a function's final line would otherwise stop a second time on
            # the way out, on a frame that has already produced its value.
            # `call` reports the `def` line, which is the only event that can
            # ever match a breakpoint placed there.
            if event in (TRACE_CALL, TRACE_LINE):
                self._debug_print(f"[PDB] HIT BREAKPOINT (exact match) at {_filename}:{_lineno}")
                self.hit_breakpoint = True
                return True
        else:
            # file not (yet) matched - this is slow so we do not want to do this often.
            # TODO: use sys.path[] method to find the file, does not work for frozen ....
            # if we have a path match , but no breakpoints - add it to the file_mappings dict simplify this check
            if file_breakpoints is None:
                self.breakpoints[_filename] = {}  # Ensure the filename is in the breakpoints dict
            if _filename not in self.file_mappings:
                self.file_mappings[_filename] = self._filename_as_debugger(_filename)

        # Check stepping
        _step_mode = self.step_mode
        if _step_mode == STEP_INTO:
            if event in (TRACE_CALL, TRACE_LINE):
                self.step_mode = None
                return True

        elif _step_mode == STEP_OVER:
            if event == TRACE_LINE and frame == self.step_frame:
                self.step_mode = None
                return True
            elif event == TRACE_RETURN and frame == self.step_frame:
                # Continue stepping in caller
                if hasattr(frame, "f_back") and frame.f_back:
                    self.step_frame = frame.f_back
                else:
                    self.step_mode = None

        elif _step_mode == STEP_OUT:
            if event == TRACE_RETURN and frame == self.step_frame:
                self.step_mode = None
                return True

        return False

    def continue_execution(self):
        """Continue execution."""
        self.step_mode = None
        self.continue_event = True

    def step_over(self):
        """Step over (next line)."""
        self.step_mode = "over"
        self.step_frame = self.current_frame
        self.continue_event = True

    def step_into(self):
        """Step into function calls."""
        self.step_mode = "into"
        self.continue_event = True

    def step_out(self):
        """Step out of current function."""
        self.step_mode = "out"
        self.step_frame = self.current_frame
        self.continue_event = True

    def pause(self):
        """Pause execution at next opportunity."""
        # This is handled by the debug session
        self.paused = True

    def wait_for_continue(self):
        """Busy-poll until a continue/step command arrives, or the client is gone.

        No server thread services the socket, so this loop is what drains it
        while the target sits stopped. If the channel disappears (bridge
        killed, board reset) while stopped, waiting forever would wedge the
        target - `sys.settrace(None)` is dropped and the loop exits so the
        target resumes and the process/session can end cleanly instead of
        requiring a power cycle.
        """
        self.continue_event = False

        self._debug_print("[PDB] Waiting for continue command...")
        while not self.continue_event:
            session = getattr(self, "_debug_session", None)
            if session is None:
                break
            if not session.connected or session.channel.closed:
                self._debug_print("[PDB] wait_for_continue: connection lost, resuming target")
                if hasattr(sys, "settrace"):
                    sys.settrace(None)
                self.continue_event = True
                break
            session.process_pending_messages()  # type: ignore[arg-type]
            time.sleep(0.01)

    def get_stack_trace(self):
        """Get the current stack trace."""
        if not self.current_frame:
            return []

        frames = []
        frame = self.current_frame
        frame_id = 0

        while frame:
            filename = frame.f_code.co_filename
            name = frame.f_code.co_name
            line = frame.f_lineno
            if "<stdin>" in filename or filename.endswith("debugpy.py"):
                hint = "subtle"
            else:
                hint = "normal"

            # Use the VS Code path if we have a mapping, otherwise use the original path
            debugger_path = self._filename_as_debugger(filename)
            # Create StackFrame info
            frames.append(
                {
                    "id": frame_id,
                    "name": name,
                    "source": {"path": debugger_path},
                    "line": line,
                    "column": 1,
                    "endLine": line,
                    "endColumn": 1,
                    "presentationHint": hint,
                }
            )

            # Cache frame for variable access
            self.variables_cache[frame_id] = frame

            # MicroPython doesn't have f_back attribute
            if hasattr(frame, "f_back"):
                frame = frame.f_back
            else:
                # Only return the current frame for MicroPython
                break
            frame_id += 1

        return frames

    def get_scopes(self, frame_id):
        """Get variable scopes for a frame."""
        scopes = [
            {
                "name": SCOPE_LOCALS,
                "variablesReference": frame_id * 1000 + VARREF_LOCALS,
                "expensive": False,
            },
            {
                "name": SCOPE_GLOBALS,
                "variablesReference": frame_id * 1000 + VARREF_GLOBALS,
                "expensive": False,
            },
        ]
        return scopes

    def _process_special_variables(self, var_dict, read_only=False):
        """Process special variables (those starting and ending with __)."""
        variables = []
        for name, value in var_dict.items():
            if name.startswith("__") and name.endswith("__"):
                try:
                    # Use lightweight serialization instead of json.dumps
                    value_str = self._lightweight_serialize(value)
                    type_str = type(value).__name__
                    info = {
                        "name": name,
                        "value": value_str,
                        "type": type_str,
                        "variablesReference": 0,
                    }
                    if read_only:
                        info["presentationHint"] = {"attributes": ["readOnly"]}
                    variables.append(info)
                except Exception:
                    variables.append(self._var_error(name))
        return variables

    def _process_regular_variables(self, var_dict, read_only=False):
        """Process regular variables (excluding special ones) - optimized."""
        variables = []
        for name, value in var_dict.items():
            # Skip private/internal variables
            if name.startswith("__") and name.endswith("__"):
                continue
            # Use fast path for variable info generation
            info = self._get_variable_info_fast(name, value)
            if read_only:
                info["presentationHint"] = {"attributes": ["readOnly"]}
            variables.append(info)
        return variables

    def _is_expandable(self, value: Any) -> bool:
        """Check if a variable can be expanded (has child elements)."""
        return isinstance(value, (dict, list, tuple, set))

    def _get_preview(self, value: Any, fallback_text: str = "") -> str:
        """Get a 30-char preview of a variable value with '...' if truncated - optimized for MicroPython."""
        try:
            # Get repr and truncate to exactly 30 chars with "..." if needed
            repr_val = repr(value)
            if len(repr_val) <= 30:
                return repr_val
            else:
                return repr_val[:30] + "..."
        except (TypeError, ValueError, MemoryError):
            # Memory-safe fallback
            return fallback_text or f"<{type(value).__name__} object>"[:30]

    def _get_variable_info(self, name: str, value: Any) -> dict[str, str | int]:
        """Get DAP-compliant variable information with proper type handling."""
        try:
            # Handle expandable types
            if self._is_expandable(value):
                var_ref = self.var_cache.add_variable(value)
                preview = self._get_preview(value)  # Always use consistent preview

                if isinstance(value, dict):
                    return {
                        "name": name,
                        "value": preview,
                        "type": "dict",
                        "variablesReference": var_ref,
                        "namedVariables": len(value),
                        "indexedVariables": 0,
                    }
                elif isinstance(value, list):
                    return {
                        "name": name,
                        "value": preview,
                        "type": "list",
                        "variablesReference": var_ref,
                        "indexedVariables": len(value),
                        "namedVariables": 0,
                    }
                elif isinstance(value, tuple):
                    return {
                        "name": name,
                        "value": preview,
                        "type": "tuple",
                        "variablesReference": var_ref,
                        "indexedVariables": len(value),
                        "namedVariables": 0,
                    }
                elif isinstance(value, set):
                    return {
                        "name": name,
                        "value": preview,
                        "type": "set",
                        "variablesReference": var_ref,
                        "indexedVariables": len(value),
                        "namedVariables": 0,
                    }

            # Simple types - use the preview helper
            preview = self._get_preview(value)

            return {
                "name": name,
                "value": preview,
                "type": type(value).__name__,
                "variablesReference": 0,
            }
        except Exception:
            return self._var_error(name)

    def _get_variable_info_fast(self, name: str, value: Any) -> dict[str, str | int]:
        """Fast path for variable info generation with reduced allocations."""
        try:
            # Handle expandable types
            if self._is_expandable(value):
                var_ref = self.var_cache.add_variable(value)
                preview = self._get_preview(value)  # Always use consistent preview

                # Use pre-calculated length for better performance
                length = 0
                try:
                    length = len(value)  # type: ignore[arg-type]
                except:
                    pass

                # Return optimized structure based on type
                if isinstance(value, dict):
                    return {
                        "name": name,
                        "value": preview,
                        "type": "dict",
                        "variablesReference": var_ref,
                        "namedVariables": length if length < 1000 else 1000,  # Cap for performance
                        "indexedVariables": 0,
                    }
                elif isinstance(value, list):
                    return {
                        "name": name,
                        "value": preview,
                        "type": "list",
                        "variablesReference": var_ref,
                        "indexedVariables": min(length, 1000),  # Cap for performance
                        "namedVariables": 0,
                    }
                else:  # tuple, set, other
                    return {
                        "name": name,
                        "value": preview,
                        "type": type(value).__name__,
                        "variablesReference": var_ref,
                        "indexedVariables": min(length, 1000),
                        "namedVariables": 0,
                    }

            # Simple types - optimized path
            preview = self._get_preview(value)
            return {
                "name": name,
                "value": preview,
                "type": type(value).__name__,
                "variablesReference": 0,
            }
        except Exception:
            return {"name": name, "value": "<error>", "type": "unknown", "variablesReference": 0}

    def _expand_complex_variable(self, ref_id: int) -> list[dict[str, str | int]]:
        """Expand a complex variable into its child elements - optimized for memory."""
        value = self.var_cache.get_variable(ref_id)
        if value is None:
            return []

        variables = []
        try:
            if isinstance(value, dict):
                # Limit dictionary expansion to prevent memory exhaustion
                items = list(value.items())
                max_items = min(len(items), 50)  # Limit to 50 items max
                for i in range(max_items):
                    key, val = items[i]
                    key_str = str(key)[:50]  # Limit key string length
                    variables.append(self._get_variable_info(key_str, val))
                if len(items) > max_items:
                    variables.append(
                        {
                            "name": f"<{len(items) - max_items} more items>",
                            "value": "...",
                            "type": "info",
                            "variablesReference": 0,
                        }
                    )
            elif isinstance(value, (list, tuple)):
                # Limit list/tuple expansion
                max_items = min(len(value), 100)  # Limit to 100 items max
                for i in range(max_items):
                    variables.append(self._get_variable_info(f"[{i}]", value[i]))
                if len(value) > max_items:
                    variables.append(
                        {
                            "name": f"<{len(value) - max_items} more items>",
                            "value": "...",
                            "type": "info",
                            "variablesReference": 0,
                        }
                    )
            elif isinstance(value, set):
                # Handle set elements with size limit
                items = list(value)  # Convert once
                max_items = min(len(items), 50)
                for i in range(max_items):
                    variables.append(self._get_variable_info(f"<{i}>", items[i]))
                if len(items) > max_items:
                    variables.append(
                        {
                            "name": f"<{len(items) - max_items} more items>",
                            "value": "...",
                            "type": "info",
                            "variablesReference": 0,
                        }
                    )
        except Exception as e:
            # Return error info for debugging
            variables.append(
                {
                    "name": "error",
                    "value": f"Failed to expand: {str(e)[:50]}",  # Limit error message length
                    "type": "error",
                    "variablesReference": 0,
                }
            )

        return variables

    @staticmethod
    def _var_error(name: str):
        return {"name": name, "value": "<error>", "type": "unknown", "variablesReference": 0}

    @staticmethod
    def _special_vars(varref: int):
        return {"name": "Special", "value": "", "variablesReference": varref}

    def get_variables(self, variables_ref):
        """Get variables for a scope with enhanced complex variable support."""
        # Handle complex variable expansion
        if variables_ref >= VARREF_COMPLEX_BASE:
            return self._expand_complex_variable(variables_ref)

        frame_id = variables_ref // 1000
        scope_type = variables_ref % 1000

        if frame_id not in self.variables_cache:
            return []

        frame = self.variables_cache[frame_id]

        # Locals are read-only in DAP when this firmware has no _set_local
        # (STORY-1.3): the edit affordance is greyed out client-side instead
        # of setVariable failing with an error after the fact. Globals always
        # stay editable - global write-back works on every firmware.
        locals_read_only = not self.capabilities.get("set_local", False)

        # Handle special scope types first
        if scope_type == VARREF_LOCALS_SPECIAL:
            var_dict = frame.f_locals if hasattr(frame, "f_locals") else {}
            return self._process_special_variables(var_dict, read_only=locals_read_only)
        elif scope_type == VARREF_GLOBALS_SPECIAL:
            var_dict = frame.f_globals if hasattr(frame, "f_globals") else {}
            return self._process_special_variables(var_dict)

        # Handle regular scope types with special folder
        variables = []
        if scope_type == VARREF_LOCALS:
            var_dict = frame.f_locals if hasattr(frame, "f_locals") else {}
            variables.append(self._special_vars(frame_id * 1000 + VARREF_LOCALS_SPECIAL))
        elif scope_type == VARREF_GLOBALS:
            var_dict = frame.f_globals if hasattr(frame, "f_globals") else {}
            variables.append(self._special_vars(frame_id * 1000 + VARREF_GLOBALS_SPECIAL))
        else:
            # Invalid reference, return empty
            return []

        # Add regular variables with enhanced processing
        read_only = locals_read_only if scope_type == VARREF_LOCALS else False
        variables.extend(self._process_regular_variables(var_dict, read_only=read_only))
        return variables

    def evaluate_expression(self, expression, frame_id=None, context="watch"):
        """Evaluate a DAP `evaluate` request in the context of a frame.

        `watch`/`hover` (and any other/absent `context`) keep the original,
        read-only contract: `eval()` only - a statement is a `SyntaxError`,
        surfaced as an evaluation error, exactly as before this method
        gained statement support.

        `repl`/`clipboard` add statement execution: `eval()` is tried first
        (so a plain expression like `1 + 1` still returns a value); a
        `SyntaxError` falls back to `exec(expression, globals_dict)` against
        the frame's live `f_globals` only. The locals snapshot is
        deliberately never passed to `exec` as a namespace - `exec(code, g,
        l)` binds a top-level assignment into `l`, and `l` here is a
        disposable copy handed back to the caller and then discarded, so
        the assignment would silently vanish instead of taking effect. Only
        `globals_dict` is live, so a statement's top-level assignments land
        in the running module namespace and are visible to the target
        program after `continue`. See `_shadowed_local_warning` for the
        honesty-rule warning this implies when the assigned name also
        exists as a frame LOCAL.
        """
        if frame_id is not None and frame_id in self.variables_cache:
            frame = self.variables_cache[frame_id]
            globals_dict = frame.f_globals if hasattr(frame, "f_globals") else {}
            locals_dict = frame.f_locals if hasattr(frame, "f_locals") else {}
        else:
            # Use current frame
            frame = self.current_frame
            if frame:
                globals_dict = frame.f_globals if hasattr(frame, "f_globals") else {}
                locals_dict = frame.f_locals if hasattr(frame, "f_locals") else {}
            else:
                globals_dict = globals()
                locals_dict = {}

        try:
            result = eval(expression, globals_dict, locals_dict)
            return result
        except SyntaxError as e:
            if context not in ("repl", "clipboard"):
                raise Exception(f"Evaluation error: {e}")
        except Exception as e:
            raise Exception(f"Evaluation error: {e}")

        # Only repl/clipboard reach here, and only after eval() raised a
        # SyntaxError - try `expression` as a statement instead.
        try:
            exec(expression, globals_dict)
        except Exception as e:
            raise Exception(f"Evaluation error: {e}")

        warning = _shadowed_local_warning(expression, locals_dict)
        return warning if warning else ""

    def cleanup(self):
        """Clean up resources with enhanced cache management."""
        self.variables_cache.clear()
        self.var_cache.clear()  # Clear variable reference cache
        self.breakpoints.clear()
        if hasattr(sys, "settrace"):
            sys.settrace(None)

    def _lightweight_serialize(self, value):  # noqa: PLR0911
        """Lightweight serialization optimized for MicroPython memory constraints."""
        if value is None:
            return "None"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            # Simple escaping for strings - avoid full JSON complexity
            if len(value) > 30:
                escaped = value[:27].replace('"', '\\"').replace("\n", "\\n")
                return f'"{escaped}..."'
            else:
                escaped = value.replace('"', '\\"').replace("\n", "\\n")
                return f'"{escaped}"'
        elif isinstance(value, (list, tuple)):
            if len(value) == 0:
                return "[]" if isinstance(value, list) else "()"
            elif len(value) <= 3:
                # Show small collections in full
                items = [self._lightweight_serialize(item) for item in value]
                brackets = "[]" if isinstance(value, list) else "()"
                return f"{brackets[0]}{', '.join(items)}{brackets[1]}"
            else:
                # Show preview for large collections
                preview = f"{type(value).__name__}({len(value)} items)"
                return preview
        elif isinstance(value, dict):
            if len(value) == 0:
                return "{}"
            elif len(value) <= 2:
                # Show small dicts in preview form
                items = []
                for k, v in value.items():
                    key_str = self._lightweight_serialize(k)
                    val_str = self._lightweight_serialize(v)
                    items.append(f"{key_str}: {val_str}")
                return "{" + ", ".join(items) + "}"
            else:
                return f"dict({len(value)} items)"
        else:
            # Fallback for other types
            type_name = type(value).__name__
            try:
                repr_val = repr(value)
                if len(repr_val) > 30:
                    return f"<{type_name} object>"
                else:
                    return repr_val
            except:
                return f"<{type_name} object>"

    def set_variable(self, variables_ref: int, name: str, value: str) -> dict[str, str | int]:
        """Set a variable to a new value and return the updated variable info.

        This function can modify both global and local variables when using a MicroPython
        build with settrace and local variable modification support (sys._set_local_var).

        For global variables: Works reliably on all MicroPython builds.
        For local variables: Requires MicroPython build with C-level local variable support.
        """
        # Handle complex variable references (not supported for setting)
        if variables_ref >= VARREF_COMPLEX_BASE:
            raise Exception("Cannot set variables in complex object expansions")

        frame_id = variables_ref // 1000
        scope_type = variables_ref % 1000

        # Only allow setting variables in the topmost frame (frame_id = 0)
        if frame_id != 0:
            raise Exception("Variable modification is only allowed in the topmost frame")

        # Use the current frame for modification
        frame = self.current_frame
        if frame is None:
            raise Exception("No current frame available")

        # Get the appropriate variable contexts
        globals_dict = frame.f_globals if hasattr(frame, "f_globals") else {}
        locals_dict = frame.f_locals if hasattr(frame, "f_locals") else {}

        try:
            # Try to evaluate the new value as a Python expression
            try:
                new_value = eval(value, globals_dict, locals_dict)
            except:
                # If evaluation fails, treat as string literal
                new_value = value

            if scope_type == VARREF_GLOBALS or scope_type == VARREF_GLOBALS_SPECIAL:
                # Check if variable exists in globals
                if name not in globals_dict:
                    raise Exception(f"Global variable '{name}' not found")

                # For global variables, direct assignment works reliably
                globals_dict[name] = new_value
                self._debug_print(f"[PDB] Successfully set global variable '{name}' = {new_value}")

            elif scope_type == VARREF_LOCALS or scope_type == VARREF_LOCALS_SPECIAL:
                # Check if variable exists in locals
                if name not in locals_dict:
                    raise Exception(f"Local variable '{name}' not found")

                # Try to use the frame._set_local method to set local variables
                try:
                    if hasattr(frame, "_set_local"):
                        # Use the frame._set_local method (CPython-compatible API)
                        frame._set_local(name, new_value)
                        self._debug_print(
                            f"[PDB] Successfully set local variable '{name}' = {new_value}"
                        )
                    else:
                        # Fallback error if the method is not available
                        raise Exception(
                            f"Cannot modify local variable '{name}'. "
                            f"This MicroPython build doesn't support local variable modification. "
                            f"Please use a MicroPython build with settrace and local variable support."
                        )
                except Exception as inner_e:
                    # If frame.set_local fails, provide detailed error
                    raise Exception(
                        f"Failed to modify local variable '{name}': {inner_e}. "
                        f"Local variables in MicroPython are stored in internal code_state->state[] slots. "
                        f"Consider using global variables for reliable modification during debugging."
                    )

            else:
                raise Exception("Invalid scope reference")

            # Return the updated variable info
            return self._get_variable_info(name, new_value)

        except Exception as e:
            raise Exception(f"Failed to set variable '{name}': {e}")
