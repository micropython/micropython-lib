import uasyncio
import unittest
from ucontextlib._async import asynccontextmanager


class AsyncContextManagerTestCase(unittest.TestCase):
    def setUp(self):
        self._history = []

        @asynccontextmanager
        async def manager(x):
            self._history.append("start")
            try:
                await uasyncio.sleep_ms(0)
                yield x
            finally:
                self._history.append("finish")

        self._manager = manager

    def test_context_manager(self):
        async def _test():
            async with self._manager(123) as x:
                self.assertEqual(x, 123)
            self.assertEqual(self._history, ["start", "finish"])

        uasyncio.run_until_complete(_test())

    def test_context_manager_on_error(self):
        async def _test():
            exc = Exception()
            try:
                async with self._manager(123) as x:
                    raise exc
            except Exception as e:
                self.assertEqual(exc, e)
            self.assertEqual(self._history, ["start", "finish"])

        uasyncio.run_until_complete(_test())


if __name__ == "__main__":
    unittest.main()
