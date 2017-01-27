from uasyncio import StreamReader

class MockSock:

    def __init__(self, data_list):
        self.data = data_list

    def read(self, sz):
        try:
            return self.data.pop(0)
        except IndexError:
            return b""


mock = MockSock([
    b"123",
    b"234", b"5",
    b"a", b"b", b"c", b"d", b"e",
])


def func():
    sr = StreamReader(mock)
    assert await sr.readexactly(3) == b"123"
    assert await sr.readexactly(4) == b"2345"
    assert await sr.readexactly(5) == b"abcde"
    # This isn't how it should be, but the current behavior
    assert await sr.readexactly(10) == b""

for i in func():
    pass
