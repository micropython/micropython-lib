import usocket


def _make_user_agent():
    import sys
    comment = sys.implementation._machine
    comment = comment.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    ua = "MicroPython/{}.{}.{} ({})".format(*sys.implementation[1][:3], comment)
    return ua

default_user_agent = _make_user_agent()


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
        import ujson

        return ujson.loads(self.content)


def request(
    method,
    url,
    data=None,
    json=None,
    headers={},
    stream=None,
    auth=None,
    timeout=None,
    parse_headers=True,
    user_agent=True
):
    redirect = None  # redirection url, None means no redirection
    chunked_data = data and getattr(data, "__next__", None) and not getattr(data, "__len__", None)

    # Security and correctness: Can't add extra fields to `headers`,
    # we have to have separate variables for them.
    #
    # This is because have `headers={}` in the function prototype.
    # So the same dictionary will get reused for every call that doesn't
    # explicitly specify a `headers` parameter.
    #
    # So if we put an Authorization header in `headers`, then following a
    # request to a site that requires a username and password, that same
    # plain-text username and password would be sent with every following HTTP
    # request that used the default for the `headers` parameter.
    basic_auth_header = None
    if auth is not None:
        import ubinascii
        username, password = auth
        basic_auth_header = b"{}:{}".format(username, password)
        basic_auth_header = ubinascii.b2a_base64(basic_auth_header)[:-1]

    if user_agent:
        if user_agent is True:
            # Use the standard User-Agent
            user_agent = default_user_agent
        elif user_agent[0] == ' ':
            # It's a suffix to append to the standard User-Agent
            user_agent = default_user_agent + user_agent

        if user_agent:
            user_agent = user_agent.encode('ascii')

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

    ai = usocket.getaddrinfo(host, port, 0, usocket.SOCK_STREAM)
    ai = ai[0]

    resp_d = None
    if parse_headers is not False:
        resp_d = {}

    s = usocket.socket(ai[0], usocket.SOCK_STREAM, ai[2])

    if timeout is not None:
        # Note: settimeout is not supported on all platforms, will raise
        # an AttributeError if not available.
        s.settimeout(timeout)

    try:
        s.connect(ai[-1])
        if proto == "https:":
            context = tls.SSLContext(tls.PROTOCOL_TLS_CLIENT)
            # TODO: This is a security vulnerability.
            # HTTPS is providing nearly zero security, because of the next
            # line.  We disable all the protection against MiTM attacks!
            #
            # I mean... with this configuration, HTTPS still provides
            # protection against passive eavesdropping, so there's that?
            # But with modern network design, and modern attacks, anyone
            # able to passively eavesdrop is almost certainly able to MiTM
            # too.  So the safety level is technically not quite zero, but
            # it is very close to zero, and is far less than people using
            # HTTPS expect.
            context.verify_mode = tls.CERT_NONE
            s = context.wrap_socket(s, server_hostname=host)
        s.write(b"%s /%s HTTP/1.0\r\n" % (method, path))
        if "Host" not in headers:
            s.write(b"Host: %s\r\n" % host)
        if basic_auth_header:
            s.write(b"Authorization: Basic ")
            s.write(basic_auth_header)
            s.write(b"\r\n")
        if user_agent:
            s.write(b"User-Agent: ")
            s.write(user_agent)
            s.write(b"\r\n")

        # Iterate over keys to avoid tuple alloc
        for k in headers:
            s.write(k)
            s.write(b": ")
            s.write(headers[k])
            s.write(b"\r\n")
        if json is not None:
            assert data is None
            import ujson

            data = ujson.dumps(json)
            s.write(b"Content-Type: application/json\r\n")
        if data:
            if chunked_data:
                s.write(b"Transfer-Encoding: chunked\r\n")
            else:
                s.write(b"Content-Length: %d\r\n" % len(data))
        s.write(b"Connection: close\r\n\r\n")
        if data:
            if chunked_data:
                for chunk in data:
                    s.write(b"%x\r\n" % len(chunk))
                    s.write(chunk)
                    s.write(b"\r\n")
                s.write("0\r\n\r\n")
            else:
                s.write(data)

        l = s.readline()
        # print(l)
        l = l.split(None, 2)
        if len(l) < 2:
            # Invalid response
            raise ValueError("HTTP error: BadStatusLine:\n%s" % l)
        status = int(l[1])
        reason = ""
        if len(l) > 2:
            reason = l[2].rstrip()
        while True:
            l = s.readline()
            if not l or l == b"\r\n":
                break
            # print(l)
            if l.startswith(b"Transfer-Encoding:"):
                if b"chunked" in l:
                    raise ValueError("Unsupported " + str(l, "utf-8"))
            elif l.startswith(b"Location:") and not 200 <= status <= 299:
                if status in [301, 302, 303, 307, 308]:
                    redirect = str(l[10:-2], "utf-8")
                else:
                    raise NotImplementedError("Redirect %d not yet supported" % status)
            if parse_headers is False:
                pass
            elif parse_headers is True:
                l = str(l, "utf-8")
                k, v = l.split(":", 1)
                # Headers are case insensitive, so we lowercase them.
                # This avoids having to do a linear case-insensitive search
                # through the dictionary later.
                resp_d[k.lower()] = v.strip()
            else:
                parse_headers(l, resp_d)
    except OSError:
        s.close()
        raise

    if redirect:
        s.close()
        if status in [301, 302, 303]:
            return request("GET", redirect, None, None, headers, stream)
        else:
            return request(method, redirect, data, json, headers, stream)
    else:
        resp = Response(s)
        resp.status_code = status
        resp.reason = reason
        if resp_d is not None:
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
