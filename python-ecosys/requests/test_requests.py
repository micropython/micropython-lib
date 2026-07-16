import io
import sys

SERVER_RESPONSE_200_OK = b"HTTP/1.1 200 OK\r\n\r\n"


class Socket:
    def __init__(self, read_data=SERVER_RESPONSE_200_OK):
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


def test_post_json_unicode():
    response = requests.request("POST", "http://example.com", json="aαbβcγdδ")  # noqa: RUF001

    assert response.raw._write_buffer.getvalue() == (
        b"POST / HTTP/1.1\r\n"
        b"Connection: close\r\n"
        b"Content-Type: application/json\r\n"
        b"Host: example.com\r\n"
        b"Content-Length: 14\r\n\r\n" + bytes('"aαbβcγdδ"', "utf-8")  # noqa: RUF001
    ), format_message(response)


def test_post_data_str():
    response = requests.request("POST", "http://example.com", data="body")

    assert response.raw._write_buffer.getvalue() == (
        b"POST / HTTP/1.1\r\n"
        b"Content-Length: 4\r\n"
        b"Host: example.com\r\n"
        b"Connection: close\r\n\r\n"
        b"body"
    ), format_message(response)


def test_post_data_str_unicode():
    response = requests.request("POST", "http://example.com", data="aαbβcγdδ")  # noqa: RUF001

    assert response.raw._write_buffer.getvalue() == (
        b"POST / HTTP/1.1\r\n"
        b"Content-Length: 12\r\n"
        b"Host: example.com\r\n"
        b"Connection: close\r\n\r\n" + bytes("aαbβcγdδ", "utf-8")  # noqa: RUF001
    ), format_message(response)


def test_post_data_bytes():
    response = requests.request("POST", "http://example.com", data=b"body\x01\x02\x03\xff")

    assert response.raw._write_buffer.getvalue() == (
        b"POST / HTTP/1.1\r\n"
        b"Content-Length: 8\r\n"
        b"Host: example.com\r\n"
        b"Connection: close\r\n\r\n"
        b"body\x01\x02\x03\xff"
    ), response.raw._write_buffer.getvalue()


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


def test_chunked_response_raises():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n0\r\n\r\n"
    )
    raised = False
    try:
        requests.request("GET", "http://example.com")
    except ValueError as e:
        raised = True
        if "Unsupported" not in str(e):
            raise
    if not raised:
        raise AssertionError("expected ValueError for chunked response")
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


def test_redirect_absolute():
    server = iter(
        [
            b"HTTP/1.1 301 OK\r\nLocation: http://example.com/index\r\n\r\n",
            SERVER_RESPONSE_200_OK,
        ]
    )
    socket.socket = lambda *a, **k: Socket(next(server))

    response = requests.request("GET", "http://example.com")

    assert response.raw._write_buffer.getvalue() == (
        b"GET /index HTTP/1.1\r\nConnection: close\r\nHost: example.com\r\n\r\n"
    ), format_message(response)

    socket.socket = lambda *a, **k: Socket()


def test_redirect_relative():
    server = iter(
        [
            b"HTTP/1.1 301 OK\r\nLocation: /index\r\n\r\n",
            SERVER_RESPONSE_200_OK,
        ]
    )
    socket.socket = lambda *a, **k: Socket(next(server))

    response = requests.request("GET", "http://example.com")

    assert response.raw._write_buffer.getvalue() == (
        b"GET /index HTTP/1.1\r\nConnection: close\r\nHost: example.com\r\n\r\n"
    ), format_message(response)

    socket.socket = lambda *a, **k: Socket()


def test_redirect_protocol_relative():
    server = iter(
        [
            b"HTTP/1.1 301 OK\r\nLocation: //example.com/index\r\n\r\n",
            SERVER_RESPONSE_200_OK,
        ]
    )
    socket.socket = lambda *a, **k: Socket(next(server))

    response = requests.request("GET", "http://example.com")

    assert response.raw._write_buffer.getvalue() == (
        b"GET /index HTTP/1.1\r\nConnection: close\r\nHost: example.com\r\n\r\n"
    ), format_message(response)

    socket.socket = lambda *a, **k: Socket()


test_simple_get()
test_get_auth()
test_get_custom_header()
test_post_json()
test_post_json_unicode()
test_post_data_str()
test_post_data_str_unicode()
test_post_data_bytes()
test_post_chunked_data()
test_overwrite_get_headers()
test_overwrite_post_json_headers()
test_overwrite_post_chunked_data_headers()
test_do_not_modify_headers_argument()
test_content_length_via_content()
test_chunked_response_raises()
test_raw_open_before_content()
test_raw_incremental_content_length()
test_raw_readinto_content_length()
test_redirect_absolute()
test_redirect_relative()
test_redirect_protocol_relative()
