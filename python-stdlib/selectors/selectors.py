"""selectors - CPython compatible selectors module for MicroPython

Thin layer over MicroPython's select.poll(), usable like the CPython module:

    import selectors
    sel = selectors.DefaultSelector()
    sel.register(sock, selectors.EVENT_READ, data)
    for key, mask in sel.select(timeout):
        ...

Differences from CPython:
- objects are keyed by identity, not by file descriptor (bare-metal
  sockets have no fileno()); SelectorKey.fd is fileno() when available,
  else -1
- get_map() returns a plain dict keyed by file object (treat it as
  read-only)
- only PollSelector is provided, DefaultSelector is an alias for it

MIT license; Copyright (c) 2026 Pavel Revak <pavelrevak@gmail.com>
"""

import select as _select
from collections import namedtuple as _namedtuple

EVENT_READ = 1 << 0
EVENT_WRITE = 1 << 1

_EVENTS_ALL = EVENT_READ | EVENT_WRITE
_POLLIN = _select.POLLIN
_POLLOUT = _select.POLLOUT

SelectorKey = _namedtuple("SelectorKey", ["fileobj", "fd", "events", "data"])


def _fileobj_to_fd(fileobj):
    """Return the file descriptor of fileobj, -1 if it has none"""
    if isinstance(fileobj, int):
        fd = fileobj
    else:
        try:
            fd = int(fileobj.fileno())
        except (AttributeError, TypeError, ValueError, OSError):
            return -1
    if fd < 0:
        raise ValueError("Invalid file descriptor: %d" % fd)
    return fd


def _check_events(events):
    if not events or events & ~_EVENTS_ALL:
        raise ValueError("Invalid events: %r" % (events,))


def _poll_mask(events):
    mask = 0
    if events & EVENT_READ:
        mask |= _POLLIN
    if events & EVENT_WRITE:
        mask |= _POLLOUT
    return mask


class BaseSelector:
    """Selector abstract base class"""

    def register(self, fileobj, events, data=None):
        raise NotImplementedError

    def unregister(self, fileobj):
        raise NotImplementedError

    def modify(self, fileobj, events, data=None):
        self.unregister(fileobj)
        return self.register(fileobj, events, data)

    def select(self, timeout=None):
        raise NotImplementedError

    def close(self):
        pass

    def get_map(self):
        raise NotImplementedError

    def get_key(self, fileobj):
        """Return the key registered for fileobj.

        Raises KeyError if not registered, RuntimeError if closed.
        """
        mapping = self.get_map()
        if mapping is None:
            raise RuntimeError("Selector is closed")
        if fileobj not in mapping:
            raise KeyError("%r is not registered" % (fileobj,))
        return mapping[fileobj]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class PollSelector(BaseSelector):
    """Selector based on MicroPython select.poll()"""

    def __init__(self):
        self._poll = _select.poll()
        self._map = {}

    def _lookup(self, fileobj):
        if self._map is None or fileobj not in self._map:
            raise KeyError("%r is not registered" % (fileobj,))
        return self._map[fileobj]

    def register(self, fileobj, events, data=None):
        if self._map is None:
            raise ValueError("Selector is closed")
        _check_events(events)
        if fileobj in self._map:
            raise KeyError("%r is already registered" % (fileobj,))
        key = SelectorKey(fileobj, _fileobj_to_fd(fileobj), events, data)
        try:
            self._poll.register(fileobj, _poll_mask(events))
        except (TypeError, OSError):  # not a stream object
            # no chaining: MicroPython warns on 'raise ... from'
            raise ValueError("Invalid file object: %r" % (fileobj,))
        self._map[fileobj] = key
        return key

    def unregister(self, fileobj):
        key = self._lookup(fileobj)
        del self._map[fileobj]
        try:
            self._poll.unregister(fileobj)
        except OSError:
            pass  # object may already be closed
        return key

    def modify(self, fileobj, events, data=None):
        key = self._lookup(fileobj)
        _check_events(events)
        if events != key.events:
            self._poll.modify(fileobj, _poll_mask(events))
        elif data is key.data:
            return key
        key = SelectorKey(fileobj, key.fd, events, data)
        self._map[fileobj] = key
        return key

    def select(self, timeout=None):
        """Wait for registered objects to become ready or timeout expire.

        timeout: None blocks, <= 0 polls, else seconds (float allowed).
        Returns a list of (key, events) tuples.
        """
        if self._map is None:
            raise ValueError("Selector is closed")
        if timeout is None:
            timeout_ms = -1
        elif timeout <= 0:
            timeout_ms = 0
        else:
            # round up, so a short timeout does not turn into a busy poll
            timeout_ms = int(timeout * 1000)
            if timeout_ms < timeout * 1000:
                timeout_ms += 1
        ready = []
        for fileobj, revents in self._poll.ipoll(timeout_ms):
            key = self._map.get(fileobj)
            if key is None:
                continue
            # error/hangup flags wake both directions, like CPython
            events = 0
            if revents & ~_POLLIN:
                events |= EVENT_WRITE
            if revents & ~_POLLOUT:
                events |= EVENT_READ
            ready.append((key, events & key.events))
        return ready

    def close(self):
        self._map = None
        self._poll = None

    def get_map(self):
        return self._map


DefaultSelector = PollSelector
