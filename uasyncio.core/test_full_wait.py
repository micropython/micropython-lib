# Test that coros scheduled to run at some time don't run prematurely
# in case of I/O completion before that.
import uasyncio.core as uasyncio

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
        self.pass_time(100)
        if self.t == 100:
            self.call_soon(lambda: self.msgs.append("I should be run first, time: %s" % self.time()))
        if self.t == 1000:
            raise StopIteration


loop = MockEventLoop()
loop.call_later_ms_(500, lambda: loop.msgs.append("I should be run second, time: %s" % loop.time()))
try:
    loop.run_forever()
except StopIteration:
    pass

print(loop.msgs)
assert loop.msgs == ['I should be run first, time: 100', 'I should be run second, time: 500']
