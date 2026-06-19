# HTTP/1.x response parsing helpers for the requests package.


def _header_get(headers, name):
    name_lower = name.lower()
    for k, v in headers.items():
        if k.lower() == name_lower:
            return v
    return None


def read_status_line(stream):
    line = stream.readline()
    if not line:
        raise ValueError("HTTP error: empty status line")
    parts = line.split(None, 2)
    if len(parts) < 2:
        raise ValueError("HTTP error: BadStatusLine:\n%s" % parts)
    status = int(parts[1])
    reason = parts[2].rstrip() if len(parts) > 2 else ""
    return status, reason


def read_headers(stream, parse_headers=True):
    resp_d = {}
    while True:
        line = stream.readline()
        if not line or line == b"\r\n":
            break
        if parse_headers is False:
            continue
        if parse_headers is True:
            text = str(line, "utf-8")
            key, value = text.split(":", 1)
            resp_d[key] = value.strip()
        else:
            parse_headers(line, resp_d)
    return resp_d


class BodyStream:
    def __init__(self, sock, remaining=None):
        self._sock = sock
        self._remaining = remaining

    def read(self, n=-1):
        if self._remaining == 0:
            return b""
        if n < 0:
            if self._remaining is not None:
                n = self._remaining
            data = self._sock.read(n)
        else:
            if self._remaining is not None and n > self._remaining:
                n = self._remaining
            data = self._sock.read(n)
        if self._remaining is not None:
            self._remaining -= len(data)
            if self._remaining > 0 and not data:
                raise ValueError("Connection closed before Content-Length satisfied")
        return data

    def close(self):
        self._sock.close()


def open_body(stream, headers):
    encoding = _header_get(headers, "transfer-encoding")
    if encoding and "chunked" in encoding.lower():
        raise ValueError("Unsupported Transfer-Encoding: %s" % encoding)
    content_length = _header_get(headers, "content-length")
    if content_length is not None:
        remaining = int(content_length)
    else:
        remaining = None
    return BodyStream(stream, remaining)
