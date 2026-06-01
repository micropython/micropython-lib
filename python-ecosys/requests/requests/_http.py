# HTTP/1.x response parsing helpers for the requests package.

DEFAULT_MAX_BODY = 32 * 1024


class Headers:
    """HTTP headers with case-insensitive keys."""

    def __init__(self):
        self._data = {}

    def __setitem__(self, key, value):
        self._data[key.lower()] = value

    def __getitem__(self, key):
        return self._data[key.lower()]

    def get(self, key, default=None):
        return self._data.get(key.lower(), default)


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


def read_headers(stream, parse_headers=None):
    headers = Headers()
    while True:
        line = stream.readline()
        if not line or line == b"\r\n":
            break
        if parse_headers is False:
            continue
        if parse_headers is True:
            text = str(line, "utf-8")
            key, value = text.split(":", 1)
            headers[key] = value.strip()
        else:
            parse_headers(line, headers)
    return headers


def _read_exact(stream, length, max_remaining):
    out = b""
    while length > 0:
        if max_remaining is not None and max_remaining <= 0:
            raise ValueError("Response body exceeds max_body limit")
        chunk_len = length
        if max_remaining is not None and chunk_len > max_remaining:
            chunk_len = max_remaining
        chunk = stream.read(chunk_len)
        if not chunk:
            break
        out += chunk
        length -= len(chunk)
        if max_remaining is not None:
            max_remaining -= len(chunk)
    if length > 0:
        raise ValueError("Connection closed before Content-Length satisfied")
    return out, max_remaining


def _read_chunked(stream, max_remaining):
    out = b""
    while True:
        line = stream.readline()
        if not line:
            raise ValueError("Connection closed in chunked body")
        size_line = line.strip().split(b";", 1)[0]
        size = int(size_line, 16)
        if size == 0:
            stream.readline()
            break
        if max_remaining is not None and size > max_remaining:
            raise ValueError("Response body exceeds max_body limit")
        chunk, max_remaining = _read_exact(stream, size, max_remaining)
        out += chunk
        stream.readline()
    return out, max_remaining


def _read_until_close(stream, max_remaining):
    out = b""
    while True:
        if max_remaining is not None and max_remaining <= 0:
            raise ValueError("Response body exceeds max_body limit")
        to_read = 256
        if max_remaining is not None:
            to_read = min(to_read, max_remaining)
        chunk = stream.read(to_read)
        if not chunk:
            break
        out += chunk
        if max_remaining is not None:
            max_remaining -= len(chunk)
    return out, max_remaining


def read_body(stream, headers, max_body=None):
    """Read the response body according to Content-Length or chunked encoding."""
    max_remaining = max_body
    encoding = headers.get("transfer-encoding", "")
    if encoding:
        enc = encoding if isinstance(encoding, str) else str(encoding, "utf-8")
        if "chunked" in enc.lower():
            body, _ = _read_chunked(stream, max_remaining)
            return body
    content_length = headers.get("content-length")
    if content_length is not None:
        length = int(content_length)
        body, _ = _read_exact(stream, length, max_remaining)
        return body
    body, _ = _read_until_close(stream, max_remaining)
    return body


def resolve_redirect_url(base_url, location):
    """Resolve a redirect Location header against the request URL."""
    loc = location.strip()
    if loc.startswith("http:") or loc.startswith("https:"):
        return loc
    try:
        proto, dummy, host, path = base_url.split("/", 3)
    except ValueError:
        proto, dummy, host = base_url.split("/", 2)
        path = ""
    if loc.startswith("/"):
        return proto + "//" + host + loc
    if path and "/" in path:
        dir_path = path.rsplit("/", 1)[0]
        new_path = dir_path + "/" + loc
    else:
        new_path = loc
    return proto + "//" + host + "/" + new_path
