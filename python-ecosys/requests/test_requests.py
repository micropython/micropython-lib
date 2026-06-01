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
        b"GET / HTTP/1.1\r\n" + b"Host: example.com\r\n" + b"Connection: close\r\n\r\n"
    ), format_message(response)
    assert response.content == b""


def test_get_auth():
    response = requests.request(
        "GET", "http://example.com", auth=("test-username", "test-password")
    )

    assert response.raw._write_buffer.getvalue() == (
        b"GET / HTTP/1.1\r\n"
        + b"Authorization: Basic dGVzdC11c2VybmFtZTp0ZXN0LXBhc3N3b3Jk\r\n"
        + b"Host: example.com\r\n"
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
        + b"Host: example.com\r\n"
        + b"Content-Type: application/json\r\n"
        + b"Content-Length: 6\r\n"
        + b"Connection: close\r\n\r\n"
        + b'"test"'
    ), format_message(response)


def test_post_chunked_data():
    def chunks():
        yield "test"

    response = requests.request("GET", "http://example.com", data=chunks())

    assert response.raw._write_buffer.getvalue() == (
        b"GET / HTTP/1.1\r\n"
        + b"Host: example.com\r\n"
        + b"Transfer-Encoding: chunked\r\n"
        + b"Connection: close\r\n\r\n"
        + b"4\r\ntest\r\n"
        + b"0\r\n\r\n"
    ), format_message(response)


def test_overwrite_get_headers():
    response = requests.request(
        "GET", "http://example.com", headers={"Host": "test.com", "Connection": "keep-alive"}
    )

    assert response.raw._write_buffer.getvalue() == (
        b"GET / HTTP/1.1\r\n" + b"Host: test.com\r\n" + b"Connection: keep-alive\r\n\r\n"
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
        + b"Content-Type: text/plain\r\n"
        + b"Content-Length: 10\r\n"
        + b"Host: example.com\r\n"
        + b"Connection: close\r\n\r\n"
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
        + b"Content-Length: 4\r\n"
        + b"Host: example.com\r\n"
        + b"Connection: close\r\n\r\n"
        + b"test"
    ), format_message(response)


def test_do_not_modify_headers_argument():
    global do_not_modify_this_dict
    do_not_modify_this_dict = {}
    requests.request("GET", "http://example.com", headers=do_not_modify_this_dict)

    assert do_not_modify_this_dict == {}, do_not_modify_this_dict


def test_content_length_body():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello"
    )
    response = requests.request("GET", "http://example.com")
    assert response.content == b"hello"
    assert response.headers["content-length"] == "5"


def test_chunked_body():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n0\r\n\r\n"
    )
    response = requests.request("GET", "http://example.com")
    assert response.content == b"hello"


def test_case_insensitive_headers():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK"
    )
    response = requests.request("GET", "http://example.com")
    assert response.headers["content-length"] == "2"
    assert response.headers["Content-Length"] == "2"


def test_max_body_limit():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nContent-Length: 10\r\n\r\n" + b"x" * 10
    )
    try:
        requests.request("GET", "http://example.com", max_body=5)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "max_body" in str(e)


def test_relative_redirect():
    calls = []

    def socket_factory(*a, **k):
        if not calls:
            calls.append(1)
            return Socket(read_data=b"HTTP/1.1 302 Found\r\nLocation: /other\r\n\r\n")
        return Socket(read_data=b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok")

    socket.socket = socket_factory
    response = requests.request("GET", "http://example.com/path/here")
    assert response.content == b"ok"
    assert b"GET /other HTTP/1.1" in response.raw._write_buffer.getvalue()


test_simple_get()
test_get_auth()
test_get_custom_header()
test_post_json()
test_post_chunked_data()
test_overwrite_get_headers()
test_overwrite_post_json_headers()
test_overwrite_post_chunked_data_headers()
test_do_not_modify_headers_argument()
test_content_length_body()
test_chunked_body()
test_case_insensitive_headers()
test_max_body_limit()
test_relative_redirect()
