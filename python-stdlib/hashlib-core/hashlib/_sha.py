# MIT license; Copyright (c) 2023 Jim Mussared
# Originally ported from CPython by Paul Sokolovsky


# Base class for SHA implementations, which must provide:
#   .digestsize & .digest_size
#   .block_size
#   ._iv
#   ._update
#   ._final
class sha:
    def __init__(self, s=None):
        self._digest = self._iv[:]
        self._count_lo = 0
        self._count_hi = 0
        self._data = bytearray(self.block_size)
        self._local = 0
        self._digestsize = self.digest_size
        if s:
            self.update(s)

    def update(self, s):
        if isinstance(s, str):
            s = s.encode("ascii")
        else:
            s = bytes(s)
        self._update(s)

    def digest(self):
        return self.copy()._final()[: self._digestsize]

    def hexdigest(self):
        return "".join(["%.2x" % i for i in self.digest()])

    def copy(self):
        new = type(self)()
        new._digest = self._digest[:]
        new._count_lo = self._count_lo
        new._count_hi = self._count_hi
        new._data = self._data[:]
        new._local = self._local
        return new
