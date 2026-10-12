# selectors

This library implements a subset of CPython's
[`selectors`](https://docs.python.org/3/library/selectors.html) module as a
thin layer over MicroPython's built-in
[`select.poll()`](https://docs.micropython.org/en/latest/library/select.html).
It lets code written for CPython's high-level I/O multiplexing API run
unchanged on MicroPython, on both the unix port and bare-metal ports.

## Example

```python
import selectors
import socket

sel = selectors.DefaultSelector()

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(socket.getaddrinfo("0.0.0.0", 8080)[0][-1])
server.listen(5)
sel.register(server, selectors.EVENT_READ, "accept")

while True:
    for key, events in sel.select(timeout=1):
        if key.data == "accept":
            conn, addr = server.accept()
            conn.setblocking(False)
            sel.register(conn, selectors.EVENT_READ, "client")
        else:
            data = key.fileobj.recv(512)
            if data:
                key.fileobj.send(data)
            else:
                sel.unregister(key.fileobj)
                key.fileobj.close()
```

## Supported API

- `EVENT_READ`, `EVENT_WRITE`
- `SelectorKey(fileobj, fd, events, data)` named tuple
- `BaseSelector` with `register()`, `unregister()`, `modify()`, `select()`,
  `close()`, `get_key()`, `get_map()` and context manager support
- `PollSelector`, and `DefaultSelector` as an alias for it

Error handling follows CPython: invalid event masks or file objects raise
`ValueError`, registering an object twice or using an unregistered object
raises `KeyError`, and `get_key()` on a closed selector raises `RuntimeError`.

`select(timeout)` accepts `None` (block), a value `<= 0` (poll without
waiting) or a timeout in seconds (float allowed), and returns a list of
`(key, events)` tuples.  Error and hang-up conditions are reported as both
read and write readiness, masked by the events the object was registered for,
the same way as CPython's `PollSelector` does.

## Differences from CPython

- File objects are tracked by identity, not by file descriptor, because
  sockets on bare-metal ports have no `fileno()`.  Any object supported by
  `select.poll()` can be registered, e.g. sockets, SSL sockets, UARTs or
  `sys.stdin`.  On the unix port an integer file descriptor can be registered
  as well.
- `SelectorKey.fd` is the result of `fileno()` when the object provides it,
  otherwise `-1`.
- `get_map()` returns a plain `dict` keyed by the registered file object, so
  it cannot be indexed by file descriptor.  Treat it as read-only.
- Two different objects sharing the same file descriptor are not detected as
  a duplicate registration.
- Only `PollSelector` is provided; `SelectSelector`, `EpollSelector`,
  `DevpollSelector` and `KqueueSelector` are not available.

## Installation

Use `mip` via `mpremote`:

```bash
> mpremote mip install selectors
```

See [Package
management](https://docs.micropython.org/en/latest/reference/packages.html) for
more details on using `mip` and `mpremote`.
