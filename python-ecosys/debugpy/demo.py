#!/usr/bin/env python3
"""Simple demo of MicroPython debugpy functionality."""

import sys
sys.path.insert(0, '.')

import debugpy

def simple_function(a, b):
    """A simple function to demonstrate debugging."""
    result = a + b
    print(f"Computing {a} + {b} = {result}")
    return result

def main():
    print("MicroPython debugpy Demo")
    print("========================")
    print()
    
    # Demonstrate trace functionality
    print("1. Testing trace functionality:")
    
    def trace_function(frame, event, arg):
        if event == 'call':
            print(f"  -> Entering function: {frame.f_code.co_name}")
        elif event == 'line':
            print(f"  -> Executing line {frame.f_lineno} in {frame.f_code.co_name}")
        elif event == 'return':
            print(f"  -> Returning from {frame.f_code.co_name} with value: {arg}")
        return trace_function
    
    # Enable tracing
    sys.settrace(trace_function)
    
    # Execute traced function
    result = simple_function(5, 3)
    
    # Disable tracing
    sys.settrace(None)
    
    print(f"Result: {result}")
    print()
    
    # Demonstrate debugpy components
    print("2. Testing debugpy components:")
    
    # Test PDB adapter
    from debugpy.server.pdb_adapter import PdbAdapter
    pdb = PdbAdapter()
    
    # Set some mock breakpoints
    breakpoints = pdb.set_breakpoints("demo.py", [{"line": 10}, {"line": 15}])
    print(f"  Set breakpoints: {len(breakpoints)} breakpoints")
    
    # Test messaging
    from debugpy.common.messaging import JsonMessageChannel
    print("  JsonMessageChannel available")
    
    print()
    print("3. debugpy is ready for VS Code integration!")
    print("   To use with VS Code:")
    print("   - Import debugpy in your script")
    print("   - Call debugpy.listen() to start the debug server")
    print("   - Connect VS Code using the 'Attach to MicroPython' configuration")
    print("   - Set breakpoints and debug normally")
    
if __name__ == "__main__":
    main()
