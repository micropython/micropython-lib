import io

from micropython import RingIO, const

try:
    from typing import Union, Tuple
except:
    pass

# From micropython/py/stream.h
_MP_STREAM_ERROR = const(-1)
_MP_STREAM_FLUSH = const(1)
_MP_STREAM_SEEK = const(2)
_MP_STREAM_POLL = const(3)
_MP_STREAM_CLOSE = const(4)
_MP_STREAM_POLL_RD = const(0x0001)


def streampair(buffer_size: Union[int, Tuple[int, int]]=256):
    """
    Returns two bi-directional linked stream objects where writes to one can be read from the other and vice/versa.
    This can be used somewhat similarly to a socket.socketpair in python, like a pipe
    of data that can be used to connect stream consumers (eg. asyncio.StreamWriter, mock Uart)
    """
    try:
        size_a, size_b = buffer_size
    except TypeError:
        size_a = size_b = buffer_size

    a = RingIO(size_a)
    b = RingIO(size_b)
    return StreamPair(a, b), StreamPair(b, a)


class StreamPair(io.IOBase):

    def __init__(self, own: RingIO, other: RingIO):
        self.own = own
        self.other = other
        super().__init__()

    def read(self, nbytes=-1):
        return self.own.read(nbytes)

    def readline(self):
        return self.own.readline()

    def readinto(self, buf, limit=-1):
        return self.own.readinto(buf, limit)

    def write(self, data):
        return self.other.write(data)

    def seek(self, offset, whence):
        return self.own.seek(offset, whence)

    def flush(self):
        self.own.flush()
        self.other.flush()

    def close(self):
        self.own.close()
        self.other.close()

    def any(self):
        return self.own.any()

    def ioctl(self, op, arg):
        if op == _MP_STREAM_POLL:
            if self.any():
                return _MP_STREAM_POLL_RD
            return 0

        elif op ==_MP_STREAM_FLUSH:
            return self.flush()
        elif op ==_MP_STREAM_SEEK:
            return self.seek(arg[0], arg[1])
        elif op ==_MP_STREAM_CLOSE:
            return self.close()

        else:
            return _MP_STREAM_ERROR
