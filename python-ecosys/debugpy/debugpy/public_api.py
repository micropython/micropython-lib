"""Public API for debugpy."""

import socket
import struct
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

    # Resolve the actual bound port (needed when the caller asked for port 0 /
    # auto). Not every MicroPython port implements getsockname().
    requested_port = port
    try:
        bound_addr = listener.getsockname()
        if isinstance(bound_addr, (tuple, list)) and len(bound_addr) >= 2:
            port = bound_addr[1]
    except Exception:
        pass
    if requested_port == 0 and port == 0:
        # The caller asked for an OS-assigned port and this port has no way
        # to report what the OS actually picked. Advertising port 0 in the
        # handshake would tell the client to connect to a port that can
        # never accept a connection, so fall back to the documented default
        # instead - it is at least a real, well-known port to try.
        port = DEFAULT_PORT

    print(f"Debugpy listening on {host}:{port}")

    # Wait for connection
    client_sock = None
    try:
        client_sock, client_addr = listener.accept()
        print(f"Debugger connected from {format_client_addr(client_addr)}")

        # Create debug session
        _debug_session = DebugSession(client_sock)

        # Handle just the initialize request, then return immediately
        print("[DAP] Waiting for initialize request...")
        init_message = _debug_session.channel.recv_message()
        if init_message and init_message.get("command") == "initialize":
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
        # The accepted client socket is independent of the listener; closing
        # the listener does not affect it. This is a single-connection server,
        # so stop listening once the client is accepted.
        listener.close()

    return (host, port)


def format_client_addr(client_addr):
    """Format client address using socket module methods"""
    if isinstance(client_addr, (tuple, list)):
        # Already in (ip, port) format
        return f"{client_addr[0]}:{client_addr[1]}"
    elif isinstance(client_addr, bytes) and len(client_addr) >= 8:
        # Extract port (bytes 2-4, network byte order)
        port = struct.unpack("!H", client_addr[2:4])[0]
        # Extract IP address (bytes 4-8) using inet_ntoa
        ip_packed = client_addr[4:8]
        try:
            # inet_ntoa expects 4-byte string in network byte order
            ip_addr = socket.inet_ntoa(ip_packed)
            return f"{ip_addr}:{port}"
        except:
            # Fallback if inet_ntoa not available (MicroPython)
            ip_addr = ".".join(str(b) for b in ip_packed)
            return f"{ip_addr}:{port}"
    else:
        return str(client_addr)


def wait_for_client(timeout_s=None):
    """Block until the DAP client has finished configuring (configurationDone).

    Replaces a fixed sleep after debug_this_thread(): breakpoints the client
    sets before configurationDone are honoured because this drains the socket
    the whole time it waits. Returns True once configurationDone arrives,
    False after a bounded timeout (logged, not silent) or if no session is
    listening.
    """
    global _debug_session
    if _debug_session is None:
        print("[DAP] wait_for_client: no debug session is listening, nothing to wait for")
        return False
    if timeout_s is None:
        return _debug_session.wait_for_client()
    return _debug_session.wait_for_client(timeout_s)


def get_capabilities():
    """Return the firmware capability dict (settrace/save_names/set_local/f_back).

    Uses the active session's probe result if a session exists, otherwise
    probes directly. Values always come from probing the running
    interpreter, never from a build/variant name.
    """
    global _debug_session
    if _debug_session is not None:
        return _debug_session.capabilities
    return DebugSession.probe_capabilities()


def breakpoint():
    """Trigger a breakpoint in the debugger."""
    global _debug_session
    if _debug_session:
        _debug_session.trigger_breakpoint()
    else:
        # Fallback to built-in breakpoint if available
        if hasattr(__builtins__, "breakpoint"):
            __builtins__.breakpoint()


def debug_this_thread():
    """Enable debugging for the current thread."""
    global _debug_session
    if _debug_session:
        _debug_session.debug_this_thread()
    else:
        # Install trace function even if no session yet
        if hasattr(sys, "settrace"):
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
