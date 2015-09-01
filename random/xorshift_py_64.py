from sys import maxsize as _maxsize

assert _maxsize > 1<<60, "Using xorshift_py_64.py requires bigger native integers."

from under_random import UnderRandom
from xorshift import XorShift128

class XorShift_py64(XorShift128):

    # From https://en.wikipedia.org/wiki/Xorshift#Example_implementation
    # #include <stdint.h>
    #
    # /* These state variables must be initialized so that they are not all zero. */
    # uint32_t x, y, z, w;
    #
    # uint32_t xorshift128(void) {
    #         uint32_t t = x ^ (x << 11);
    #         x = y; y = z; z = w;
    #         return w = w ^ (w >> 19) ^ t ^ (t >> 8);
    #     }

    @staticmethod
    def _step(a):
        # a contains x, y, z, w, t
        a[4] = (a[0] ^ a[0] << 11) & 0xffffffff
        a[0] = a[1]
        a[1] = a[2]
        a[2] = a[3]
        a[3] = (a[3] ^ (a[3] >> 19) ^ a[4] ^ (a[4] >> 8)) & 0xffffffff
        return a[3] & 0x3fffffff # bottom 30 bits only

class Random(UnderRandom, XorShift_py64):
    pass

