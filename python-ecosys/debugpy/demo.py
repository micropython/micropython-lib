"""Simple demo of MicroPython debugpy functionality.

Exercises the pieces a session is built from without starting one: the
firmware's trace hook, and the two package internals that sit on top of it.
Starting a server is the launcher's job, not a sample's.
"""

import sys

# The package is a sibling of this file, not installed.
sys.path.insert(0, ".")


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
        if event == "call":
            print(f"  -> Entering function: {frame.f_code.co_name}")
        elif event == "line":
            print(f"  -> Executing line {frame.f_lineno} in {frame.f_code.co_name}")
        elif event == "return":
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
    print("   To debug a program with VS Code:")
    print("   - Start the server first: listen(), then wait_for_client()")
    print("   - Import and run the program from there, so the client's")
    print("     breakpoints are already set when it starts")
    print("   - Attach with the 'Attach to MicroPython' configuration")
    print("   - See development_guide.md for the command")


if __name__ == "__main__":
    main()
