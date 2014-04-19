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
        while self.q:
#            t, cnt, cb, args = self.q.pop(0)
            t, cnt, cb, args = heapq.heappop(self.q)
            tnow = self.time()
            delay = t - tnow
            if delay > 0:
                self.wait(delay)
            delay = 0
            try:
                ret = next(cb)
#                print("ret:", ret)
                if isinstance(ret, Sleep):
                    delay = ret.args[0]
            except StopIteration as e:
                print(c, "finished")
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
        self.poller.register(fd, select.EPOLLIN, (cb, args))

    def add_writer(self, fd, cb, *args):
        self.poller.register(fd, select.EPOLLOUT, (cb, args))

    def wait(self, delay):
        res = self.poller.poll(int(delay * 1000))
        print("poll: ", res)
        for cb, ev in res:
            cb[0](*cb[1])


class SysCall:

    def __init__(self, call, *args):
        self.call = call
        self.args = args

class Sleep(SysCall):

    def handle(self):
        time.sleep(self.args[0])


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
