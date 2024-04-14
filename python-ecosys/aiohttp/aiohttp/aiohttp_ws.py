# MicroPython aiohttp library
# MIT license; Copyright (c) 2023 Carlos Gil
# adapted from https://github.com/danni/uwebsockets
# and https://github.com/miguelgrinberg/microdot/blob/main/src/microdot_asyncio_websocket.py

import asyncio
import random
import json as _json
import binascii
import re
import struct
from collections import namedtuple

URL_RE = re.compile(r"(wss|ws)://([A-Za-z0-9-\.]+)(?:\:([0-9]+))?(/.+)?")
URI = namedtuple("URI", ("protocol", "hostname", "port", "path"))  # noqa: PYI024


def urlparse(uri):
    """Parse ws:// URLs"""
    match = URL_RE.match(uri)
    if match:
        protocol = match.group(1)
        host = match.group(2)
        port = match.group(3)
        path = match.group(4)

        if protocol == "wss":
            if port is None:
                port = 443
        elif protocol == "ws":
            if port is None:
                port = 80
        else:
            raise ValueError("Scheme {} is invalid".format(protocol))

        return URI(protocol, host, int(port), path)


class WebSocketMessage:
    def __init__(self, opcode, data):
        self.type = opcode
        self.data = data


class WSMsgType:
    TEXT = 1
    BINARY = 2
    ERROR = 258


class WebSocketClient:
    CONT = 0
    TEXT = 1
    BINARY = 2
    CLOSE = 8
    PING = 9
    PONG = 10

    def __init__(self, params):
        self.params = params
        self.closed = False
        self.reader = None
        self.writer = None

    async def connect(self, uri, ssl=None, handshake_request=None):
        uri = urlparse(uri)
        assert uri
        if uri.protocol == "wss":
            if not ssl:
                ssl = True
        await self.handshake(uri, ssl, handshake_request)

    @classmethod
    def _parse_frame_header(cls, header):
        byte1, byte2 = struct.unpack("!BB", header)

        # Byte 1: FIN(1) _(1) _(1) _(1) OPCODE(4)
        fin = bool(byte1 & 0x80)
        opcode = byte1 & 0x0F

        # Byte 2: MASK(1) LENGTH(7)
        mask = bool(byte2 & (1 << 7))
        length = byte2 & 0x7F

        return fin, opcode, mask, length

    def _process_websocket_frame(self, opcode, payload):
        if opcode == self.TEXT:
            payload = str(payload, "utf-8")
        elif opcode == self.BINARY:
            pass
        elif opcode == self.CLOSE:
            # raise OSError(32, "Websocket connection closed")
            return opcode, payload
        elif opcode == self.PING:
            return self.PONG, payload
        elif opcode == self.PONG:  # pragma: no branch
            return None, None
        return None, payload

    @classmethod
    def _encode_websocket_frame(cls, opcode, payload):
        if opcode == cls.TEXT:
            payload = payload.encode()

        length = len(payload)
        fin = mask = True

        # Frame header
        # Byte 1: FIN(1) _(1) _(1) _(1) OPCODE(4)
        byte1 = 0x80 if fin else 0
        byte1 |= opcode

        # Byte 2: MASK(1) LENGTH(7)
        byte2 = 0x80 if mask else 0

        if length < 126:  # 126 is magic value to use 2-byte length header
            byte2 |= length
            frame = struct.pack("!BB", byte1, byte2)

        elif length < (1 << 16):  # Length fits in 2-bytes
            byte2 |= 126  # Magic code
            frame = struct.pack("!BBH", byte1, byte2, length)

        elif length < (1 << 64):
            byte2 |= 127  # Magic code
            frame = struct.pack("!BBQ", byte1, byte2, length)

        else:
            raise ValueError

        # Mask is 4 bytes
        mask_bits = struct.pack("!I", random.getrandbits(32))
        frame += mask_bits
        payload = bytes(b ^ mask_bits[i % 4] for i, b in enumerate(payload))
        return frame + payload

    async def handshake(self, uri, ssl, req):
        headers = {}
        _http_proto = "http" if uri.protocol != "wss" else "https"
        url = f"{_http_proto}://{uri.hostname}:{uri.port}{uri.path or '/'}"
        key = binascii.b2a_base64(bytes(random.getrandbits(8) for _ in range(16)))[:-1]
        headers["Host"] = f"{uri.hostname}:{uri.port}"
        headers["Connection"] = "Upgrade"
        headers["Upgrade"] = "websocket"
        headers["Sec-WebSocket-Key"] = str(key, "utf-8")
        headers["Sec-WebSocket-Version"] = "13"
        headers["Origin"] = f"{_http_proto}://{uri.hostname}:{uri.port}"

        self.reader, self.writer = await req(
            "GET",
            url,
            ssl=ssl,
            headers=headers,
            is_handshake=True,
            version="HTTP/1.1",
        )

        header = await self.reader.readline()
        header = header[:-2]
        assert header.startswith(b"HTTP/1.1 101 "), header

        while header:
            header = await self.reader.readline()
            header = header[:-2]

    async def receive(self):
        while True:
            opcode, payload = await self._read_frame()
            send_opcode, data = self._process_websocket_frame(opcode, payload)
            if send_opcode:  # pragma: no cover
                await self.send(data, send_opcode)
            if opcode == self.CLOSE:
                self.closed = True
                return opcode, data
            elif data:  # pragma: no branch
                return opcode, data

    async def send(self, data, opcode=None):
        frame = self._encode_websocket_frame(
            opcode or (self.TEXT if isinstance(data, str) else self.BINARY), data
        )
        self.writer.write(frame)
        await self.writer.drain()

    async def close(self):
        if not self.closed:  # pragma: no cover
            self.closed = True
            await self.send(b"", self.CLOSE)

    async def _read_frame(self):
        header = await self.reader.read(2)
        if len(header) != 2:  # pragma: no cover
            # raise OSError(32, "Websocket connection closed")
            opcode = self.CLOSE
            payload = b""
            return opcode, payload
        fin, opcode, has_mask, length = self._parse_frame_header(header)
        if length == 126:  # Magic number, length header is 2 bytes
            (length,) = struct.unpack("!H", await self.reader.read(2))
        elif length == 127:  # Magic number, length header is 8 bytes
            (length,) = struct.unpack("!Q", await self.reader.read(8))

        if has_mask:  # pragma: no cover
            mask = await self.reader.read(4)
        payload = await self.reader.read(length)
        if has_mask:  # pragma: no cover
            payload = bytes(x ^ mask[i % 4] for i, x in enumerate(payload))
        return opcode, payload


