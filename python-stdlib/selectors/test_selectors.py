# Behaviour tests for selectors.
#
# The tests only use the public selectors API and also pass against CPython's
# stdlib selectors module, so a pass on both means this module behaves like
# CPython's.

import selectors
import socket
import time
import unittest

_next_port = [20000 + int(time.time() * 1000) % 20000]


def _listener():
    # Return (listening socket, its address).  MicroPython unix sockets have
    # no getsockname(), so ports are picked here instead of binding to port 0.
    while True:
        port = _next_port[0]
        _next_port[0] += 1
        addr = socket.getaddrinfo("127.0.0.1", port)[0][-1]
        listener = socket.socket()
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            listener.bind(addr)
        except OSError:
            listener.close()
            continue
        listener.listen(1)
        return listener, addr


def _ready(sel, timeout=0.5):
    # CPython's kqueue selector reports READ and WRITE as separate entries
    ready = {}
    for key, mask in sel.select(timeout):
        ready[key.data] = ready.get(key.data, 0) | mask
    return ready


class TestSelectors(unittest.TestCase):
    def setUp(self):
        # connected (listener, client, server-side) TCP socket triple
        self.listener, addr = _listener()
        self.client = socket.socket()
        self.client.connect(addr)
        self.conn, _ = self.listener.accept()
        self.conn.setblocking(False)
        self.client.setblocking(False)
        self.sel = selectors.DefaultSelector()

    def tearDown(self):
        self.sel.close()
        for sock in (self.listener, self.client, self.conn):
            sock.close()

    def test_constants(self):
        self.assertEqual(selectors.EVENT_READ, 1)
        self.assertEqual(selectors.EVENT_WRITE, 2)

    def test_register_returns_key(self):
        key = self.sel.register(self.conn, selectors.EVENT_READ, "data")
        self.assertIs(key.fileobj, self.conn)
        self.assertEqual(key.events, selectors.EVENT_READ)
        self.assertEqual(key.data, "data")
        self.assertEqual(self.sel.get_key(self.conn), key)
        self.assertIn(self.conn, self.sel.get_map())

    def test_register_errors(self):
        sel = self.sel
        with self.assertRaises(ValueError):
            sel.register(self.conn, 0)
        with self.assertRaises(ValueError):
            sel.register(self.conn, 4)
        with self.assertRaises(ValueError):
            sel.register(object(), selectors.EVENT_READ)
        with self.assertRaises(ValueError):
            sel.register(-1, selectors.EVENT_READ)
        self.assertEqual(len(sel.get_map()), 0)
        sel.register(self.conn, selectors.EVENT_READ)
        with self.assertRaises(KeyError):
            sel.register(self.conn, selectors.EVENT_READ)

    def test_select_after_invalid_register(self):
        # A rejected object must not break the selector, neither for objects
        # registered before it nor for ones registered after it
        self.sel.register(self.client, selectors.EVENT_WRITE, "client")
        with self.assertRaises(ValueError):
            self.sel.register(object(), selectors.EVENT_READ)
        self.sel.register(self.conn, selectors.EVENT_READ, "conn")
        self.client.send(b"x")
        time.sleep(0.05)
        self.assertEqual(
            _ready(self.sel),
            {"conn": selectors.EVENT_READ, "client": selectors.EVENT_WRITE})
        self.sel.unregister(self.client)
        self.assertEqual(_ready(self.sel), {"conn": selectors.EVENT_READ})

    def test_unregister(self):
        key = self.sel.register(self.conn, selectors.EVENT_READ, "x")
        self.assertEqual(self.sel.unregister(self.conn), key)
        with self.assertRaises(KeyError):
            self.sel.unregister(self.conn)
        with self.assertRaises(KeyError):
            self.sel.get_key(self.conn)
        self.client.send(b"hello")
        time.sleep(0.05)
        self.assertEqual(self.sel.select(0), [])

    def test_unregister_after_close(self):
        # Unregistering an already closed socket must work
        self.sel.register(self.conn, selectors.EVENT_READ)
        self.conn.close()
        self.sel.unregister(self.conn)
        self.assertEqual(len(self.sel.get_map()), 0)

    def test_select_timeout(self):
        self.sel.register(self.conn, selectors.EVENT_READ)
        start = time.time()
        self.assertEqual(self.sel.select(0.1), [])
        elapsed = time.time() - start
        self.assertTrue(0.05 <= elapsed < 1, elapsed)
        self.assertEqual(self.sel.select(0), [])
        self.assertEqual(self.sel.select(-1), [])

    def test_select_read_write(self):
        self.sel.register(self.conn, selectors.EVENT_READ, "conn")
        self.sel.register(self.client, selectors.EVENT_WRITE, "client")
        self.assertEqual(_ready(self.sel), {"client": selectors.EVENT_WRITE})
        self.client.send(b"ping")
        time.sleep(0.05)
        self.assertEqual(
            _ready(self.sel),
            {"conn": selectors.EVENT_READ, "client": selectors.EVENT_WRITE})
        self.assertEqual(self.conn.recv(16), b"ping")
        self.assertEqual(_ready(self.sel), {"client": selectors.EVENT_WRITE})

    def test_select_masks_by_key_events(self):
        # Only the registered events are reported
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(self.conn, events, "conn")
        self.assertEqual(_ready(self.sel), {"conn": selectors.EVENT_WRITE})
        self.client.send(b"x")
        time.sleep(0.05)
        self.assertEqual(_ready(self.sel), {"conn": events})

    def test_select_accept(self):
        listener, addr = _listener()
        self.sel.register(listener, selectors.EVENT_READ, "listener")
        self.assertEqual(self.sel.select(0), [])
        client = socket.socket()
        client.connect(addr)
        self.assertEqual(_ready(self.sel), {"listener": selectors.EVENT_READ})
        conn, _ = listener.accept()
        for sock in (listener, client, conn):
            sock.close()

    def test_peer_close_reports_read(self):
        self.sel.register(self.conn, selectors.EVENT_READ, "conn")
        self.client.close()
        time.sleep(0.05)
        self.assertEqual(_ready(self.sel), {"conn": selectors.EVENT_READ})
        self.assertEqual(self.conn.recv(16), b"")

    def test_modify(self):
        sel = self.sel
        key = sel.register(self.conn, selectors.EVENT_READ, "a")
        self.assertEqual(sel.select(0), [])
        self.assertEqual(sel.modify(self.conn, selectors.EVENT_READ, "a"), key)
        key2 = sel.modify(self.conn, selectors.EVENT_READ, "b")
        self.assertEqual(key2.data, "b")
        self.assertEqual(sel.get_key(self.conn), key2)
        key3 = sel.modify(self.conn, selectors.EVENT_WRITE, "c")
        self.assertEqual(key3.events, selectors.EVENT_WRITE)
        self.assertEqual(_ready(sel), {"c": selectors.EVENT_WRITE})
        with self.assertRaises(ValueError):
            sel.modify(self.conn, 0)
        with self.assertRaises(KeyError):
            sel.modify(self.client, selectors.EVENT_READ)

    def test_close(self):
        sel = self.sel
        sel.register(self.conn, selectors.EVENT_READ)
        sel.close()
        self.assertIsNone(sel.get_map())
        with self.assertRaises(RuntimeError):
            sel.get_key(self.conn)
        with self.assertRaises(KeyError):
            sel.unregister(self.conn)
        with self.assertRaises(KeyError):
            sel.modify(self.conn, selectors.EVENT_READ)
        with self.assertRaises(ValueError):
            sel.register(self.client, selectors.EVENT_READ)
        with self.assertRaises(ValueError):
            sel.select(0)
        sel.close()  # idempotent

    def test_context_manager(self):
        with selectors.DefaultSelector() as sel:
            sel.register(self.conn, selectors.EVENT_READ)
        self.assertIsNone(sel.get_map())


if __name__ == "__main__":
    unittest.main()
