import asyncio
import unittest
from streampair import streampair

def async_test(f):
    """
    Decorator to run an async test function
    """
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        # loop.set_exception_handler(_exception_handler)
        t = loop.create_task(f(*args, **kwargs))
        loop.run_until_complete(t)

    return wrapper

class StreamPairTestCase(unittest.TestCase):

    def test_streampair(self):
        a, b = streampair()
        assert a.write(b"foo") == 3
        assert b.write(b"bar") == 3

        assert (r := a.read()) == b"bar", r
        assert (r := b.read()) == b"foo", r

    @async_test
    async def test_async_streampair(self):
        a, b = streampair()
        ar = asyncio.StreamReader(a)
        bw = asyncio.StreamWriter(b)

        br = asyncio.StreamReader(b)
        aw = asyncio.StreamWriter(a)

        aw.write(b"foo\n")
        await aw.drain()
        assert not a.any()
        assert b.any()
        assert (r := await br.readline()) == b"foo\n", r
        assert not b.any()
        assert not a.any()

        bw.write(b"bar\n")
        await bw.drain()
        assert not b.any()
        assert a.any()
        assert (r := await ar.readline()) == b"bar\n", r
        assert not b.any()
        assert not a.any()


if __name__ == "__main__":
    unittest.main()
