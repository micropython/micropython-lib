from sys import maxsize as _maxsize

# FIXME once https://github.com/micropython/micropython/issues/1448 is resolved
if _maxsize > 1<<40:
    BPF = 53        # Number of bits in a float
else:
    BPF = 24        # Number of bits in a 32-bit IEEE 754 float mantissa

RECIP_BPF = 2**-BPF
_BytesNeededPF = (BPF+7)//8
_DownshiftBits = 8 * _BytesNeededPF - BPF

class UnderRandom():

    def random(self):
        """Get the next random number in the range [0.0, 1.0)."""
        return (int.from_bytes(self.getrandbytes(_BytesNeededPF), 'little') \
                >> _DownshiftBits) * RECIP_BPF

    def getrandbits(self, k):
        """getrandbits(k) -> x.  Generates an int with k random bits."""
        if k <= 0:
            raise ValueError('number of bits must be greater than zero')
        if k != int(k):
            raise TypeError('number of bits should be an integer')
        numbytes = (k + 7) // 8                       # bits / 8 and rounded up
        # Can't do x = int.from_bytes(_urandom(numbytes), 'big')
        # since int.from_bytes() on pyboard is not implemented for big integers
        # so we do it manually. Note this is a big-endian conversion: earliest
        # byte is most significant.
        x = 0
        for b in self.getrandbytes(numbytes):
            x = (x << 8) + b
        return x >> (numbytes * 8 - k)                # trim excess bits
