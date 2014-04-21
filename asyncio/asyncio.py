import __main__
import time
import heapq
import errno
import logging


log = logging.getLogger("asyncio")

def coroutine(f):
    return f


class EventLoop:

    def __init__(self):
        self.q = []
        self.cnt = 0

    def time(self):
        return time.time()

    def call_soon(self, callback, *args):
        self.call_at(0, callback, *args)

    def call_later(self, delay, callback, *args):
        self.call_at(self.time() + delay, callback, *args)

    def call_at(self, time, callback, *args):
#        self.q.append((callback, args))
        # self.cnt is workaround per heapq docs
        log.debug("Scheduling %s", (time, self.cnt, callback, args))
        heapq.heappush(self.q, (time, self.cnt, callback, args))
#        print(self.q)
        self.cnt += 1

#    def run_forever(self):
#        while self.q:
#            c = self.q.pop(0)
#            c[0](*c[1])

    def wait(self, delay):
#        print("Sleeping for:", delay)
        time.sleep(delay)

    def run_forever(self):
        while True:
            if self.q:
                t, cnt, cb, args = heapq.heappop(self.q)
                log.debug("Next task to run: %s", (t, cnt, cb, args))
#                __main__.mem_info()
                tnow = self.time()
                delay = t - tnow
                if delay > 0:
                    self.wait(delay)
            else:
                self.wait(-1)
                # Assuming IO completion scheduled some tasks
                continue
            if callable(cb):
                cb(*args)
            else:
                delay = 0
                try:
                    if args == ():
                        args = (None,)
                    log.debug("Gen send args: %s", args)
                    ret = cb.send(*args)
                    log.debug("Gen yield result: %s", ret)
                    if isinstance(ret, SysCall):
                        if isinstance(ret, Sleep):
                            delay = ret.args[0]
                        elif isinstance(ret, IORead):
#                            self.add_reader(ret.obj.fileno(), lambda self, c, f: self.call_soon(c, f), self, cb, ret.obj)
#                            self.add_reader(ret.obj.fileno(), lambda c, f: self.call_soon(c, f), cb, ret.obj)
                            self.add_reader(ret.obj.fileno(), lambda f: self.call_soon(cb, f), ret.obj)
                            continue
                        elif isinstance(ret, IOWrite):
                            self.add_writer(ret.obj.fileno(), lambda f: self.call_soon(cb, f), ret.obj)
                            continue
                except StopIteration as e:
                    log.debug("Gen finished: %s", cb)
                    continue
                #self.q.append(c)
                self.call_later(delay, cb, *args)

    def run_until_complete(self, coro):
        val = None
        while True:
            try:
                ret = coro.send(val)
            except StopIteration as e:
                print(e)
                break
            print("ret:", ret)
            if isinstance(ret, SysCall):
                ret.handle()

    def close(self):
        pass

import select

class EpollEventLoop(EventLoop):

    def __init__(self):
        EventLoop.__init__(self)
        self.poller = select.epoll(1)

    def add_reader(self, fd, cb, *args):
        log.debug("add_reader%s", (fd, cb, args))
        self.poller.register(fd, select.EPOLLIN, (cb, args))

    def add_writer(self, fd, cb, *args):
        log.debug("add_writer%s", (fd, cb, args))
        self.poller.register(fd, select.EPOLLOUT, (cb, args))

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


class SysCall:

    def __init__(self, call, *args):
        self.call = call
        self.args = args

class Sleep(SysCall):

    def handle(self):
        time.sleep(self.args[0])

class IORead(SysCall):

    def __init__(self, obj):
        self.obj = obj

class IOWrite(SysCall):

    def __init__(self, obj):
        self.obj = obj


def get_event_loop():
    return EpollEventLoop()

def sleep(secs):
    yield Sleep("sleep", secs)

def sleep2(secs):
    t = time.time()
#    print("Started sleep:", t, "targetting:", t + secs)
    while time.time() < t + secs:
        time.sleep(0.01)
        yield None
#    print("Finished sleeping", secs)
#    time.sleep(secs)


import microsocket as _socket

class StreamReader:

    def __init__(self, s):
        self.s = s

    def readline(self):
        log.debug("StreamReader.readline()")
        s = yield IORead(self.s)
        log.debug("StreamReader.readline(): after IORead: %s", s)
        res = self.s.readline()
        log.debug("StreamReader.readline(): res: %s", res)
        return res


class StreamWriter:

    def __init__(self, s):
        self.s = s

    def write(self, buf):
        res = self.s.write(buf)
        log.debug("StreamWriter.write(): %d", res)
        s = yield IOWrite(self.s)
        log.debug("StreamWriter.write(): returning")


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
