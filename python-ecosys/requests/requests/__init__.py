import socket


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


class Response:
    def __init__(self, f):
        self.raw = f
        self.encoding = "utf-8"
        self._cached = None

    def close(self):
        if self.raw:
            self.raw.close()
            self.raw = None
        self._cached = None

    @property
    def content(self):
        if self._cached is None:
            try:
                self._cached = self.raw.read()
            finally:
                self.raw.close()
                self.raw = None
        return self._cached

    @property
    def text(self):
        return str(self.content, self.encoding)

    def json(self):
        import json

        return json.loads(self.content)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def request(
    method,
    url,
    data=None,
    json=None,
    headers=None,
    stream=None,
    auth=None,
    timeout=None,
    parse_headers=True,
):
    if headers is None:
        headers = {}
    else:
        headers = headers.copy()

    redirect = None  # redirection url, None means no redirection
    chunked_data = data and getattr(data, "__next__", None) and not getattr(data, "__len__", None)

    if auth is not None:
        import binascii

        username, password = auth
        formatted = b"{}:{}".format(username, password)
        formatted = str(binascii.b2a_base64(formatted)[:-1], "ascii")
        headers["Authorization"] = "Basic {}".format(formatted)

    try:
        proto, dummy, host, path = url.split("/", 3)
    except ValueError:
        proto, dummy, host = url.split("/", 2)
        path = ""
    if proto == "http:":
        port = 80
    elif proto == "https:":
        import tls

        port = 443
    else:
        raise ValueError("Unsupported protocol: " + proto)

    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    ai = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
    ai = ai[0]

    s = socket.socket(ai[0], socket.SOCK_STREAM, ai[2])

    if timeout is not None:
        # Note: settimeout is not supported on all platforms, will raise
        # an AttributeError if not available.
        s.settimeout(timeout)

    try:
        s.connect(ai[-1])
        if proto == "https:":
            context = tls.SSLContext(tls.PROTOCOL_TLS_CLIENT)
            context.verify_mode = tls.CERT_NONE
            s = context.wrap_socket(s, server_hostname=host)
        s.write(b"%s /%s HTTP/1.1\r\n" % (method, path))

        if "Host" not in headers:
            headers["Host"] = host

        if json is not None:
            assert data is None
            from json import dumps

            data = dumps(json)

            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/json"

        if data:
            if chunked_data:
                if "Transfer-Encoding" not in headers and "Content-Length" not in headers:
                    headers["Transfer-Encoding"] = "chunked"
            elif "Content-Length" not in headers:
                headers["Content-Length"] = str(len(data))

        if "Connection" not in headers:
            headers["Connection"] = "close"

        # Iterate over keys to avoid tuple alloc
        for k in headers:
            s.write(k)
            s.write(b": ")
            s.write(headers[k])
            s.write(b"\r\n")

        s.write(b"\r\n")

        if data:
            if chunked_data:
                if headers.get("Transfer-Encoding", None) == "chunked":
                    for chunk in data:
                        s.write(b"%x\r\n" % len(chunk))
                        s.write(chunk)
                        s.write(b"\r\n")
                    s.write("0\r\n\r\n")
                else:
                    for chunk in data:
                        s.write(chunk)
            else:
                s.write(data)

        status, reason = read_status_line(s)
        resp_d = read_headers(s, parse_headers)

        if not 200 <= status <= 299:
            location = None
            if resp_d:
                for k in resp_d:
                    if k.lower() == "location":
                        location = resp_d[k]
                        break
            if location:
                if status in [301, 302, 303, 307, 308]:
                    redirect = location
                else:
                    raise NotImplementedError("Redirect %d not yet supported" % status)
    except OSError:
        s.close()
        raise

    if redirect:
        s.close()
        # Use the host specified in the redirect URL, as it may not be the same as the original URL.
        headers.pop("Host", None)
        if status in [301, 302, 303]:
            return request("GET", redirect, None, None, headers, stream)
        else:
            return request(method, redirect, data, json, headers, stream)
    else:
        resp = Response(open_body(s, resp_d))
        resp.status_code = status
        resp.reason = reason
        if parse_headers is not False:
            resp.headers = resp_d
        return resp


def head(url, **kw):
    return request("HEAD", url, **kw)


def get(url, **kw):
    return request("GET", url, **kw)


def post(url, **kw):
    return request("POST", url, **kw)


def put(url, **kw):
    return request("PUT", url, **kw)


def patch(url, **kw):
    return request("PATCH", url, **kw)


def delete(url, **kw):
    return request("DELETE", url, **kw)
