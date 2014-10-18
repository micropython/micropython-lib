import uasyncio as asyncio


class ClientResponse:

    def __init__(self, reader):
        self.content = reader

    def read(self, sz=-1):
        return (yield from self.content.read(sz))

    def __repr__(self):
        return "<ClientResponse %d %s>" % (self.status, self.headers)


def request_raw(method, url):
    try:
        proto, dummy, host, path = url.split("/", 3)
    except ValueError:
        proto, dummy, host = url.split("/", 2)
        path = ""
    reader, writer = yield from asyncio.open_connection(host, 80)
    query = "%s /%s HTTP/1.0\r\nHost: %s\r\n\r\n" % (method, path, host)
    yield from writer.awrite(query.encode('latin-1'))
#    yield from writer.close()
    return reader


def request(method, url):
    reader = yield from request_raw(method, url)
    resp = ClientResponse(reader)
    headers = []
    sline = yield from reader.readline()
    protover, st, msg = sline.split(None, 2)
    resp.status = int(st)
    while True:
        line = yield from reader.readline()
        if not line or line == b"\r\n":
            break
        headers.append(line)

    resp.headers = headers
    return resp
