from utime import *
from utime import ticks_ms, ticks_diff


class Monotonic:
    """
    MicroPython replacement for time.monotonic suitable for timeouts & comparisons.
    """

    # CPython time.monotonic() → float returns the value (in fractional seconds) of a monotonic clock,
    # i.e. a clock that cannot go backwards. The clock is not affected by system clock updates.
    # The reference point of the returned value is undefined, so that only the difference between the
    # results of two calls is valid.

    # Most micropython ports have single-precision float for size / efficiency reasons, and some do not have
    # float support at all in hardware (so are very slow).
    # To support measurements of difference between two time points, time.ticks_ms() and time.ticks.diff()
    # are generally recommended, however this can complicate efforts to port existing libraries using
    # time.monotonic.

    # This library is intended to support being used as a drop-in replacement for many/most use cases of
    # time.monotonic. It will wrap the ticks functions and handle/hide the 32-bit rollover handling.

    # Note however if you convert the output of monotonic to int or float, eg `float(monotonic())` then
    # comparisions between these value are not always valid becasuse they will wrap around back to zero
    # after a certain length of time. In other words, always do comparisons against the object returned
    # by monotonic() without type conversion.

    # See the test_monotonic.py unit test for examples of usage.

    def __init__(self, val_ms) -> None:
        self.val_ms = val_ms

    def __int__(self):
        return int(self.val_ms // 1000)

    def __float__(self):
        return float(self.val_ms) / 1000.0

    def __repr__(self):
        return str(self.__float__())

    @staticmethod
    def _convert(other):
        if isinstance(other, Monotonic):
            return other.val_ms
        elif isinstance(other, float):
            return int(round(other * 1000))
        else:
            return int(other * 1000)

    def __add__(self, other):
        return Monotonic(self.val_ms + self._convert(other))

    def __sub__(self, other):
        """Returns relative difference in time in seconds"""
        return float(ticks_diff(self.val_ms, self._convert(other))) / 1000.0

    def __gt__(self, other):
        return self.__sub__(other) > 0

    def __lt__(self, other):
        return self.__sub__(other) < 0


def monotonic():
    return Monotonic(ticks_ms())
