"""PDB adapter for integrating with MicroPython's trace system."""

import sys
import time
import os
from ..common.constants import (
    TRACE_CALL, TRACE_LINE, TRACE_RETURN, TRACE_EXCEPTION,
    SCOPE_LOCALS, SCOPE_GLOBALS
)


class PdbAdapter:
    """Adapter between DAP protocol and MicroPython's sys.settrace functionality."""
    
    def __init__(self):
        self.breakpoints = {}  # filename -> {line_no: breakpoint_info}
        self.current_frame = None
        self.step_mode = None  # None, 'over', 'into', 'out'
        self.step_frame = None
        self.step_depth = 0
        self.hit_breakpoint = False
        self.continue_event = False
        self.variables_cache = {}  # frameId -> variables
        self.frame_id_counter = 1
        self.path_mapping = {}  # runtime_path -> vscode_path mapping
        
    def _debug_print(self, message):
        """Print debug message only if debug logging is enabled."""
        if hasattr(self, '_debug_session') and self._debug_session.debug_logging:
            print(message)
    
    def _normalize_path(self, path):
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
            
    def set_breakpoints(self, filename, breakpoints):
        """Set breakpoints for a file."""
        self.breakpoints[filename] = {}
        actual_breakpoints = []
        
        # Debug log the breakpoint path
        self._debug_print(f"[PDB] Setting breakpoints for file: {filename}")
        
        for bp in breakpoints:
            line = bp.get("line")
            if line:
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
                
        return actual_breakpoints
        
    def should_stop(self, frame, event, arg):
        """Determine if execution should stop at this point."""
        self.current_frame = frame
        self.hit_breakpoint = False
        
        # Get frame information
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        
        # Debug: print filename and line for debugging
        if event == TRACE_LINE and lineno in [20, 21, 22, 23, 24]:  # Only log lines near our breakpoints
            self._debug_print(f"[PDB] Checking {filename}:{lineno} (event={event})")
            self._debug_print(f"[PDB] Available breakpoint files: {list(self.breakpoints.keys())}")
        
        # Check for exact filename match first
        if filename in self.breakpoints:
            if lineno in self.breakpoints[filename]:
                self._debug_print(f"[PDB] HIT BREAKPOINT (exact match) at {filename}:{lineno}")
                # Record the path mapping (in this case, they're already the same)
                self.path_mapping[filename] = filename
                self.hit_breakpoint = True
                return True
        
        # Also try checking by basename for path mismatches
        def basename(path):
            return path.split('/')[-1] if '/' in path else path
        
        # Check if this might be a relative path match
        def ends_with_path(full_path, relative_path):
            """Check if full_path ends with relative_path components."""
            full_parts = full_path.replace('\\', '/').split('/')
            rel_parts = relative_path.replace('\\', '/').split('/')
            if len(rel_parts) > len(full_parts):
                return False
            return full_parts[-len(rel_parts):] == rel_parts

        file_basename = basename(filename)
        self._debug_print(f"[PDB] Fallback basename match: '{file_basename}' vs available files")
        for bp_file in self.breakpoints:
            bp_basename = basename(bp_file)
            self._debug_print(f"[PDB]   Comparing '{file_basename}' == '{bp_basename}' ?")
            if bp_basename == file_basename:
                self._debug_print(f"[PDB]   Basename match found! Checking line {lineno} in {list(self.breakpoints[bp_file].keys())}")
                if lineno in self.breakpoints[bp_file]:
                    self._debug_print(f"[PDB] HIT BREAKPOINT (fallback basename match) at {filename}:{lineno} -> {bp_file}")
                    # Record the path mapping so we can report the correct path in stack traces
                    self.path_mapping[filename] = bp_file
                    self.hit_breakpoint = True
                    return True
            
            # Also check if the runtime path might be relative and the breakpoint path absolute
            if ends_with_path(bp_file, filename):
                self._debug_print(f"[PDB]   Relative path match: {bp_file} ends with {filename}")
                if lineno in self.breakpoints[bp_file]:
                    self._debug_print(f"[PDB] HIT BREAKPOINT (relative path match) at {filename}:{lineno} -> {bp_file}")
                    # Record the path mapping so we can report the correct path in stack traces
                    self.path_mapping[filename] = bp_file
                    self.hit_breakpoint = True
                    return True
                
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
        pass
        
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
                self._debug_session.process_pending_messages()
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
            
            # Use the VS Code path if we have a mapping, otherwise use the original path
            display_path = self.path_mapping.get(filename, filename)
            if filename != display_path:
                self._debug_print(f"[PDB] Stack trace path mapping: {filename} -> {display_path}")
            
            # Create frame info
            frames.append({
                "id": frame_id,
                "name": name,
                "source": {"path": display_path},
                "line": line,
                "column": 1,
                "endLine": line,
                "endColumn": 1
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
                "variablesReference": frame_id * 1000 + 1,
                "expensive": False
            },
            {
                "name": "Globals", 
                "variablesReference": frame_id * 1000 + 2,
                "expensive": False
            }
        ]
        return scopes
        
    def get_variables(self, variables_ref):
        """Get variables for a scope."""
        frame_id = variables_ref // 1000
        scope_type = variables_ref % 1000
        
        if frame_id not in self.variables_cache:
            return []
            
        frame = self.variables_cache[frame_id]
        variables = []
        
        if scope_type == 1:  # Locals
            var_dict = frame.f_locals if hasattr(frame, 'f_locals') else {}
        elif scope_type == 2:  # Globals
            var_dict = frame.f_globals if hasattr(frame, 'f_globals') else {}
        else:
            return []
            
        for name, value in var_dict.items():
            # Skip private/internal variables
            if name.startswith('__') and name.endswith('__'):
                continue
                
            try:
                value_str = repr(value)
                type_str = type(value).__name__
                
                variables.append({
                    "name": name,
                    "value": value_str,
                    "type": type_str,
                    "variablesReference": 0  # Simple implementation - no nested objects
                })
            except Exception:
                variables.append({
                    "name": name,
                    "value": "<error>",
                    "type": "unknown",
                    "variablesReference": 0
                })
                
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
