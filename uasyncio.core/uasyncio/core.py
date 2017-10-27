import utime as time
import utimeq


type_gen = type((lambda: (yield))())

DEBUG = 0
log = None

def set_debug(val):
    global DEBUG, log
    DEBUG = val
    if val:
        import logging
        log = logging.getLogger("uasyncio.core")


class EventLoop:

    def __init__(self, len=42):
        self.q = utimeq.utimeq(len)

    def time(self):
        return time.ticks_ms()

    def create_task(self, coro):
        # CPython 3.4.2
        self.call_later_ms(0, coro)
        # CPython asyncio incompatibility: we don't return Task object

    def call_soon(self, callback, *args):
        self.call_at_(self.time(), callback, args)

    def call_later(self, delay, callback, *args):
        self.call_at_(time.ticks_add(self.time(), int(delay * 1000)), callback, args)

    def call_later_ms(self, delay, callback, *args):
        self.call_at_(time.ticks_add(self.time(), delay), callback, args)

    def call_at_(self, time, callback, args=()):
        if __debug__ and DEBUG:
            log.debug("Scheduling %s", (time, callback, args))
        self.q.push(time, callback, args)

    def wait(self, delay):
        # Default wait implementation, to be overriden in subclasses
        # with IO scheduling
        if __debug__ and DEBUG:
            log.debug("Sleeping for: %s", delay)
        time.sleep_ms(delay)

    def run_forever(self):
        cur_task = [0, 0, 0]
        while True:
            if self.q:
                # wait() may finish prematurely due to I/O completion,
                # and schedule new, earlier than before tasks to run.
                while 1:
                    t = self.q.peektime()
                    tnow = self.time()
                    delay = time.ticks_diff(t, tnow)
                    if delay < 0:
                        delay = 0
                    # Always call wait(), to give a chance to I/O scheduling
                    self.wait(delay)
                    if delay == 0:
                        break

                self.q.pop(cur_task)
                t = cur_task[0]
                cb = cur_task[1]
                args = cur_task[2]
                if __debug__ and DEBUG:
                    log.debug("Next coroutine to run: %s", (t, cb, args))
#                __main__.mem_info()
            else:
                self.wait(-1)
                # Assuming IO completion scheduled some tasks
                continue
            if callable(cb):
                cb(*args)
            else:
                delay = 0
                try:
                    if __debug__ and DEBUG:
                        log.debug("Coroutine %s send args: %s", cb, args)
                    if args == ():
                        ret = next(cb)
                    else:
                        ret = cb.send(*args)
                    if __debug__ and DEBUG:
                        log.debug("Coroutine %s yield result: %s", cb, ret)
                    if isinstance(ret, SysCall1):
                        arg = ret.arg
                        if isinstance(ret, SleepMs):
                            delay = arg
                        elif isinstance(ret, IORead):
                            self.add_reader(arg, cb)
                            continue
                        elif isinstance(ret, IOWrite):
                            self.add_writer(arg, cb)
                            continue
                        elif isinstance(ret, IOReadDone):
                            self.remove_reader(arg)
                        elif isinstance(ret, IOWriteDone):
                            self.remove_writer(arg)
                        elif isinstance(ret, StopLoop):
                            return arg
                        else:
                            assert False, "Unknown syscall yielded: %r (of type %r)" % (ret, type(ret))
                    elif isinstance(ret, type_gen):
                        self.call_soon(ret)
                    elif isinstance(ret, int):
                        # Delay
                        delay = ret
                    elif ret is None:
                        # Just reschedule
                        pass
                    elif ret is False:
                        # Don't reschedule
                        continue
                    else:
                        assert False, "Unsupported coroutine yield value: %r (of type %r)" % (ret, type(ret))
                except StopIteration as e:
                    if __debug__ and DEBUG:
                        log.debug("Coroutine finished: %s", cb)
                    continue
                # Currently all syscalls don't return anything, so we don't
                # need to feed anything to the next invocation of coroutine.
                # If that changes, need to pass that value below.
                self.call_later_ms(delay, cb)

    def run_until_complete(self, coro):
        def _run_and_stop():
            yield from coro
            yield StopLoop(0)
        self.call_soon(_run_and_stop())
        self.run_forever()

    def stop(self):
        self.call_soon((lambda: (yield StopLoop(0)))())

    def close(self):
        pass


class SysCall:

    def __init__(self, *args):
        self.args = args

    def handle(self):
        raise NotImplementedError

# Optimized syscall with 1 arg
class SysCall1(SysCall):

    def __init__(self, arg):
        self.arg = arg

class StopLoop(SysCall1):
    pass

class IORead(SysCall1):
    pass

class IOWrite(SysCall1):
    pass

class IOReadDone(SysCall1):
    pass

class IOWriteDone(SysCall1):
    pass


_event_loop = None
_event_loop_class = EventLoop
def get_event_loop(len=42):
    global _event_loop
    if _event_loop is None:
        _event_loop = _event_loop_class(len)
    return _event_loop

def sleep(secs):
    yield int(secs * 1000)

# Implementation of sleep_ms awaitable with zero heap memory usage
class SleepMs(SysCall1):

    def __init__(self):
        self.v = None
        self.arg = None

    def __call__(self, arg):
        self.v = arg
        #print("__call__")
        return self

    def __iter__(self):
        #print("__iter__")
        return self

    def __next__(self):
        if self.v is not None:
            #print("__next__ syscall enter")
            self.arg = self.v
            self.v = None
            return self
        #print("__next__ syscall exit")
        _stop_iter.__traceback__ = None
        raise _stop_iter

_stop_iter = StopIteration()
sleep_ms = SleepMs()


def coroutine(f):
    return f

#
# The functions below are deprecated in uasyncio, and provided only
# for compatibility with CPython asyncio
#

def ensure_future(coro, loop=_event_loop):
    _event_loop.call_soon(coro)
    # CPython asyncio incompatibility: we don't return Task object
    return coro


# CPython asyncio incompatibility: Task is a function, not a class (for efficiency)
def Task(coro, loop=_event_loop):
    # Same as async()
    _event_loop.call_soon(coro)
