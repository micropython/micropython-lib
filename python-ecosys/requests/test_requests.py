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


def install_mock_socket():
    sys.modules["socket"] = socket


install_mock_socket()
# ruff: noqa: E402
import requests


def request_bytes(response):
    return response.raw._sock._write_buffer.getvalue()


def assert_has(data, *parts):
    for part in parts:
        if part not in data:
            raise AssertionError("missing {!r} in:\n{}".format(part, data))


def test_simple_get():
    install_mock_socket()
    response = requests.request("GET", "http://example.com")
    data = request_bytes(response)
    assert_has(
        data,
        b"GET / HTTP/1.1\r\n",
        b"Host: example.com\r\n",
        b"Connection: close\r\n",
        b"\r\n",
    )
    assert response.content == b""


def test_get_auth():
    install_mock_socket()
    response = requests.request(
        "GET", "http://example.com", auth=("test-username", "test-password")
    )
    data = request_bytes(response)
    assert_has(
        data,
        b"GET / HTTP/1.1\r\n",
        b"Authorization: Basic dGVzdC11c2VybmFtZTp0ZXN0LXBhc3N3b3Jk\r\n",
        b"Host: example.com\r\n",
        b"Connection: close\r\n",
    )


def test_get_custom_header():
    install_mock_socket()
    response = requests.request("GET", "http://example.com", headers={"User-Agent": "test-agent"})
    data = request_bytes(response)
    assert_has(
        data,
        b"GET / HTTP/1.1\r\n",
        b"User-Agent: test-agent\r\n",
        b"Host: example.com\r\n",
        b"Connection: close\r\n",
    )


def test_post_json():
    install_mock_socket()
    response = requests.request("GET", "http://example.com", json="test")
    data = request_bytes(response)
    assert_has(
        data,
        b"GET / HTTP/1.1\r\n",
        b"Content-Type: application/json\r\n",
        b"Host: example.com\r\n",
        b"Content-Length: 6\r\n",
        b"Connection: close\r\n",
        b'"test"',
    )


def test_post_chunked_data():
    def chunks():
        yield "test"

    install_mock_socket()
    response = requests.request("GET", "http://example.com", data=chunks())
    data = request_bytes(response)
    assert_has(
        data,
        b"GET / HTTP/1.1\r\n",
        b"Transfer-Encoding: chunked\r\n",
        b"Host: example.com\r\n",
        b"Connection: close\r\n",
        b"4\r\ntest\r\n",
        b"0\r\n\r\n",
    )


def test_overwrite_get_headers():
    install_mock_socket()
    response = requests.request(
        "GET", "http://example.com", headers={"Host": "test.com", "Connection": "keep-alive"}
    )
    data = request_bytes(response)
    assert_has(data, b"GET / HTTP/1.1\r\n", b"Host: test.com\r\n", b"Connection: keep-alive\r\n")


def test_overwrite_post_json_headers():
    install_mock_socket()
    response = requests.request(
        "GET",
        "http://example.com",
        json="test",
        headers={"Content-Type": "text/plain", "Content-Length": "10"},
    )
    data = request_bytes(response)
    assert_has(
        data,
        b"Content-Type: text/plain\r\n",
        b"Content-Length: 10\r\n",
        b"Host: example.com\r\n",
        b'"test"',
    )


def test_overwrite_post_chunked_data_headers():
    def chunks():
        yield "test"

    install_mock_socket()
    response = requests.request(
        "GET", "http://example.com", data=chunks(), headers={"Content-Length": "4"}
    )
    data = request_bytes(response)
    assert_has(data, b"Content-Length: 4\r\n", b"Host: example.com\r\n", b"test")


def test_do_not_modify_headers_argument():
    install_mock_socket()
    headers_arg = {}
    requests.request("GET", "http://example.com", headers=headers_arg)
    assert headers_arg == {}, headers_arg


def test_content_length_via_content():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello"
    )
    response = requests.request("GET", "http://example.com")
    assert response.content == b"hello"
    assert response.headers["Content-Length"] == "5"
    install_mock_socket()


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
    install_mock_socket()


def test_raw_open_before_content():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello"
    )
    response = requests.request("GET", "http://example.com")
    assert response.raw is not None
    assert response.raw.read(1) == b"h"
    install_mock_socket()


def test_raw_incremental_content_length():
    socket.socket = lambda *a, **k: Socket(
        read_data=b"HTTP/1.1 200 OK\r\nContent-Length: 10\r\n\r\nhelloworld"
    )
    response = requests.request("GET", "http://example.com")
    assert response.raw.read(3) == b"hel"
    assert response.raw.read(3) == b"low"
    assert response.raw.read() == b"orld"
    assert response.content == b"helloworld"
    assert response.raw is None
    install_mock_socket()


TESTS = (
    test_simple_get,
    test_get_auth,
    test_get_custom_header,
    test_post_json,
    test_post_chunked_data,
    test_overwrite_get_headers,
    test_overwrite_post_json_headers,
    test_overwrite_post_chunked_data_headers,
    test_do_not_modify_headers_argument,
    test_content_length_via_content,
    test_chunked_response_raises,
    test_raw_open_before_content,
    test_raw_incremental_content_length,
)


def run_all():
    for test in TESTS:
        test()


if __name__ == "__main__":
    run_all()
    print("test_requests: {} tests OK".format(len(TESTS)))
