"""Live HTTP tests using a local TCP server (unix port / network stack).

Run with MicroPython unix:
  micropython test_requests_live.py
"""

import sys
import time

try:
    import _thread
except ImportError:
    _thread = None


def _prefer_filesystem_requests():
    try:
        import os

        os.stat("/lib/requests/__init__.py")
        if "/lib" not in sys.path[:1]:
            sys.path.insert(0, "/lib")
    except OSError:
        pass


_prefer_filesystem_requests()

if "requests" in sys.modules:
    del sys.modules["requests"]

import socket

import requests

_next_port = 52000


def _alloc_port():
    global _next_port
    port = _next_port
    _next_port += 1
    return port


def _bind_addr(port):
    return socket.getaddrinfo("127.0.0.1", port)[0][-1]


def _drain_request(conn):
    while True:
        line = conn.readline()
        if not line or line == b"\r\n":
            break


def _run_server(port, response_bytes):
    srv = socket.socket()
    srv.bind(_bind_addr(port))
    srv.listen(1)
    srv.settimeout(10)
    conn, addr = srv.accept()
    _drain_request(conn)
    conn.send(response_bytes)
    conn.close()
    srv.close()


def _fetch(port, path="/", method="GET", **kw):
    url = "http://127.0.0.1:{}{}".format(port, path)
    return requests.request(method, url, **kw)


def test_live_content_length():
    port = _alloc_port()
    body = b"live-ok"
    resp_bytes = b"HTTP/1.1 200 OK\r\nContent-Length: 7\r\n\r\n" + body
    _thread.start_new_thread(_run_server, (port, resp_bytes))
    time.sleep(0.2)
    r = _fetch(port)
    assert r.status_code == 200
    assert r.content == body


def test_live_chunked():
    port = _alloc_port()
    resp_bytes = b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n0\r\n\r\n"
    _thread.start_new_thread(_run_server, (port, resp_bytes))
    time.sleep(0.2)
    r = _fetch(port)
    assert r.content == b"hello"


def test_live_redirect_relative():
    port = _alloc_port()
    first = b"HTTP/1.1 302 Found\r\nLocation: /done\r\nConnection: close\r\n\r\n"
    second = b"HTTP/1.1 200 OK\r\nContent-Length: 3\r\n\r\nyes"

    def multi_server():
        srv = socket.socket()
        srv.bind(_bind_addr(port))
        srv.listen(1)
        srv.settimeout(10)
        for resp in (first, second):
            conn, addr = srv.accept()
            _drain_request(conn)
            conn.send(resp)
            conn.close()
        srv.close()

    _thread.start_new_thread(multi_server, ())
    time.sleep(0.2)
    r = _fetch(port, "/start")
    assert r.content == b"yes"


def test_live_max_body():
    port = _alloc_port()
    body = b"0123456789"
    resp_bytes = b"HTTP/1.1 200 OK\r\nContent-Length: 10\r\n\r\n" + body
    _thread.start_new_thread(_run_server, (port, resp_bytes))
    time.sleep(0.2)
    raised = False
    try:
        _fetch(port, max_body=5)
    except ValueError:
        raised = True
    if not raised:
        raise AssertionError("expected max_body ValueError")


LIVE_TESTS = (
    test_live_content_length,
    test_live_chunked,
    test_live_redirect_relative,
    test_live_max_body,
)


def run_all():
    if _thread is None:
        print("test_requests_live: SKIP (no _thread)")
        return
    for test in LIVE_TESTS:
        test()


if __name__ == "__main__":
    run_all()
    print("test_requests_live: {} tests OK".format(len(LIVE_TESTS)))
