#!/usr/bin/env python3
"""Test script for VS Code debugging with MicroPython debugpy."""

import sys

sys.path.insert(0, '.')

import debugpy

foo = 42
bar = "Hello, MicroPython!"

def fibonacci(n):
    """Calculate fibonacci number (iterative for efficiency)."""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def debuggable_code():
    """The actual code we want to debug - wrapped in a function so sys.settrace will trace it."""
    global foo
    print("Starting debuggable code...")
    
    # Test data - set breakpoint here (using smaller numbers to avoid slow fibonacci)
    numbers = [3, 4, 5]
    for i, num in enumerate(numbers):
        print(f"Calculating fibonacci({num})...")
        result = fibonacci(num)  # <-- SET BREAKPOINT HERE (line 26)
        foo += result  # Modify foo to see if it gets traced
        print(f"fibonacci({num}) = {result}")
        print(sys.implementation)
        import machine
        print(dir(machine))
    
    # Test manual breakpoint
    print("\nTriggering manual breakpoint...")
    debugpy.breakpoint()
    print("Manual breakpoint triggered!")
    
    print("Test completed successfully!")

def main():
    print("MicroPython VS Code Debugging Test")
    print("==================================")
    
    # Start debug server
    try:
        debugpy.listen()
        print("Debug server attached on 127.0.0.1:5678")
        print("Connecting back to VS Code debugger now...")
        # print("Set a breakpoint on line 26: 'result = fibonacci(num)'")
        # print("Press Enter to continue after connecting debugger...")
        # try:
        #     input()
        # except:
        #     pass
        
        # Enable debugging for this thread
        debugpy.debug_this_thread()
        
        # Give VS Code a moment to set breakpoints after attach
        print("\nGiving VS Code time to set breakpoints...")
        import time
        time.sleep(2)
        
        # Call the debuggable code function so it gets traced
        debuggable_code()
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()