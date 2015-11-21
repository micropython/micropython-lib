import usocket

def urlopen(url, data=None):
    if data:
        raise NotImplementedError("POST is not yet supported")
    try:
        proto, dummy, host, path = url.split("/", 3)
    except ValueError:
        proto, dummy, host = url.split("/", 2)
        path = ""
    if proto != "http:":
        raise ValueError("Unsupported protocol: " + proto)

    ai = usocket.getaddrinfo(host, 80)
    addr = ai[0][4]
    s = usocket.socket()
    s.connect(addr)
    s.send(b"GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n" % (path, host))

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
