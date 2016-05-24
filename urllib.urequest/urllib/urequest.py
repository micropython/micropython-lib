import usocket

def urlopen(url, data=None, method="GET"):
    if data is not None and method == "GET":
        method = "POST"
    try:
        proto, dummy, host, path = url.split("/", 3)
    except ValueError:
        proto, dummy, host = url.split("/", 2)
        path = ""
    if proto != "http:":
        raise ValueError("Unsupported protocol: " + proto)

    port = 80
    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    ai = usocket.getaddrinfo(host, port)
    addr = ai[0][4]
    s = usocket.socket()
    s.connect(addr)
    if data:
        req = b"%s /%s HTTP/1.0\r\nHost: %s\r\nContent-Length: %d\r\n\r\n" % (method, path, host, len(data))
    else:
        req = b"%s /%s HTTP/1.0\r\nHost: %s\r\n\r\n" % (method, path, host)
    s.send(req)
    if data:
        s.send(data)

    l = s.readline()
    protover, status, msg = l.split(None, 2)
    status = int(status)
    #print(protover, status, msg)
    while True:
        l = s.readline()
        if not l or l == b"\r\n":
            break
        #print(line)
        if l.startswith(b"Transfer-Encoding:"):
            if b"chunked" in line:
                raise ValueError("Unsupported " + l)
        elif l.startswith(b"Location:"):
            raise NotImplementedError("Redirects not yet supported")

    return s
