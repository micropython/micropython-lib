import asyncio
import unittest
import select
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

    def test_select_poll_compatibility(self):
        """Test that streampair works with select.poll()"""
        a, b = streampair()

        # Register stream with poll
        poller = select.poll()
        poller.register(a, select.POLLIN)

        # No data available initially
        events = poller.poll(0)
        assert len(events) == 0, f"Expected no events, got {events}"

        # Write data to b, should be readable from a
        b.write(b"test data")

        # Should now poll as readable
        events = poller.poll(0)
        assert len(events) == 1, f"Expected 1 event, got {events}"
        assert events[0][0] == a, "Event should be for stream a"
        assert events[0][1] & select.POLLIN, "Should be readable"

        # Read the data
        data = a.read()
        assert data == b"test data", f"Expected b'test data', got {data}"

        # Should no longer poll as readable
        events = poller.poll(0)
        assert len(events) == 0, f"Expected no events after read, got {events}"

        poller.unregister(a)

    @async_test
    async def test_streamreader_direct_usage(self):
        """Test that streampair can be used directly with asyncio.StreamReader"""
        a, b = streampair()

        # Create StreamReader directly on the streampair object
        reader = asyncio.StreamReader(a)

        # Write data in background task
        async def write_delayed():
            await asyncio.sleep_ms(10)
            b.write(b"async test\n")

        task = asyncio.create_task(write_delayed())

        # Should be able to read via StreamReader
        data = await asyncio.wait_for(reader.readline(), 1.0)
        assert data == b"async test\n", f"Expected b'async test\\n', got {data}"

        # Wait for background task to complete
        await task


if __name__ == "__main__":
    unittest.main()
