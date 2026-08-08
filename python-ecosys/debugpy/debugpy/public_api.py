"""Public API for debugpy."""

import socket
import struct
import sys
from .common.constants import DEFAULT_HOST, DEFAULT_PORT
from .common.stream_transport import StreamTransport
from .server.debug_session import DebugSession, RestartRequest

_debug_session = None
# Bound-but-not-yet-accepted socket, held between listen() and the accept that
# wait_for_client() performs.
_listener = None
# Set by enable_restart() before a session exists, because the capability it
# controls is answered during the `initialize` that starts one.
_restart_supported = False


def listen(port=DEFAULT_PORT, host=DEFAULT_HOST):
    """Bind a listening socket and return the address it is bound to.

    Returns as soon as the socket is bound, WITHOUT waiting for a client, so
    the caller can publish the endpoint that a client then connects to. The
    accept and the `initialize` handshake happen in `wait_for_client()`. This
    matches CPython debugpy, where `listen()` reports the endpoint and
    `wait_for_client()` blocks.

    Args:
        port: Port number to listen on, or 0 to let the system choose
              (default: 5678)
        host: Host address to bind to (default: "127.0.0.1")

    Returns:
        (host, port) tuple of the actual bound address
    """
    global _listener

    if _listener is not None or _debug_session is not None:
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
        # Callers act on the endpoint this returns, so reporting a port
        # nothing can connect to would be worse than refusing: substituting
        # DEFAULT_PORT here would advertise an address the socket is not
        # bound to. Ask for an explicit port on a target whose getsockname()
        # cannot report the OS-assigned one.
        listener.close()
        raise OSError(
            "port=0 needs getsockname() to report the assigned port, which "
            "this target does not implement; pass an explicit port"
        )

    _listener = listener
    print(f"Debugpy listening on {host}:{port}")
    return (host, port)


def listen_stream(reader, writer=None):
    """Start a debug session directly on an already-open stream, no TCP.

    For a board with a second CDC interface dedicated to DAP: `reader`/`writer`
    are that interface's stream (the same object for both if it is one
    read/write file, as `open(dev, "r+b")` gives on the unix port). Unlike
    `listen()`, the stream is already connected - there is no bind/accept
    step, so `wait_for_client()` goes straight to the initialize/
    configurationDone handshake.
    """
    global _listener

    if _listener is not None or _debug_session is not None:
        raise RuntimeError("Already listening for debugger")

    _listener = StreamTransport(reader, writer)
    print("Debugpy listening on stream")
    return _listener


def _accept_and_initialize():
    """Accept the pending connection and handle the client's `initialize`.

    Split out of `listen()` so the endpoint can be published before a client
    exists. Returns True once a session is ready.
    """
    global _debug_session, _listener

    if _listener is None:
        print("[DAP] no listening socket; call listen() first")
        return False

    listener, _listener = _listener, None
    # A stream transport (listen_stream()) is already connected - there is no
    # separate client socket to accept, and no separate listener to close off
    # once accepted (it IS the connection).
    is_stream = isinstance(listener, StreamTransport)
    client_sock = None
    try:
        if is_stream:
            client_sock = listener
        else:
            client_sock, client_addr = listener.accept()
            print(f"Debugger connected from {format_client_addr(client_addr)}")

        _debug_session = DebugSession(client_sock, is_stream, _restart_supported)

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
        return True

    except Exception as e:
        print(f"[DAP] Connection error: {e}")
        if client_sock is not None:
            client_sock.close()
        _debug_session = None
        return False
    finally:
        # This is a single-connection server, so stop listening once the
        # client is accepted. Not for a stream transport: it IS the client
        # socket, still needed by the session this just started.
        if not is_stream:
            listener.close()


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
    """Block until a client has attached and finished configuring.

    Accepts the connection and handles `initialize` (both deferred by
    `listen()` so the endpoint can be published first), then waits for
    `configurationDone`. Breakpoints the client sets before then are honoured
    because this drains the socket the whole time it waits. Returns True once
    configurationDone arrives, False after a bounded timeout (logged, not
    silent) or if nothing is listening.
    """
    global _debug_session
    if _debug_session is None and not _accept_and_initialize():
        print("[DAP] wait_for_client: nothing is listening, nothing to wait for")
        return False
    if timeout_s is None:
        return _debug_session.wait_for_client()
    return _debug_session.wait_for_client(timeout_s)


def enable_restart():
    """Declare that this process can re-run its target, so `restart` is offered.

    Must be called before `wait_for_client()`: the capability is answered in the
    `initialize` request, which that accepts and handles. Only the code that
    owns the run loop can honour a restart, so nothing else turns this on.
    """
    global _restart_supported
    _restart_supported = True
    if _debug_session is not None:
        _debug_session.restart_supported = True


def wait_for_restart():
    """Block between runs until a restart is requested, or the client leaves.

    Returns True if the target should be run again, False if there is no client
    left to run it for. The caller must not be traced while it waits (see
    DebugSession.wait_for_restart).
    """
    if _debug_session is None:
        return False
    return _debug_session.wait_for_restart()


def console(text):
    """Show `text` in the client's debug console, if a session is connected.

    A no-op with no session, so a target can report progress unconditionally
    without caring whether it is being debugged. See DebugSession.console for
    why anything worth saying goes here as well as to stdout.
    """
    if _debug_session is not None:
        _debug_session.console(text)


def get_capabilities():
    """Return the firmware capability dict (settrace/save_names/set_local/f_back).

    Uses the active session's probe result if a session exists, otherwise
    probes directly. Values always come from probing the running
    interpreter, never from a build/variant name - except `serial_dap`,
    which comes from whichever of `_debug_session`/`_listener` exists: the
    boot script calls this between `listen()`/`listen_stream()` and
    `wait_for_client()` (before a session exists), so `_listener` is the
    only place the channel choice is recorded yet.

    Call this after `listen()`/`listen_stream()`; called before either, or
    after `disconnect()`/a `wait_for_client()` timeout has cleared both
    globals, `serial_dap` reports `False` regardless of which channel a
    prior session used.
    """
    global _debug_session
    if _debug_session is not None:
        return _debug_session.capabilities
    return DebugSession.probe_capabilities(isinstance(_listener, StreamTransport))


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
