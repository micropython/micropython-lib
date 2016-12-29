import errno
import uselect as select
import usocket as _socket
from uasyncio.core import *


class EpollEventLoop(EventLoop):

    def __init__(self):
        EventLoop.__init__(self)
        self.poller = select.poll()
        self.objmap = {}

    def add_reader(self, fd, cb, *args):
        if DEBUG and __debug__:
            log.debug("add_reader%s", (fd, cb, args))
        if args:
            self.poller.register(fd, select.POLLIN)
            self.objmap[fd] = (cb, args)
        else:
            self.poller.register(fd, select.POLLIN)
            self.objmap[fd] = cb

    def remove_reader(self, fd):
        if DEBUG and __debug__:
            log.debug("remove_reader(%s)", fd)
        self.poller.unregister(fd)
        del self.objmap[fd]

    def add_writer(self, fd, cb, *args):
        if DEBUG and __debug__:
            log.debug("add_writer%s", (fd, cb, args))
        if args:
            self.poller.register(fd, select.POLLOUT)
            self.objmap[fd] = (cb, args)
        else:
            self.poller.register(fd, select.POLLOUT)
            self.objmap[fd] = cb

    def remove_writer(self, fd):
        if DEBUG and __debug__:
            log.debug("remove_writer(%s)", fd)
        try:
            self.poller.unregister(fd)
            self.objmap.pop(fd, None)
        except OSError as e:
            # StreamWriter.awrite() first tries to write to an fd,
            # and if that succeeds, yield IOWrite may never be called
            # for that fd, and it will never be added to poller. So,
            # ignore such error.
            if e.args[0] != errno.ENOENT:
                raise

    def wait(self, delay):
        if DEBUG and __debug__:
            log.debug("epoll.wait(%d)", delay)
        # We need one-shot behavior (second arg of 1 to .poll())
        if delay == -1:
            res = self.poller.poll(-1, 1)
        else:
            res = self.poller.poll(delay, 1)
        #log.debug("epoll result: %s", res)
        # Remove "if res" workaround after
        # https://github.com/micropython/micropython/issues/2716 fixed.
        if res:
            for fd, ev in res:
                cb = self.objmap[fd]
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
        yield IORead(self.s)
        while True:
            res = self.s.read(n)
            if res is not None:
                break
            log.warn("Empty read")
        if not res:
            yield IOReadDone(self.s)
        return res

    def readline(self):
        if __debug__:
            log.debug("StreamReader.readline()")
        yield IORead(self.s)
#        if DEBUG and __debug__:
#            log.debug("StreamReader.readline(): after IORead: %s", s)
        while True:
            res = self.s.readline()
            if res is not None:
                break
            log.warn("Empty read")
        if not res:
            yield IOReadDone(self.s)
        if DEBUG and __debug__:
            log.debug("StreamReader.readline(): res: %s", res)
        return res

    def aclose(self):
        yield IOReadDone(self.s)
        self.s.close()

    def __repr__(self):
        return "<StreamReader %r>" % self.s


class StreamWriter:

    def __init__(self, s, extra):
        self.s = s
        self.extra = extra

    def awrite(self, buf):
        # This method is called awrite (async write) to not proliferate
        # incompatibility with original asyncio. Unlike original asyncio
        # whose .write() method is both not a coroutine and guaranteed
        # to return immediately (which means it has to buffer all the
        # data), this method is a coroutine.
        sz = len(buf)
        if DEBUG and __debug__:
            log.debug("StreamWriter.awrite(): spooling %d bytes", sz)
        while True:
            res = self.s.write(buf)
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
            buf = buf[res:]
            sz -= res
            yield IOWrite(self.s)
            #assert s2.fileno() == self.s.fileno()
            if __debug__:
                log.debug("StreamWriter.awrite(): can write more")

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
        if e.args[0] != errno.EINPROGRESS:
            raise
    if __debug__:
        log.debug("open_connection: After connect")
    yield IOWrite(s)
#    if __debug__:
#        assert s2.fileno() == s.fileno()
    if DEBUG and __debug__:
        log.debug("open_connection: After iowait: %s", s)
    return StreamReader(s), StreamWriter(s, {})


def start_server(client_coro, host, port, backlog=10):
    log.debug("start_server(%s, %s)", host, port)
    s = _socket.socket()
    s.setblocking(False)

    ai = _socket.getaddrinfo(host, port)
    addr = ai[0][4]
    s.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(backlog)
    while True:
        if __debug__:
            log.debug("start_server: Before accept")
        yield IORead(s)
        if __debug__:
            log.debug("start_server: After iowait")
        s2, client_addr = s.accept()
        s2.setblocking(False)
        if DEBUG and __debug__:
            log.debug("start_server: After accept: %s", s2)
        extra = {"peername": client_addr}
        yield client_coro(StreamReader(s2), StreamWriter(s2, extra))


import uasyncio.core
uasyncio.core._event_loop_class = EpollEventLoop
