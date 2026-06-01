import socket

from ._http import (
    DEFAULT_MAX_BODY,
    read_body,
    read_headers,
    read_status_line,
    resolve_redirect_url,
)


def _to_bytes(val):
    if isinstance(val, str):
        return val.encode()
    return val


class Response:
    def __init__(self, body=b""):
        self.raw = None
        self.encoding = "utf-8"
        self._cached = body

    def close(self):
        self.raw = None
        self._cached = None

    @property
    def content(self):
        return self._cached

    @property
    def text(self):
        return str(self.content, self.encoding)

    def json(self):
        import json

        return json.loads(self.content)


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
    max_body=DEFAULT_MAX_BODY,
):
    if headers is None:
        headers = {}
    else:
        headers = headers.copy()

    redirect = None
    chunked_data = data and getattr(data, "__next__", None) and not getattr(data, "__len__", None)

    if auth is not None:
        import binascii

        username, password = auth
        formatted = (username + ":" + password).encode()
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
        s.settimeout(timeout)

    try:
        s.connect(ai[-1])
        if proto == "https:":
            context = tls.SSLContext(tls.PROTOCOL_TLS_CLIENT)
            context.verify_mode = tls.CERT_NONE
            s = context.wrap_socket(s, server_hostname=host)
        if not isinstance(method, bytes):
            method = method.encode()
        if not isinstance(path, bytes):
            path = path.encode()
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

        for k in headers:
            s.write(_to_bytes(k))
            s.write(b": ")
            s.write(_to_bytes(headers[k]))
            s.write(b"\r\n")

        s.write(b"\r\n")

        if data:
            if chunked_data:
                if headers.get("Transfer-Encoding", None) == "chunked":
                    for chunk in data:
                        chunk = _to_bytes(chunk)
                        s.write(b"%x\r\n" % len(chunk))
                        s.write(chunk)
                        s.write(b"\r\n")
                    s.write(b"0\r\n\r\n")
                else:
                    for chunk in data:
                        s.write(_to_bytes(chunk))
            else:
                s.write(_to_bytes(data))

        status, reason = read_status_line(s)
        resp_headers = read_headers(s, parse_headers)

        if not 200 <= status <= 299:
            location = resp_headers.get("location")
            if location:
                if status in [301, 302, 303, 307, 308]:
                    redirect = resolve_redirect_url(url, location)
                else:
                    raise NotImplementedError("Redirect %d not yet supported" % status)
    except OSError:
        s.close()
        raise

    if redirect:
        s.close()
        headers.pop("Host", None)
        if status in [301, 302, 303]:
            return request(
                "GET",
                redirect,
                None,
                None,
                headers,
                stream,
                auth,
                timeout,
                parse_headers,
                max_body,
            )
        return request(
            method,
            redirect,
            data,
            json,
            headers,
            stream,
            auth,
            timeout,
            parse_headers,
            max_body,
        )

    if method == "HEAD":
        body = b""
    else:
        body = read_body(s, resp_headers, max_body)
    resp = Response(body)
    resp.raw = s
    s.close()
    resp.status_code = status
    resp.reason = reason
    if parse_headers is not False:
        resp.headers = resp_headers
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
