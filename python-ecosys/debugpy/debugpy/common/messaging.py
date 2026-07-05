"""JSON message handling for DAP protocol."""

import json
from .constants import MSG_TYPE_REQUEST, MSG_TYPE_RESPONSE, MSG_TYPE_EVENT


class JsonMessageChannel:
    """Handles JSON message communication over a socket using DAP format."""

    def __init__(self, sock, debug_callback=None):
        self.sock = sock
        self.seq = 0
        self.closed = False
        self._recv_buffer = b""
        self._debug_print = debug_callback or (lambda x: None)  # Default to no-op

    def send_message(self, msg_type, command=None, **kwargs):
        """Send a DAP message."""
        if self.closed:
            return

        self.seq += 1
        message = {
            "seq": self.seq,
            "type": msg_type,
        }

        if command:
            if msg_type == MSG_TYPE_REQUEST:
                message["command"] = command
                if kwargs:
                    message["arguments"] = kwargs
            elif msg_type == MSG_TYPE_RESPONSE:
                message["command"] = command
                message["request_seq"] = kwargs.get("request_seq", 0)
                message["success"] = kwargs.get("success", True)
                if "body" in kwargs:
                    message["body"] = kwargs["body"]
                if "message" in kwargs:
                    message["message"] = kwargs["message"]
            elif msg_type == MSG_TYPE_EVENT:
                message["event"] = command
                if kwargs:
                    message["body"] = kwargs

        json_str = json.dumps(message)
        content = json_str.encode("utf-8")
        header = f"Content-Length: {len(content)}\r\n\r\n".encode("utf-8")

        try:
            self.sock.send(header + content)
        except OSError:
            self.closed = True

    def send_request(self, command, **kwargs):
        """Send a request message."""
        self.send_message(MSG_TYPE_REQUEST, command, **kwargs)

    def send_response(self, command, request_seq, success=True, body=None, message=None):
        """Send a response message."""
        kwargs = {"request_seq": request_seq, "success": success}
        if body is not None:
            kwargs["body"] = body
        if message is not None:
            kwargs["message"] = message

        self._debug_print(
            f"[DAP] SEND: response {command} (req_seq={request_seq}, success={success})"
        )
        if body:
            self._debug_print(f"[DAP]   body: {body}")
        if message:
            self._debug_print(f"[DAP]   message: {message}")

        self.send_message(MSG_TYPE_RESPONSE, command, **kwargs)

    def send_event(self, event, **kwargs):
        """Send an event message."""
        self._debug_print(f"[DAP] SEND: event {event}")
        if kwargs:
            self._debug_print(f"[DAP]   body: {kwargs}")
        self.send_message(MSG_TYPE_EVENT, event, **kwargs)

    def recv_message(self):
        """Receive a DAP message, or None if a full one isn't available yet.

        Called repeatedly against a socket with a short recv timeout (see
        `DebugSession.process_pending_messages`), so a single message's
        header and body routinely arrive across several calls. Everything
        read so far - including an already-located header - is kept in
        `self._recv_buffer` verbatim until the *entire* message (header +
        `Content-Length` body bytes) is available, and only then is it
        parsed and sliced off. Parsing the header again on each call is
        cheap and avoids having to separately persist "header already
        parsed, N body bytes still outstanding" state between calls: a
        prior version stripped the header out of the buffer as soon as it
        was found, which discarded that state and desynchronised framing
        for the rest of the connection whenever the body arrived in a
        later read than the header.
        """
        if self.closed:
            return None

        # Non-blocking top-up: pull in whatever is available right now
        # without blocking if there's nothing new yet.
        try:
            data = self.sock.recv(4096)
            if not data:
                # A truly empty read (as opposed to EAGAIN/EWOULDBLOCK,
                # handled below) means the peer closed the connection.
                self.closed = True
                return None
            self._recv_buffer += data
        except OSError as e:
            if not (hasattr(e, "errno") and e.errno in (11, 35)):  # EAGAIN, EWOULDBLOCK
                self.closed = True
                return None
            # No new data available right now - fall through and try to
            # parse a complete message out of whatever is already buffered.

        recv_buffer = self._recv_buffer
        header_end = recv_buffer.find(b"\r\n\r\n")
        if header_end < 0:
            return None  # Header not fully received yet.

        header_str = recv_buffer[:header_end].decode("utf-8")
        content_length = 0
        for line in header_str.split("\r\n"):
            if line.startswith("Content-Length:"):
                content_length = int(line.split(":", 1)[1].strip())
                break

        body_start = header_end + 4
        if len(recv_buffer) < body_start + content_length:
            return None  # Body not fully received yet.

        body = recv_buffer[body_start : body_start + content_length]
        self._recv_buffer = recv_buffer[body_start + content_length :]

        try:
            message = json.loads(body.decode("utf-8"))
            self._debug_print(
                f"[DAP] Successfully received message: {message.get('type')} {message.get('command', message.get('event', 'unknown'))}"
            )
            return message
        except (ValueError, UnicodeDecodeError) as e:
            print(f"[DAP] JSON parse error: {e}")
            return None

    def close(self):
        """Close the channel."""
        self.closed = True
        try:
            self.sock.close()
        except OSError:
            pass
