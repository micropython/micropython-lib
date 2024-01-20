# Implements the hmac module from the Python standard library.


class HMAC:
    def __init__(self, key, msg=None, digestmod=None):
        if not isinstance(key, (bytes, bytearray)):
            raise TypeError("key: expected bytes/bytearray")

        import hashlib

        if digestmod is None:
            # TODO: Default hash algorithm is now deprecated.
            digestmod = hashlib.md5

        if callable(digestmod):
            # A hashlib constructor returning a new hash object.
            make_hash = digestmod  # A
        elif isinstance(digestmod, str):
            # A hash name suitable for hashlib.new().
            make_hash = lambda d=b"": getattr(hashlib, digestmod)(d)
        else:
            # A module supporting PEP 247.
            make_hash = digestmod.new  # C

        self._outer = make_hash()
        self._inner = make_hash()

        self.digest_size = getattr(self._inner, "digest_size", None)
        # If the provided hash doesn't support block_size (e.g. built-in
        # hashlib), 64 is the correct default for all built-in hash
        # functions (md5, sha1, sha256).
        self.block_size = getattr(self._inner, "block_size", 64)

        # Truncate to digest_size if greater than block_size.
        if len(key) > self.block_size:
            key = make_hash(key).digest()

        # Pad to block size.
        key = key + bytes(self.block_size - len(key))

        self._outer.update(bytes(x ^ 0x5C for x in key))
        self._inner.update(bytes(x ^ 0x36 for x in key))

        if msg is not None:
            self.update(msg)

    @property
    def name(self):
        return "hmac-" + getattr(self._inner, "name", type(self._inner).__name__)

    def update(self, msg):
        self._inner.update(msg)

    def copy(self):
        if not hasattr(self._inner, "copy"):
            # Not supported for built-in hash functions.
            raise NotImplementedError()
        # Call __new__ directly to avoid the expensive __init__.
        other = self.__class__.__new__(self.__class__)
        other.block_size = self.block_size
        other.digest_size = self.digest_size
        other._inner = self._inner.copy()
        other._outer = self._outer.copy()
        return other

    def _current(self):
        h = self._outer
        if hasattr(h, "copy"):
            # built-in hash functions don't support this, and as a result,
            # digest() will finalise the hmac and further calls to
            # update/digest will fail.
            h = h.copy()
        h.update(self._inner.digest())
        return h

    def digest(self):
        h = self._current()
        return h.digest()

    def hexdigest(self):
        import binascii

        return str(binascii.hexlify(self.digest()), "utf-8")


def new(key, msg=None, digestmod=None):
    return HMAC(key, msg, digestmod)
