"""MicroPython debugpy implementation.

A minimal port of debugpy for MicroPython to enable VS Code debugging support.
This implementation focuses on the core DAP (Debug Adapter Protocol) functionality
needed for basic debugging operations like breakpoints, stepping, and variable inspection.
"""

__version__ = "0.1.0"

from .public_api import (
    breakpoint,
    debug_this_thread,
    disconnect,
    get_capabilities,
    is_client_connected,
    listen,
    listen_stream,
    wait_for_client,
)
from .common.constants import DEFAULT_HOST, DEFAULT_PORT

__all__ = [
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "breakpoint",
    "debug_this_thread",
    "disconnect",
    "get_capabilities",
    "is_client_connected",
    "listen",
    "listen_stream",
    "wait_for_client",
]
