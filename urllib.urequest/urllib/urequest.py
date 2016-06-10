import usocket

def urlopen(url, data=None, method="GET"):
    if data is not None and method == "GET":
        method = "POST"
    try:
        proto, dummy, host, path = url.split("/", 3)
    except ValueError:
        proto, dummy, host = url.split("/", 2)
        path = ""
    if proto == "http:":
        port = 80
    elif proto == "https:":
        import ussl
        port = 443
    else:
        raise ValueError("Unsupported protocol: " + proto)

    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    ai = usocket.getaddrinfo(host, port)
    addr = ai[0][4]
    s = usocket.socket()
    s.connect(addr)
    if proto == "https:":
        s = ussl.wrap_socket(s)

    s.write(method)
    s.write(b" /")
    s.write(path)
    s.write(b" HTTP/1.0\r\nHost: ")
    s.write(host)
    s.write(b"\r\n")

    if data:
        s.write(b"Content-Length: ")
        s.write(str(len(data)))
        s.write(b"\r\n")
    s.write(b"\r\n")
    if data:
        s.write(data)

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
