"""A program to debug: ordinary MicroPython that knows nothing about debugpy.

Something else starts the session and then runs this. A launcher calls
`debugpy.listen()` and `debugpy.wait_for_client()`, imports this module and
calls `main()`; `development_guide.md` gives the command. That is the case
worth demonstrating - stopping in code with no debugger calls in it - and the
only one available when the program being debugged is on a device and the
client is not.
"""

import sys

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
    """A call to step into, a global to watch, and a loop to break inside."""
    global foo
    print("Starting debuggable code...")

    # Small numbers: fibonacci is here to be stepped through, not benchmarked.
    numbers = [3, 4, 5]
    for i, num in enumerate(numbers):
        print(f"[{i}] Calculating fibonacci({num})...")
        result = fibonacci(num)  # <-- SET BREAKPOINT HERE
        foo += result  # Modify foo to see if it gets traced
        print(f"fibonacci({num}) = {result}")

    print("Test completed successfully!")


def main():
    print("MicroPython VS Code Debugging Test")
    print("==================================")
    print(sys.implementation)
    debuggable_code()


if __name__ == "__main__":
    main()
