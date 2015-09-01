from under_random import UnderRandom

class Random(UnderRandom):
    def __init__(self):
        self.state = 7603603

    def _rng(self):
        # For these choice of numbers, see P L'Ecuyer,
        #"Tables of linear congruential generators of
        # different sizes and good lattice structure"
        rv = self.state = (self.state * 653276) % 8388593
        return rv

    def seed(self, a):
        if isinstance(a, str):
            a = a.encode()
        if isinstance(a, (bytes, bytearray)):
            a = int.from_bytes(a)
        self.state = a % 8388593

    def getstate(self):
        return self.state.to_bytes(4)

    def setstate(self, state):
        self.state = int.from_bytes(state)

    def getrandbytes(self, n):
        return bytes((self._rng() >> 5) & 0xff for i in range(n))
