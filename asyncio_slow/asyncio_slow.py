import time
import logging


log = logging.getLogger("asyncio")


# Workaround for not being able to subclass builtin types
class LoopStop(Exception):
    pass

class InvalidStateError(Exception):
    pass

# Object not matching any other object
_sentinel = []


class EventLoop:

    def __init__(self):
        self.q = []

    def call_soon(self, c, *args):
        self.q.append((c, args))

    def call_later(self, delay, c, *args):
        def _delayed(c, args, delay):
            yield from sleep(delay)
            self.call_soon(c, *args)
        Task(_delayed(c, args, delay))

    def run_forever(self):
        while self.q:
            c = self.q.pop(0)
            try:
                c[0](*c[1])
            except LoopStop:
                return
        # I mean, forever
        while True:
            time.sleep(1)

    def stop(self):
        def _cb():
            raise LoopStop
        self.call_soon(_cb)

    def run_until_complete(self, coro):
        t = async(coro)
        t.add_done_callback(lambda a: self.stop())
        self.run_forever()

    def close(self):
        pass


_def_event_loop = EventLoop()


class Future:

    def __init__(self, loop=_def_event_loop):
        self.loop = loop
        self.res = _sentinel
        self.cbs = []

    def result(self):
        if self.res is _sentinel:
            raise InvalidStateError
        return self.res

    def add_done_callback(self, fn):
        if self.res is _sentinel:
            self.cbs.append(fn)
        else:
            self.loop.call_soon(fn, self)

    def set_result(self, val):
        self.res = val
        for f in self.cbs:
            f(self)


class Task(Future):

    def __init__(self, coro, loop=_def_event_loop):
        super().__init__()
        self.loop = loop
        self.c = coro
        # upstream asyncio forces task to be scheduled on instantiation
        self.loop.call_soon(self)

    def __call__(self):
        try:
            next(self.c)
            self.loop.call_soon(self)
        except StopIteration as e:
            log.debug("Coro finished: %s", self.c)
            self.set_result(None)


def get_event_loop():
    return _def_event_loop


# Decorator
def coroutine(f):
    return f


def async(coro):
    if isinstance(coro, Future):
        return coro
    return Task(coro)


class Wait(Future):

    def __init__(self, n):
        Future.__init__(self)
        self.n = n

    def _done(self):
        self.n -= 1
        log.debug("Wait: remaining tasks: %d", self.n)
        if not self.n:
            self.set_result(None)

    def __call__(self):
        pass


def wait(coro_list, loop=_def_event_loop):

    w = Wait(len(coro_list))

    for c in coro_list:
        t = async(c)
        t.add_done_callback(lambda val: w._done())
        loop.call_soon(t)

    return w


def sleep(secs):
    t = time.time()
    log.debug("Started sleep at: %s, targetting: %s", t, t + secs)
    while time.time() < t + secs:
        time.sleep(0.01)
        yield
    log.debug("Finished sleeping %ss", secs)
