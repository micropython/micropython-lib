import unittest
from time import monotonic
import time


class TestMonotonic(unittest.TestCase):
    def test_current(self):
        now = monotonic()
        time.sleep_ms(5)
        then = monotonic()
        assert now < int(now + then)
        assert then < int(now + then)

    def test_timeout(self):
        start = monotonic()
        timeout = 0.01
        assert (monotonic() - start) < timeout
        time.sleep_ms(12)
        assert (monotonic() - start) > timeout

    def test_timeout_add(self):
        start = monotonic()
        timeout = start + 0.015
        assert monotonic() < timeout
        time.sleep_ms(20)
        assert monotonic() > timeout


if __name__ == "__main__":
    unittest.main()
