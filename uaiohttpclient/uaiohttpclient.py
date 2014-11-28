import uasyncio as asyncio


class ClientResponse:

    def __init__(self, reader):
        self.content = reader

    def read(self, sz=-1):
        return (yield from self.content.read(sz))

    def __repr__(self):
        return "<ClientResponse %d %s>" % (self.status, self.headers)


class ChunkedClientResponse(ClientResponse):

    def __init__(self, reader):
        self.content = reader
        self.chunk_size = 0

    def read(self, sz=4*1024*1024):
        if self.chunk_size == 0:
            l = yield from self.content.readline()
            #print("chunk line:", l)
            l = l.split(b";", 1)[0]
            self.chunk_size = int(l, 16)
            #print("chunk size:", self.chunk_size)
            if self.chunk_size == 0:
                # End of message
                sep = yield from self.content.read(2)
                assert sep == b"\r\n"
                return b''
        data = yield from self.content.read(min(sz, self.chunk_size))
        self.chunk_size -= len(data)
        if self.chunk_size == 0:
            sep = yield from self.content.read(2)
            assert sep == b"\r\n"
        return data

    def __repr__(self):
        return "<ChunkedClientResponse %d %s>" % (self.status, self.headers)


def request_raw(method, url):
    try:
        proto, dummy, host, path = url.split("/", 3)
    except ValueError:
        proto, dummy, host = url.split("/", 2)
        path = ""
    reader, writer = yield from asyncio.open_connection(host, 80)
    # Use protocol 1.0, because 1.1 always allows to use chunked transfer-encoding
    # But explicitly set Connection: close, even though this should be default for 1.0,
    # because some servers misbehave w/o it.
    query = "%s /%s HTTP/1.0\r\nHost: %s\r\nConnection: close\r\n\r\n" % (method, path, host)
    yield from writer.awrite(query.encode('latin-1'))
#    yield from writer.close()
    return reader


def request(method, url):
    reader = yield from request_raw(method, url)
    headers = []
    sline = yield from reader.readline()
    protover, st, msg = sline.split(None, 2)
    chunked = False
    while True:
        line = yield from reader.readline()
        if not line or line == b"\r\n":
            break
        headers.append(line)
        if line.startswith(b"Transfer-Encoding:"):
            if b"chunked" in line:
                chunked = True

    if chunked:
        resp = ChunkedClientResponse(reader)
    else:
        resp = ClientResponse(reader)
    resp.status = int(st)
    resp.headers = headers
    return resp
