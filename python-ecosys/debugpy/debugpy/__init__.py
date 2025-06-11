"""MicroPython debugpy implementation.

A minimal port of debugpy for MicroPython to enable VS Code debugging support.
This implementation focuses on the core DAP (Debug Adapter Protocol) functionality
needed for basic debugging operations like breakpoints, stepping, and variable inspection.
"""

__version__ = "0.1.0"

from .public_api import listen, wait_for_client, breakpoint, debug_this_thread
from .common.constants import DEFAULT_HOST, DEFAULT_PORT

__all__ = [
    "listen",
    "wait_for_client", 
    "breakpoint",
    "debug_this_thread",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
]
