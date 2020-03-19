# Test that coros scheduled to run at some time don't run prematurely
# in case of I/O completion before that.
import uasyncio.core as uasyncio
import logging
logging.basicConfig(level=logging.DEBUG)
#uasyncio.set_debug(True)


class MockEventLoop(uasyncio.EventLoop):

    def __init__(self):
        super().__init__()
        self.t = 0
        self.msgs = []

    def time(self):
        return self.t

    def pass_time(self, delta):
        self.t += delta

    def wait(self, delay):
        #print("%d: wait(%d)" % (self.t, delay))
        self.pass_time(100)

        if self.t == 100:
            def cb_1st():
                self.msgs.append("I should be run first, time: %s" % self.time())
            self.call_soon(cb_1st)

        if self.t == 1000:
            raise StopIteration


loop = MockEventLoop()

def cb_2nd():
    loop.msgs.append("I should be run second, time: %s" % loop.time())

loop.call_later_ms(500, cb_2nd)

try:
    loop.run_forever()
except StopIteration:
    pass

print(loop.msgs)
# .wait() is now called on each loop iteration, and for our mock case, it means that
# at the time of running, self.time() will be skewed by 100 virtual time units.
assert loop.msgs == ['I should be run first, time: 100', 'I should be run second, time: 500'], str(loop.msgs)
