import io
import sys


class Socket:
    def __init__(self, read_data=b"HTTP/1.1 200 OK\r\n\r\n"):
        self._write_buffer = io.BytesIO()
        self._read_buffer = io.BytesIO(read_data)

    def connect(self, address):
        pass

    def write(self, buf):
        self._write_buffer.write(buf)

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
    def getaddrinfo(host, port, af=0, type=0, flags=0):
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", 80))]

    def socket(af=AF_INET, type=SOCK_STREAM, proto=IPPROTO_TCP):
        return Socket()


sys.modules["socket"] = socket
# ruff: noqa: E402
import requests


def format_message(response):
    return response.raw._write_buffer.getvalue().decode("utf8")


def test_simple_get():
    response = requests.request("GET", "http://example.com")

    assert response.raw._write_buffer.getvalue() == (
        b"GET / HTTP/1.1\r\n" + b"Connection: close\r\n" + b"Host: example.com\r\n\r\n"
    ), format_message(response)


def test_get_auth():
    response = requests.request(
        "GET", "http://example.com", auth=("test-username", "test-password")
    )

    assert response.raw._write_buffer.getvalue() == (
        b"GET / HTTP/1.1\r\n"
        + b"Host: example.com\r\n"
        + b"Authorization: Basic dGVzdC11c2VybmFtZTp0ZXN0LXBhc3N3b3Jk\r\n"
        + b"Connection: close\r\n\r\n"
    ), format_message(response)


def test_get_custom_header():
    response = requests.request("GET", "http://example.com", headers={"User-Agent": "test-agent"})

    assert response.raw._write_buffer.getvalue() == (
        b"GET / HTTP/1.1\r\n"
        + b"User-Agent: test-agent\r\n"
        + b"Host: example.com\r\n"
        + b"Connection: close\r\n\r\n"
    ), format_message(response)


def test_post_json():
    response = requests.request("GET", "http://example.com", json="test")

    assert response.raw._write_buffer.getvalue() == (
        b"GET / HTTP/1.1\r\n"
        + b"Connection: close\r\n"
        + b"Content-Type: application/json\r\n"
        + b"Host: example.com\r\n"
        + b"Content-Length: 6\r\n\r\n"
        + b'"test"'
    ), format_message(response)


def test_post_chunked_data():
    def chunks():
        yield "test"

    response = requests.request("GET", "http://example.com", data=chunks())

    assert response.raw._write_buffer.getvalue() == (
        b"GET / HTTP/1.1\r\n"
        + b"Transfer-Encoding: chunked\r\n"
        + b"Host: example.com\r\n"
        + b"Connection: close\r\n\r\n"
        + b"4\r\ntest\r\n"
        + b"0\r\n\r\n"
    ), format_message(response)


def test_overwrite_get_headers():
    response = requests.request(
        "GET", "http://example.com", headers={"Host": "test.com", "Connection": "keep-alive"}
    )

    assert response.raw._write_buffer.getvalue() == (
        b"GET / HTTP/1.1\r\n" + b"Connection: keep-alive\r\n" + b"Host: test.com\r\n\r\n"
    ), format_message(response)


def test_overwrite_post_json_headers():
    response = requests.request(
        "GET",
        "http://example.com",
        json="test",
        headers={"Content-Type": "text/plain", "Content-Length": "10"},
    )

    assert response.raw._write_buffer.getvalue() == (
        b"GET / HTTP/1.1\r\n"
        + b"Connection: close\r\n"
        + b"Content-Length: 10\r\n"
        + b"Content-Type: text/plain\r\n"
        + b"Host: example.com\r\n\r\n"
        + b'"test"'
    ), format_message(response)


def test_overwrite_post_chunked_data_headers():
    def chunks():
        yield "test"

    response = requests.request(
        "GET", "http://example.com", data=chunks(), headers={"Content-Length": "4"}
    )

    assert response.raw._write_buffer.getvalue() == (
        b"GET / HTTP/1.1\r\n"
        + b"Host: example.com\r\n"
        + b"Content-Length: 4\r\n"
        + b"Connection: close\r\n\r\n"
        + b"test"
    ), format_message(response)


def test_do_not_modify_headers_argument():
    global do_not_modify_this_dict
    do_not_modify_this_dict = {}
    requests.request("GET", "http://example.com", headers=do_not_modify_this_dict)

    assert do_not_modify_this_dict == {}, do_not_modify_this_dict


def test_content_length_via_content():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello"
    )
    response = requests.request("GET", "http://example.com")
    assert response.content == b"hello"
    assert response.headers["Content-Length"] == "5"
    socket.socket = lambda *a, **k: Socket()


def test_chunked_response_via_content():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n6\r\n world\r\n0\r\n\r\n"
    )
    response = requests.request("GET", "http://example.com")
    assert response.content == b"hello world"
    socket.socket = lambda *a, **k: Socket()


def test_chunked_response_readinto():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n3\r\nabc\r\n4\r\ndefg\r\n0\r\n\r\n"
    )
    response = requests.request("GET", "http://example.com")
    buf = bytearray(2)
    result = b""
    while True:
        n = response.raw.readinto(buf)
        if n == 0:
            break
        result += buf if n == 2 else buf[:n]
    assert result == b"abcdefg"
    socket.socket = lambda *a, **k: Socket()


def test_raw_open_before_content():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello"
    )
    response = requests.request("GET", "http://example.com")
    assert response.raw is not None
    assert response.raw.read(1) == b"h"
    socket.socket = lambda *a, **k: Socket()


def test_raw_incremental_content_length():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nContent-Length: 10\r\n\r\nabcdefghij"
    )
    response = requests.request("GET", "http://example.com")
    assert response.raw.read(3) == b"abc"
    assert response.raw.read(3) == b"def"
    assert response.content == b"ghij"
    assert response.raw is None
    socket.socket = lambda *a, **k: Socket()


def test_raw_readinto_content_length():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nContent-Length: 10\r\n\r\nabcdefghij"
    )
    response = requests.request("GET", "http://example.com")
    buf = bytearray(3)
    result = b""
    while True:
        n = response.raw.readinto(buf)
        if n == 0:
            break
        result += buf if n == 3 else buf[:n]
    assert result == b"abcdefghij"
    socket.socket = lambda *a, **k: Socket()


test_simple_get()
test_get_auth()
test_get_custom_header()
test_post_json()
test_post_chunked_data()
test_overwrite_get_headers()
test_overwrite_post_json_headers()
test_overwrite_post_chunked_data_headers()
test_do_not_modify_headers_argument()
test_content_length_via_content()
test_chunked_response_via_content()
test_chunked_response_readinto()
test_raw_open_before_content()
test_raw_incremental_content_length()
test_raw_readinto_content_length()
