from uasyncio import StreamReader

class MockSock:

    def __init__(self, data_list):
        self.data = data_list

    def readline(self):
        try:
            return self.data.pop(0)
        except IndexError:
            return b""


mock = MockSock([
    b"line1\n",
    b"parts ", b"of ", b"line2\n",
    b"unterminated",
])


def func():
    sr = StreamReader(mock)
    assert await sr.readline() == b"line1\n"
    assert await sr.readline() == b"parts of line2\n"
    assert await sr.readline() == b"unterminated"
    assert await sr.readline() == b""

for i in func():
    pass
