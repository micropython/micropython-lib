import asyncio


class ClientResponse:
    def __init__(self, reader):
        self.content = reader

    async def read(self, sz=-1):
        return await self.content.read(sz)

    def __repr__(self):
        return "<ClientResponse %d %s>" % (self.status, self.headers)


class ChunkedClientResponse(ClientResponse):
    def __init__(self, reader):
        self.content = reader
        self.chunk_size = 0

    async def read(self, sz=4 * 1024 * 1024):
        if self.chunk_size == 0:
            line = await self.content.readline()
            # print("chunk line:", l)
            line = line.split(b";", 1)[0]
            self.chunk_size = int(line, 16)
            # print("chunk size:", self.chunk_size)
            if self.chunk_size == 0:
                # End of message
                sep = await self.content.read(2)
                assert sep == b"\r\n"
                return b""
        data = await self.content.read(min(sz, self.chunk_size))
        self.chunk_size -= len(data)
        if self.chunk_size == 0:
            sep = await self.content.read(2)
            assert sep == b"\r\n"
        return data

    def __repr__(self):
        return "<ChunkedClientResponse %d %s>" % (self.status, self.headers)


async def request_raw(method, url):
    try:
        proto, dummy, host, path = url.split("/", 3)
    except ValueError:
        proto, dummy, host = url.split("/", 2)
        path = ""

    if ":" in host:
        host, port = host.split(":")
        port = int(port)
    else:
        port = 80

    if proto != "http:":
        raise ValueError("Unsupported protocol: " + proto)
    reader, writer = await asyncio.open_connection(host, port)
    # Use protocol 1.0, because 1.1 always allows to use chunked
    # transfer-encoding But explicitly set Connection: close, even
    # though this should be default for 1.0, because some servers
    # misbehave w/o it.
    query = "%s /%s HTTP/1.0\r\nHost: %s\r\nConnection: close\r\nUser-Agent: compat\r\n\r\n" % (
        method,
        path,
        host,
    )
    await writer.awrite(query.encode("latin-1"))
    return reader


async def request(method, url):
    redir_cnt = 0
    while redir_cnt < 2:
        reader = await request_raw(method, url)
        headers = []
        sline = await reader.readline()
        sline = sline.split(None, 2)
        status = int(sline[1])
        chunked = False
        while True:
            line = await reader.readline()
            if not line or line == b"\r\n":
                break
            headers.append(line)
            if line.startswith(b"Transfer-Encoding:"):
                if b"chunked" in line:
                    chunked = True
            elif line.startswith(b"Location:"):
                url = line.rstrip().split(None, 1)[1].decode("latin-1")

        if 301 <= status <= 303:
            redir_cnt += 1
            await reader.aclose()
            continue
        break

    if chunked:
        resp = ChunkedClientResponse(reader)
    else:
        resp = ClientResponse(reader)
    resp.status = status
    resp.headers = headers
    return resp
