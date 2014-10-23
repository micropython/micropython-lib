import errno
import select
import usocket as _socket
from uasyncio.core import *


class EpollEventLoop(EventLoop):

    def __init__(self):
        EventLoop.__init__(self)
        self.poller = select.epoll(1)

    def add_reader(self, fd, cb, *args):
        log.debug("add_reader%s", (fd, cb, args))
        self.poller.register(fd, select.EPOLLIN, (cb, args))

    def remove_reader(self, fd):
        log.debug("remove_reader(%s)", fd)
        self.poller.unregister(fd)

    def add_writer(self, fd, cb, *args):
        log.debug("add_writer%s", (fd, cb, args))
        self.poller.register(fd, select.EPOLLOUT, (cb, args))

    def remove_writer(self, fd):
        log.debug("remove_writer(%s)", fd)
        self.poller.unregister(fd)

    def wait(self, delay):
        log.debug("epoll.wait(%d)", delay)
        if delay == -1:
            res = self.poller.poll(-1)
        else:
            res = self.poller.poll(int(delay * 1000))
        log.debug("epoll result: %s", res)
        for cb, ev in res:
            log.debug("Calling IO callback: %s%s", cb[0], cb[1])
            cb[0](*cb[1])


def get_event_loop():
    return EpollEventLoop()


class StreamReader:

    def __init__(self, s):
        self.s = s

    def read(self, n=-1):
        s = yield IORead(self.s)
        while True:
            res = self.s.read(n)
            if res is not None:
                break
            log.warn("Empty read")
        if not res:
            yield IOReadDone(self.s)
        return res

    def readline(self):
        log.debug("StreamReader.readline()")
        s = yield IORead(self.s)
        log.debug("StreamReader.readline(): after IORead: %s", s)
        while True:
            res = self.s.readline()
            if res is not None:
                break
            log.warn("Empty read")
        if not res:
            yield IOReadDone(self.s)
        log.debug("StreamReader.readline(): res: %s", res)
        return res

    def __repr__(self):
        return "<StreamReader %r>" % self.s


class StreamWriter:

    def __init__(self, s):
        self.s = s

    def awrite(self, buf):
        # This method is called awrite (async write) to not proliferate
        # incompatibility with original asyncio. Unlike original asyncio
        # whose .write() method is both not a coroutine and guaranteed
        # to return immediately (which means it has to buffer all the
        # data), this method is a coroutine.
        sz = len(buf)
        log.debug("StreamWriter.awrite(): spooling %d bytes", sz)
        while True:
            res = self.s.write(buf)
            # If we spooled everything, return immediately
            if res == sz:
                log.debug("StreamWriter.awrite(): completed spooling %d bytes", res)
                return
            if res is None:
                res = 0
            log.debug("StreamWriter.awrite(): spooled partial %d bytes", res)
            assert res < sz
            buf = buf[res:]
            sz -= res
            s = yield IOWrite(self.s)
            log.debug("StreamWriter.awrite(): can write more")

    def close(self):
        yield IOWriteDone(self.s)
        self.s.close()

    def __repr__(self):
        return "<StreamWriter %r>" % self.s


def open_connection(host, port):
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
    log.debug("open_connection: After connect")
    s = yield IOWrite(s)
    log.debug("open_connection: After iowait: %s", s)
    return StreamReader(s), StreamWriter(s)


def start_server(client_coro, host, port):
    log.debug("start_server(%s, %s)", host, port)
    s = _socket.socket()
    s.setblocking(False)

    ai = _socket.getaddrinfo(host, port)
    addr = ai[0][4]
    s.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(10)
    while True:
        log.debug("start_server: Before accept")
        yield IORead(s)
        log.debug("start_server: After iowait")
        s2, client_addr = s.accept()
        s2.setblocking(False)
        log.debug("start_server: After accept: %s", s2)
        yield client_coro(StreamReader(s2), StreamWriter(s2))
