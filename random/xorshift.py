from array import array
from uctypes import addressof, bytearray_at
from os import urandom as _urandom

class XorShift128():
    def __init__(self):
        self.sa = array('I', range(5)) # x, y, z, w, and t
        self.state = bytearray_at(addressof(self.sa), 4 * len(self.sa))
        self.seed()

    def getstate(self):
        return bytes(self.state)

    def setstate(self, state):
        for i in range(len(self.state)):
            self.state[i] = state[i]

    def seed(self, a=None):
        if a is None:
            a = _urandom(len(self.state))
        else:
            if isinstance(a, int):
                a = a.to_bytes(len(self.state))
            elif isinstance(a, str):
                a = a.encode()
        salt = b'G\xf1(\xbd\xb2\xcdxa\x0c\x17\xe2:q\xbc\xd9j\xe6\xc7kP'
        for i in range(len(self.state)):
            try:
                self.state[i] = a[i] ^ salt[i]
            except IndexError:
                # low entropy seed. Could warn.
                self.state[i] = salt[i]

    def getrandbytes(self, n):
        return b''.join(self._rand_4_bytes() for i in range(n//4 + 1))[:n]

    def _rand_4_bytes(self):
        self._step(self.sa)
        # FIXME: sensitive to endian-ness
        # FIXME: change order in self.sa so that W is first
        return bytes(self.state[12:16]) # The full 4 bytes of w

    def __iter__(self):
        return self

    def __next__(self):
        return self._step(self.sa)

    rng = __next__

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
        # Note this method should return only 30 bits, for the sake of the little platforms
        raise NotImplementedError('missing _step()') # Must provide in subclass
