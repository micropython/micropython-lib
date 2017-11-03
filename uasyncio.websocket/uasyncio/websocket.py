import uasyncio as asyncio
import uhashlib, ubinascii
import websocket


def make_respkey(webkey):
    d = uhashlib.sha1(webkey)
    d.update(b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11")
    respkey = d.digest()
    respkey = ubinascii.b2a_base64(respkey) #[:-1]
    return respkey


class WSWriter:

    def __init__(self, s):
        self.s = s

    async def awrite(self, data):
        assert len(data) < 126
        await self.s.awrite(b"\x81")
        await self.s.awrite(bytes([len(data)]))
        await self.s.awrite(data)


def WSReader(reader, writer):

        webkey = None
        while 1:
            l = yield from reader.readline()
            print(l)
            if not l:
                raise ValueError()
            if l == b"\r\n":
                break
            if l.startswith(b'Sec-WebSocket-Key'):
                webkey = l.split(b":", 1)[1]
                webkey = webkey.strip()

        if not webkey:
            raise ValueError("Not a websocker request")

        respkey = make_respkey(webkey)

        await writer.awrite(b"""\
HTTP/1.1 101 Switching Protocols\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Accept: """)
        await writer.awrite(respkey)
        await writer.awrite("\r\n")
#        await writer.awrite("\r\n\r\n")

        print("Finished webrepl handshake")

        ws = websocket.websocket(reader.ios)
        rws = asyncio.StreamReader(reader.ios, ws)

        return rws


#deprecated
def start_ws_server(client_coro, host, port, backlog=10):

    def ws_wrap(reader, writer):
        print(reader, writer)

        print("Req:", (yield from reader.readline()))

        webkey = None
        while 1:
            l = yield from reader.readline()
            print(l)
            if not l:
                raise ValueError()
            if l == b"\r\n":
                break
            if l.startswith(b'Sec-WebSocket-Key'):
                webkey = l.split(b":", 1)[1]
                webkey = webkey.strip()

        if not webkey:
            raise ValueError("Not a websocker request")

        respkey = make_respkey(webkey)

        await writer.awrite(b"""\
HTTP/1.1 101 Switching Protocols\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Accept: """)
        await writer.awrite(respkey)
        await writer.awrite("\r\n")
#        await writer.awrite("\r\n\r\n")

        print("Finished webrepl handshake")

        ws = websocket.websocket(reader.ios)
        rws = asyncio.StreamReader(reader.ios, ws)

        return await client_coro(rws, WSWriter(writer))


    await asyncio.start_server(ws_wrap, host, port, backlog)
