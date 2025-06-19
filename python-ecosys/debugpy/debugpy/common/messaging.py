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

        self._debug_print(f"[DAP] SEND: response {command} (req_seq={request_seq}, success={success})")
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
        """Receive a DAP message."""
        if self.closed:
            return None

        try:
            # Read headers
            while b"\r\n\r\n" not in self._recv_buffer:
                try:
                    data = self.sock.recv(1024)
                    if not data:
                        self.closed = True
                        return None
                    self._recv_buffer += data
                except OSError as e:
                    # Handle timeout and other socket errors
                    if hasattr(e, 'errno') and e.errno in (11, 35):  # EAGAIN, EWOULDBLOCK
                        return None  # No data available
                    self.closed = True
                    return None

            header_end = self._recv_buffer.find(b"\r\n\r\n")
            header_str = self._recv_buffer[:header_end].decode("utf-8")
            self._recv_buffer = self._recv_buffer[header_end + 4:]

            # Parse Content-Length
            content_length = 0
            for line in header_str.split("\r\n"):
                if line.startswith("Content-Length:"):
                    content_length = int(line.split(":", 1)[1].strip())
                    break

            if content_length == 0:
                return None

            # Read body
            while len(self._recv_buffer) < content_length:
                try:
                    data = self.sock.recv(content_length - len(self._recv_buffer))
                    if not data:
                        self.closed = True
                        return None
                    self._recv_buffer += data
                except OSError as e:
                    if hasattr(e, 'errno') and e.errno in (11, 35):  # EAGAIN, EWOULDBLOCK
                        return None
                    self.closed = True
                    return None

            body = self._recv_buffer[:content_length]
            self._recv_buffer = self._recv_buffer[content_length:]

            # Parse JSON
            try:
                message = json.loads(body.decode("utf-8"))
                self._debug_print(f"[DAP] Successfully received message: {message.get('type')} {message.get('command', message.get('event', 'unknown'))}")
                return message
            except (ValueError, UnicodeDecodeError) as e:
                print(f"[DAP] JSON parse error: {e}")
                return None

        except OSError as e:
            print(f"[DAP] Socket error in recv_message: {e}")
            self.closed = True
            return None

    def close(self):
        """Close the channel."""
        self.closed = True
        try:
            self.sock.close()
        except OSError:
            pass
