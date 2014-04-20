import time
import heapq


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
#        print("Scheduling", (time, self.cnt, callback, args))
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
                    print("Send args:", args)
                    ret = cb.send(*args)
                    print("ret:", ret)
                    if isinstance(ret, SysCall):
                        if isinstance(ret, Sleep):
                            delay = ret.args[0]
                        elif isinstance(ret, IORead):
                            self.add_reader(ret.obj.fileno(), lambda f: self.call_soon(cb, f), ret.obj)
                            continue
                        elif isinstance(ret, IOWrite):
                            self.add_writer(ret.obj.fileno(), lambda f: self.call_soon(cb, f), ret.obj)
                            continue
                except StopIteration as e:
                    print(cb, "finished")
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
        print("add_reader")
        self.poller.register(fd, select.EPOLLIN, (cb, args))

    def add_writer(self, fd, cb, *args):
        print("add_writer")
        self.poller.register(fd, select.EPOLLOUT, (cb, args))

    def wait(self, delay):
        print("epoll.wait", delay)
        if delay == -1:
            res = self.poller.poll(-1)
        else:
            res = self.poller.poll(int(delay * 1000))
        print("poll: ", res)
        for cb, ev in res:
            print("Calling %s%s" % (cb[0], cb[1]))
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
        print("readline")
        s = yield IORead(self.s)
        print("after IORead")
        res = self.s.readline()
        print("readline res:", res)
        return res


class StreamWriter:

    def __init__(self, s):
        self.s = s

    def write(self, buf):
        print("Write!")
        res = self.s.write(buf)
        print("write res:", res)
        s = yield IOWrite(self.s)
        print("returning write res:", res)


def open_connection(host, port):
    s = _socket.socket()
    s.setblocking(False)
    ai = _socket.getaddrinfo(host, port)
    addr = ai[0][4]
    try:
        s.connect(addr)
    except OSError as e:
        print(e.args[0])
    print("After connect")
    s = yield IOWrite(s)
    print("After iowait:", s)
    return StreamReader(s), StreamWriter(s)
