import uerrno
import uselect as select
import usocket as _socket
from uasyncio.core import *


DEBUG = 0
log = None

def set_debug(val):
    global DEBUG, log
    DEBUG = val
    if val:
        import logging
        log = logging.getLogger("uasyncio")


class PollEventLoop(EventLoop):

    def __init__(self, len=42):
        EventLoop.__init__(self, len)
        self.poller = select.poll()
        self.objmap = {}

    def add_reader(self, sock, cb, *args):
        if DEBUG and __debug__:
            log.debug("add_reader%s", (sock, cb, args))
        if args:
            self.poller.register(sock, select.POLLIN)
            self.objmap[id(sock)] = (cb, args)
        else:
            self.poller.register(sock, select.POLLIN)
            self.objmap[id(sock)] = cb

    def remove_reader(self, sock):
        if DEBUG and __debug__:
            log.debug("remove_reader(%s)", sock)
        self.poller.unregister(sock)
        del self.objmap[id(sock)]

    def add_writer(self, sock, cb, *args):
        if DEBUG and __debug__:
            log.debug("add_writer%s", (sock, cb, args))
        if args:
            self.poller.register(sock, select.POLLOUT)
            self.objmap[id(sock)] = (cb, args)
        else:
            self.poller.register(sock, select.POLLOUT)
            self.objmap[id(sock)] = cb

    def remove_writer(self, sock):
        if DEBUG and __debug__:
            log.debug("remove_writer(%s)", sock)
        try:
            self.poller.unregister(sock)
            self.objmap.pop(id(sock), None)
        except OSError as e:
            # StreamWriter.awrite() first tries to write to a socket,
            # and if that succeeds, yield IOWrite may never be called
            # for that socket, and it will never be added to poller. So,
            # ignore such error.
            if e.args[0] != uerrno.ENOENT:
                raise

    def wait(self, delay):
        if DEBUG and __debug__:
            log.debug("poll.wait(%d)", delay)
        # We need one-shot behavior (second arg of 1 to .poll())
        res = self.poller.ipoll(delay, 1)
        #log.debug("poll result: %s", res)
        # Remove "if res" workaround after
        # https://github.com/micropython/micropython/issues/2716 fixed.
        if res:
            for sock, ev in res:
                cb = self.objmap[id(sock)]
                if DEBUG and __debug__:
                    log.debug("Calling IO callback: %r", cb)
                if isinstance(cb, tuple):
                    cb[0](*cb[1])
                else:
                    self.call_soon(cb)


class StreamReader:

    def __init__(self, s):
        self.s = s

    def read(self, n=-1):
        while True:
            yield IORead(self.s)
            res = self.s.read(n)
            if res is not None:
                break
            log.warn("Empty read")
        if not res:
            yield IOReadDone(self.s)
        return res

    def readexactly(self, n):
        buf = b""
        while n:
            yield IORead(self.s)
            res = self.s.read(n)
            assert res is not None
            if not res:
                yield IOReadDone(self.s)
                break
            buf += res
            n -= len(res)
        return buf

    def readline(self):
        if DEBUG and __debug__:
            log.debug("StreamReader.readline()")
        buf = b""
        while True:
            yield IORead(self.s)
            res = self.s.readline()
            assert res is not None
            if not res:
                yield IOReadDone(self.s)
                break
            buf += res
            if buf[-1] == 0x0a:
                break
        if DEBUG and __debug__:
            log.debug("StreamReader.readline(): %s", buf)
        return buf

    def aclose(self):
        yield IOReadDone(self.s)
        self.s.close()

    def __repr__(self):
        return "<StreamReader %r>" % self.s


class StreamWriter:

    def __init__(self, s, extra):
        self.s = s
        self.extra = extra

    def awrite(self, buf, off=0, sz=-1):
        # This method is called awrite (async write) to not proliferate
        # incompatibility with original asyncio. Unlike original asyncio
        # whose .write() method is both not a coroutine and guaranteed
        # to return immediately (which means it has to buffer all the
        # data), this method is a coroutine.
        if sz == -1:
            sz = len(buf) - off
        if DEBUG and __debug__:
            log.debug("StreamWriter.awrite(): spooling %d bytes", sz)
        while True:
            res = self.s.write(buf, off, sz)
            # If we spooled everything, return immediately
            if res == sz:
                if DEBUG and __debug__:
                    log.debug("StreamWriter.awrite(): completed spooling %d bytes", res)
                return
            if res is None:
                res = 0
            if DEBUG and __debug__:
                log.debug("StreamWriter.awrite(): spooled partial %d bytes", res)
            assert res < sz
            off += res
            sz -= res
            yield IOWrite(self.s)
            #assert s2.fileno() == self.s.fileno()
            if DEBUG and __debug__:
                log.debug("StreamWriter.awrite(): can write more")

    # Write piecewise content from iterable (usually, a generator)
    def awriteiter(self, iterable):
        for buf in iterable:
            yield from self.awrite(buf)

    def aclose(self):
        yield IOWriteDone(self.s)
        self.s.close()

    def get_extra_info(self, name, default=None):
        return self.extra.get(name, default)

    def __repr__(self):
        return "<StreamWriter %r>" % self.s


def open_connection(host, port):
    if DEBUG and __debug__:
        log.debug("open_connection(%s, %s)", host, port)
    s = _socket.socket()
    s.setblocking(False)
    ai = _socket.getaddrinfo(host, port)
    addr = ai[0][4]
    try:
        s.connect(addr)
    except OSError as e:
        if e.args[0] != uerrno.EINPROGRESS:
            raise
    if DEBUG and __debug__:
        log.debug("open_connection: After connect")
    yield IOWrite(s)
#    if __debug__:
#        assert s2.fileno() == s.fileno()
    if DEBUG and __debug__:
        log.debug("open_connection: After iowait: %s", s)
    return StreamReader(s), StreamWriter(s, {})


def start_server(client_coro, host, port, backlog=10):
    if DEBUG and __debug__:
        log.debug("start_server(%s, %s)", host, port)
    s = _socket.socket()
    s.setblocking(False)

    ai = _socket.getaddrinfo(host, port)
    addr = ai[0][4]
    s.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(backlog)
    while True:
        if DEBUG and __debug__:
            log.debug("start_server: Before accept")
        yield IORead(s)
        if DEBUG and __debug__:
            log.debug("start_server: After iowait")
        s2, client_addr = s.accept()
        s2.setblocking(False)
        if DEBUG and __debug__:
            log.debug("start_server: After accept: %s", s2)
        extra = {"peername": client_addr}
        yield client_coro(StreamReader(s2), StreamWriter(s2, extra))


import uasyncio.core
uasyncio.core._event_loop_class = PollEventLoop
