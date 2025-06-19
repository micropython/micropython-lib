"""Public API for debugpy."""

import socket
import sys
from .common.constants import DEFAULT_HOST, DEFAULT_PORT
from .server.debug_session import DebugSession

_debug_session = None


def listen(port=DEFAULT_PORT, host=DEFAULT_HOST):
    """Start listening for debugger connections.
    
    Args:
        port: Port number to listen on (default: 5678)
        host: Host address to bind to (default: "127.0.0.1")
        
    Returns:
        (host, port) tuple of the actual listening address
    """
    global _debug_session

    if _debug_session is not None:
        raise RuntimeError("Already listening for debugger")

    # Create listening socket
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except:
        pass  # Not supported in MicroPython

    # Use getaddrinfo for MicroPython compatibility
    addr_info = socket.getaddrinfo(host, port)
    addr = addr_info[0][-1]  # Get the sockaddr
    listener.bind(addr)
    listener.listen(1)

    # getsockname not available in MicroPython, use original values
    print(f"Debugpy listening on {host}:{port}")

    # Wait for connection
    client_sock = None
    try:
        client_sock, client_addr = listener.accept()
        print(f"Debugger connected from {client_addr}")

        # Create debug session
        _debug_session = DebugSession(client_sock)

        # Handle just the initialize request, then return immediately
        print("[DAP] Waiting for initialize request...")
        init_message = _debug_session.channel.recv_message()
        if init_message and init_message.get('command') == 'initialize':
            _debug_session._handle_message(init_message)
            print("[DAP] Initialize request handled - returning control immediately")
        else:
            print(f"[DAP] Warning: Expected initialize, got {init_message}")

        # Set socket to non-blocking for subsequent message processing
        _debug_session.channel.sock.settimeout(0.001)

        print("[DAP] Debug session ready - all other messages will be handled in trace function")

    except Exception as e:
        print(f"[DAP] Connection error: {e}")
        if client_sock:
            client_sock.close()
            _debug_session = None
    finally:
        # Only close the listener, not the client connection
        listener.close()

    return (host, port)


def wait_for_client():
    """Wait for the debugger client to connect and initialize."""
    global _debug_session
    if _debug_session:
        _debug_session.wait_for_client()


def breakpoint():
    """Trigger a breakpoint in the debugger."""
    global _debug_session
    if _debug_session:
        _debug_session.trigger_breakpoint()
    else:
        # Fallback to built-in breakpoint if available
        if hasattr(__builtins__, 'breakpoint'):
            __builtins__.breakpoint()


def debug_this_thread():
    """Enable debugging for the current thread."""
    global _debug_session
    if _debug_session:
        _debug_session.debug_this_thread()
    else:
        # Install trace function even if no session yet
        if hasattr(sys, 'settrace'):
            sys.settrace(_default_trace_func)
        else:
            raise RuntimeError("MICROPY_PY_SYS_SETTRACE required")


def _default_trace_func(frame, event, arg):
    """Default trace function when no debug session is active."""
    # Just return None to continue execution
    return None



def is_client_connected():
    """Check if a debugger client is connected."""
    global _debug_session
    return _debug_session is not None and _debug_session.is_connected()


def disconnect():
    """Disconnect from the debugger client."""
    global _debug_session
    if _debug_session:
        _debug_session.disconnect()
        _debug_session = None
