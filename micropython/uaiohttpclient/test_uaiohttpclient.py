import io
import sys

_MP_STREAM_POLL = 3
_SERVER_RESPONSE_200_OK = b"HTTP/1.1 200 OK\r\n\r\n"


class Socket(io.IOBase):
    def __init__(self, read_data):
        self._write_buffer = io.BytesIO()
        self._read_buffer = io.BytesIO(read_data)

    def ioctl(self, cmd, arg):
        if cmd == _MP_STREAM_POLL:
            return arg
        return -1

    def setblocking(self, value):
        pass

    def connect(self, address):
        pass

    def write(self, buf):
        self._write_buffer.write(buf)
        return len(buf)

    def readline(self):
        return self._read_buffer.readline()

    def read(self, size=-1):
        return self._read_buffer.read(size)

    def readinto(self, buf):
        return self._read_buffer.readinto(buf)

    def close(self):
        pass


class socket:
    AF_INET = 2
    SOCK_STREAM = 1
    IPPROTO_TCP = 6

    @staticmethod
    def _set_responses(r):
        socket._responses = r

    @staticmethod
    def getaddrinfo(host, port, af=0, type=0, flags=0):
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", 80))]

    def socket(af=AF_INET, type=SOCK_STREAM, proto=IPPROTO_TCP):
        return Socket(socket._responses.pop(0))


# Patch the socket module with a mock one for testing.
sys.modules["socket"] = socket

# ruff: noqa: E402
import asyncio
import uaiohttpclient
import unittest


class Test(unittest.TestCase):
    async def do_request(self, url):
        resp = await uaiohttpclient.request("GET", url)
        body = await resp.read()
        return resp, body

    def test_request(self):
        BODY_DATA = b"body"
        socket._set_responses([_SERVER_RESPONSE_200_OK + BODY_DATA])

        resp, body = asyncio.run(self.do_request("http://example.com"))
        request_data = resp.content.s._write_buffer.getvalue()
        self.assertEqual(
            request_data,
            b"GET / HTTP/1.0\r\nHost: example.com\r\nConnection: close\r\nUser-Agent: compat\r\n\r\n",
        )
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.headers, [])
        self.assertEqual(body, BODY_DATA)

    def test_redirect_absolute(self):
        BODY_DATA = b"body"
        socket._set_responses(
            [
                b"HTTP/1.1 301 OK\r\nLocation: http://example.com/index\r\n\r\n",
                _SERVER_RESPONSE_200_OK + BODY_DATA,
            ]
        )

        resp, body = asyncio.run(self.do_request("http://example.com"))
        request_data = resp.content.s._write_buffer.getvalue()
        self.assertEqual(
            request_data,
            b"GET /index HTTP/1.0\r\nHost: example.com\r\nConnection: close\r\nUser-Agent: compat\r\n\r\n",
        )
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.headers, [])
        self.assertEqual(body, BODY_DATA)


if __name__ == "__main__":
    unittest.main()