class ClientWebSocketResponse:
    def __init__(self, wsclient):
        self.ws = wsclient

    def __aiter__(self):
        return self

    async def __anext__(self):
        msg = WebSocketMessage(*await self.ws.receive())
        # print(msg.data, msg.type) # DEBUG
        if (not msg.data and msg.type == self.ws.CLOSE) or self.ws.closed:
            raise StopAsyncIteration
        return msg

    async def close(self):
        await self.ws.close()

    async def send_str(self, data):
        if not isinstance(data, str):
            raise TypeError("data argument must be str (%r)" % type(data))
        await self.ws.send(data)

    async def send_bytes(self, data):
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("data argument must be byte-ish (%r)" % type(data))
        await self.ws.send(data)

    async def send_json(self, data):
        await self.send_str(_json.dumps(data))

    async def receive_str(self):
        msg = WebSocketMessage(*await self.ws.receive())
        if msg.type != self.ws.TEXT:
            raise TypeError(f"Received message {msg.type}:{msg.data!r} is not str")
        return msg.data

    async def receive_bytes(self):
        msg = WebSocketMessage(*await self.ws.receive())
        if msg.type != self.ws.BINARY:
            raise TypeError(f"Received message {msg.type}:{msg.data!r} is not bytes")
        return msg.data

    async def receive_json(self):
        data = await self.receive_str()
        return _json.loads(data)


class _WSRequestContextManager:
    def __init__(self, client, request_co):
        self.reqco = request_co
        self.client = client

    async def __aenter__(self):
        return await self.reqco

    async def __aexit__(self, *args):
        await self.client._reader.aclose()
        return await asyncio.sleep(0)
