"""PDB adapter for integrating with MicroPython's trace system."""

import sys
import time
import os
import json
from ..common.constants import (
    TRACE_CALL, TRACE_LINE, TRACE_RETURN, TRACE_EXCEPTION,
    SCOPE_LOCALS, SCOPE_GLOBALS
)
VARREF_LOCALS = 1
VARREF_GLOBALS = 2
VARREF_LOCALS_SPECIAL = 3
VARREF_GLOBALS_SPECIAL = 4


# Also try checking by basename for path mismatches
def basename(path:str):
    return path.split('/')[-1] if '/' in path else path

# Check if this might be a relative path match
def ends_with_path(full_path:str, relative_path:str):
    """Check if full_path ends with relative_path components."""
    full_parts = full_path.replace('\\', '/').split('/')
    rel_parts = relative_path.replace('\\', '/').split('/')
    if len(rel_parts) > len(full_parts):
        return False
    return full_parts[-len(rel_parts):] == rel_parts

class PdbAdapter:
    """Adapter between DAP protocol and MicroPython's sys.settrace functionality."""

    def __init__(self):
        self.breakpoints : dict[str,dict[int,dict]] = {}  # filename -> {line_no: breakpoint_info}      # todo - simplify - reduce info stored 
        self.current_frame = None
        self.step_mode = None  # None, 'over', 'into', 'out'
        self.step_frame = None
        self.step_depth = 0
        self.hit_breakpoint = False
        self.continue_event = False
        self.variables_cache = {}  # frameId -> variables
        self.frame_id_counter = 1
        self.path_mappings : list[tuple[str,str]] = []  # runtime_path -> vscode_path mapping           # todo: move to session level 
        self.file_mappings : dict[str,str] = {}  # runtime_path -> vscode_path mapping                  # todo : merge with .breakpoints

    def _debug_print(self, message):
        """Print debug message only if debug logging is enabled."""
        if hasattr(self, '_debug_session') and self._debug_session.debug_logging: # type: ignore
            print(message)

    def _normalize_path(self, path:str):
        """Normalize a file path for consistent comparisons."""
        # Convert to absolute path if possible
        try:
            if hasattr(os.path, 'abspath'):
                path = os.path.abspath(path)
            elif hasattr(os.path, 'realpath'):
                path = os.path.realpath(path)
        except:
            pass
        # Ensure consistent separators
        path = path.replace('\\', '/')
        return path

    def set_trace_function(self, trace_func):
        """Install the trace function."""
        if hasattr(sys, 'settrace'):
            sys.settrace(trace_func)
        else:
            raise RuntimeError("sys.settrace not available")

    def _filename_as_debugee(self, path:str):
        # check if we have a 1:1 file mapping for this path
        if self.file_mappings.get(path):
            return self.file_mappings[path]
        # Check if we have a folder mapping for this path
        for runtime_path, vscode_path in self.path_mappings:
            if path.startswith(vscode_path):
                path = path.replace(vscode_path, runtime_path, 1)
                if path.startswith('//'):
                    path = path[1:]
        # If no mapping found, return the original path
        return path
    
    def _filename_as_debugger(self, path:str):
        """Convert a file path to the debugger's expected format."""
        path = path or ""
        if not path:
            return path
        if path.startswith('<'):
            # Special case for <stdin> or similar
            return path
        # Check if we have a 1:1 file mapping for this path
        for runtime_path, vscode_path in self.path_mappings:
            if path.startswith(runtime_path):
                path = path.replace(runtime_path, vscode_path, 1)
                return path

        # Check if we have a folder mapping for this path
        for runtime_path, vscode_path in self.path_mappings:
            if path.startswith(runtime_path):
                path = path.replace(runtime_path, vscode_path, 1)
                if path.startswith('//'):
                    path = path[1:]
        # If no mapping found, return the original path
        return path

    def set_breakpoints(self, filename:str, breakpoints:list[dict]):
        """Set breakpoints for a file."""
        self.breakpoints[filename] = {}
        local_name = self._filename_as_debugee(filename)
        self.file_mappings[local_name] = filename
        actual_breakpoints = []
        self._debug_print(f"[PDB] Setting breakpoints for file: {filename}")

        for bp in breakpoints:
            line = bp.get("line")
            if line:
                if local_name != filename:
                    self.breakpoints[local_name] = {}
                    self._debug_print(f"[>>>] Setting breakpoints for local: {local_name}:{line}")
                    self.breakpoints[local_name][line] = {
                        "line": line,
                        "verified": True,
                        "source": {"path": filename}
                    }
                self.breakpoints[filename][line] = {
                    "line": line,
                    "verified": True,
                    "source": {"path": filename}
                }
                actual_breakpoints.append({
                    "line": line,
                    "verified": True,
                    "source": {"path": filename}
                })

        self._debug_print(f"[PDB] Breakpoints set : {self.breakpoints}")

        return actual_breakpoints

    def should_stop(self, frame, event:str, arg):
        """Determine if execution should stop at this point."""
        self.current_frame = frame
        self.hit_breakpoint = False

        # Get frame information
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        # Check for exact filename match first
        if filename in self.breakpoints:
            if lineno in self.breakpoints[filename]:
                self._debug_print(f"[PDB] HIT BREAKPOINT (exact match) at {filename}:{lineno}")
                # Record the path mapping (in this case, they're already the same)
                self.file_mappings[filename] = self._filename_as_debugger(filename)
                self.hit_breakpoint = True
                return True
            # path/file.py matched - but not the line number - keep running
        else:
            # file not (yet) matched - this is slow so we do not want to do this often.
            # TODO: use builins - sys.path method to find the file
            # if we have a path match , but no breakpoints - add it to the file_mappings dict avoid this check
            self.breakpoints[filename] = {}  # Ensure the filename is in the breakpoints dict
            if not filename in self.file_mappings:
                self.file_mappings[filename] = self._filename_as_debugger(filename)
                self._debug_print(f"[PDB] add mapping for :'{filename}' -> '{self.file_mappings[filename]}'")

        # Check stepping
        if self.step_mode == 'into':
            if event in (TRACE_CALL, TRACE_LINE):
                self.step_mode = None
                return True

        elif self.step_mode == 'over':
            if event == TRACE_LINE and frame == self.step_frame:
                self.step_mode = None
                return True
            elif event == TRACE_RETURN and frame == self.step_frame:
                # Continue stepping in caller
                if hasattr(frame, 'f_back') and frame.f_back:
                    self.step_frame = frame.f_back
                else:
                    self.step_mode = None

        elif self.step_mode == 'out':
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
        self.step_mode = 'over'
        self.step_frame = self.current_frame
        self.continue_event = True

    def step_into(self):
        """Step into function calls."""
        self.step_mode = 'into'
        self.continue_event = True

    def step_out(self):
        """Step out of current function."""
        self.step_mode = 'out'
        self.step_frame = self.current_frame
        self.continue_event = True

    def pause(self):
        """Pause execution at next opportunity."""
        # This is handled by the debug session

    def wait_for_continue(self):
        """Wait for continue command (simplified implementation)."""
        # In a real implementation, this would block until continue
        # For MicroPython, we'll use a simple polling approach
        self.continue_event = False

        # Process DAP messages while waiting for continue
        self._debug_print("[PDB] Waiting for continue command...")
        while not self.continue_event:
            # Process any pending DAP messages (scopes, variables, etc.)
            if hasattr(self, '_debug_session'):
                self._debug_session.process_pending_messages() # type: ignore
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
            if "<stdin>" in filename or filename.endswith("debugpy.py") :
                hint = 'subtle'
            else :
                hint = 'normal'

            # self._debug_print("=" * 40 )
            # self._debug_print(f"[PDB] file mappings: {repr(self.file_mappings)} " )
            # self._debug_print(f"[PDB] path mappings: {repr(self.path_mappings)}" )
            # self._debug_print("=" * 40 )

            # Use the VS Code path if we have a mapping, otherwise use the original path
            debugger_path = self._filename_as_debugger(filename)
            if filename != debugger_path:
                self._debug_print(f"[PDB] Stack trace path mapping: {filename} -> {debugger_path}")
            # Create StackFrame info
            frames.append({
                "id": frame_id,
                "name": name,
                "source": {"path": debugger_path},
                "line": line,
                "column": 1,
                "endLine": line,
                "endColumn": 1,
                "presentationHint": hint
            })

            # Cache frame for variable access
            self.variables_cache[frame_id] = frame

            # MicroPython doesn't have f_back attribute
            if hasattr(frame, 'f_back'):
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
                "name": "Locals",
                "variablesReference": frame_id * 1000 + VARREF_LOCALS,
                "expensive": False
            },
            {
                "name": "Globals",
                "variablesReference": frame_id * 1000 + VARREF_GLOBALS ,
                "expensive": False
            }
        ]
        return scopes

    def _process_special_variables(self, var_dict):
        """Process special variables (those starting and ending with __)."""
        variables = []
        for name, value in var_dict.items():
            if name.startswith('__') and name.endswith('__'):
                try:
                    value_str = json.dumps(value)
                    type_str = type(value).__name__
                    variables.append({
                        "name": name,
                        "value": value_str,
                        "type": type_str,
                        "variablesReference": 0
                    })
                except Exception:
                    variables.append(self._var_error(name))
        return variables

    def _process_regular_variables(self, var_dict):
        """Process regular variables (excluding special ones)."""
        variables = []
        for name, value in var_dict.items():
            # Skip private/internal variables
            if name.startswith('__') and name.endswith('__'):
                continue
            try:
                value_str = json.dumps(value)
                type_str = type(value).__name__
                variables.append({
                    "name": name,
                    "value": value_str,
                    "type": type_str,
                    "variablesReference": 0
                })
            except Exception:
                variables.append(self._var_error(name))
        return variables

    @staticmethod
    def _var_error(name:str):
        return {"name": name, "value": "<error>", "type": "unknown", "variablesReference": 0 }

    @staticmethod
    def _special_vars(varref:int):
        return {"name": "Special", "value": "", "variablesReference": varref}

    def get_variables(self, variables_ref):
        """Get variables for a scope."""
        frame_id = variables_ref // 1000
        scope_type = variables_ref % 1000

        if frame_id not in self.variables_cache:
            return []

        frame = self.variables_cache[frame_id]

        # Handle special scope types first
        if scope_type == VARREF_LOCALS_SPECIAL:
            var_dict = frame.f_locals if hasattr(frame, 'f_locals') else {}
            return self._process_special_variables(var_dict)
        elif scope_type == VARREF_GLOBALS_SPECIAL:
            var_dict = frame.f_globals if hasattr(frame, 'f_globals') else {}
            return self._process_special_variables(var_dict)

        # Handle regular scope types with special folder
        variables = []
        if scope_type == VARREF_LOCALS:
            var_dict = frame.f_locals if hasattr(frame, 'f_locals') else {}
            variables.append(self._special_vars( VARREF_LOCALS_SPECIAL))
        elif scope_type == VARREF_GLOBALS:
            var_dict = frame.f_globals if hasattr(frame, 'f_globals') else {}
            variables.append(self._special_vars( VARREF_GLOBALS_SPECIAL))
        else:
            # Invalid reference, return empty
            return []

        # Add regular variables
        variables.extend(self._process_regular_variables(var_dict))
        return variables

    def evaluate_expression(self, expression, frame_id=None):
        """Evaluate an expression in the context of a frame."""
        if frame_id is not None and frame_id in self.variables_cache:
            frame = self.variables_cache[frame_id]
            globals_dict = frame.f_globals if hasattr(frame, 'f_globals') else {}
            locals_dict = frame.f_locals if hasattr(frame, 'f_locals') else {}
        else:
            # Use current frame
            frame = self.current_frame
            if frame:
                globals_dict = frame.f_globals if hasattr(frame, 'f_globals') else {}
                locals_dict = frame.f_locals if hasattr(frame, 'f_locals') else {}
            else:
                globals_dict = globals()
                locals_dict = {}
        try:
            # Evaluate the expression
            result = eval(expression, globals_dict, locals_dict)
            return result
        except Exception as e:
            raise Exception(f"Evaluation error: {e}")

    def cleanup(self):
        """Clean up resources."""
        self.variables_cache.clear()
        self.breakpoints.clear()
        if hasattr(sys, 'settrace'):
            sys.settrace(None)
