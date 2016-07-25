"""HMAC (Keyed-Hashing for Message Authentication) MicroPython module.

Implements the HMAC algorithm as described by RFC 2104.
"""

#import warnings as _warnings
#from _operator import _compare_digest as compare_digest
#import hashlib as _hashlib
#PendingDeprecationWarning = None
#RuntimeWarning = None
import uhashlib as _hashlib

trans_5C = bytes((x ^ 0x5C) for x in range(256))
trans_36 = bytes((x ^ 0x36) for x in range(256))

def translate(d, t):
    # Using bytes with a throw away array instead of char below
    # to avoid ending up with the wrong key when a key in the
    # form of b'\xAA' is used.
    return b''.join([bytes([t[x]]) for x in d])

# The size of the digests returned by HMAC depends on the underlying
# hashing module used.  Use digest_size from the instance of HMAC instead.
digest_size = None



class HMAC:
    """RFC 2104 HMAC class.  Also complies with RFC 4231.

    This supports the API for Cryptographic Hash Functions (PEP 247).
    """
    blocksize = 64  # 512-bit HMAC; Both sha1 and sha256 have a 512 bits blocksize.

    def __init__(self, key, msg=None, digestmod=None):
        """Create a new HMAC object.

        key:       key for the keyed hash object.
        msg:       Initial input for the hash, if provided.
        digestmod: A module supporting PEP 247,  *OR*
                   A hash name suitable for hashlib.new()  *OR*
                   A hashlib constructor returning a new hash object.
                   Defaults to uhashlib.sha256.

        Note: key and msg must be a bytes or bytearray objects.
        """

        self.finished = False
        self.digest_bytes = None
        self.hex_bytes = None

        if not isinstance(key, (bytes, bytearray)):
            raise TypeError("key: expected bytes or bytearray, but got %r" % type(key).__name__)

        if digestmod is None:
            #_warnings.warn("HMAC() without an explicit digestmod argument "
            #               "is deprecated.", PendingDeprecationWarning, 2)
            #digestmod = _hashlib.md5
            digestmod = _hashlib.sha256

        if callable(digestmod):
            self.digest_cons = digestmod
        elif isinstance(digestmod, str):
            self.digest_cons = lambda d=b'': getattr(_hashlib, digestmod)(d)
        elif isinstance(digestmod, (bytes, bytearray)):
            self.digest_cons = lambda d=b'': getattr(_hashlib, str(digestmod)[2:-1:])(d)
        else:
            self.digest_cons = lambda d=b'': digestmod.new(d)

        self.outer = self.digest_cons()
        self.inner = self.digest_cons()
        #self.digest_size = self.inner.digest_size

        #if hasattr(self.inner, 'block_size'):
        #    blocksize = self.inner.block_size
        #    if blocksize < 16:
        #        _warnings.warn('block_size of %d seems too small; using our '
        #                       'default of %d.' % (blocksize, self.blocksize),
        #                       RuntimeWarning, 2)
        #        blocksize = self.blocksize


        if str(self.inner) == '<sha1>':
            self.digest_size = 20
        elif str(self.inner) == '<sha256>':
            self.digest_size = 32
        else:
            #_warnings.warn('No block_size attribute on given digest object; '
            #               'Assuming %d.' % (self.blocksize),
            #               RuntimeWarning, 2)
            #blocksize = self.blocksize

            # uhashlib doesn't provide a digest_size and we only have hardcoded
            # values for the two uhashlib hash functions.
            self.digest_size = None

        # Both uhashlib supported algorithms have the same blocksize.
        blocksize = self.blocksize

        # self.blocksize is the default blocksize. self.block_size is
        # effective block size as well as the public API attribute.
        self.block_size = blocksize

        if len(key) > blocksize:
            key = self.digest_cons(key).digest()

        key = key + bytes(blocksize - len(key))
        self.outer.update(translate(key, trans_5C))
        self.inner.update(translate(key, trans_36))
        if msg is not None:
            self.update(msg)

    @property
    def name(self):
        return "hmac-" + str(self.inner)[1:-1:]

    def update(self, msg):
        """Update this hashing object with the string msg.
        """
        if not self.finished:
            self.inner.update(msg)
        else:
            # MicroPython's uhashlib sha1 and sha256 don't support the
            # copy method (yet) so not being able to update after a
            # digest is generated is a limitation.
            raise ValueError('Currently, a digest can only be generated once. '
                             'This object is now "spent" and cannot be updated.')
    #def copy(self):
    #    """Return a separate copy of this hashing object.
    #    An update to this copy won't affect the original object.
    #    """
        # Call __new__ directly to avoid the expensive __init__.
    #    other = self.__class__.__new__(self.__class__)
    #    other.digest_cons = self.digest_cons
    #    other.digest_size = self.digest_size
    #    other.inner = self.inner.copy()
    #    other.outer = self.outer.copy()
    #    return other

    def _current(self):
        """Return a hash object for the current state.

        To be used only internally with digest() and hexdigest().
        """
        #h = self.outer.copy()
        #h.update(self.inner.digest())
        #return h
        self.outer.update(self.inner.digest())
        return self.outer

    def digest(self):
        """Return the hash value of this hashing object.

        This returns a string containing 8-bit data. You cannot continue
        updating the object after calling this function.
        """
        #h = self._current()
        #return h.digest()
        if not self.finished:
            h = self._current()
            self.digest_bytes = h.digest()
            import ubinascii
            self.hex_bytes = ubinascii.hexlify(self.digest_bytes)
            del(ubinascii)
            self.finished = True
        return self.digest_bytes

    def hexdigest(self):
        """Like digest(), but returns a string of hexadecimal digits instead.
        """
        #h = self._current()
        #return h.hexdigest()
        if not self.finished:
            h = self._current()
            self.digest_bytes = h.digest()
            import ubinascii
            self.hex_bytes = ubinascii.hexlify(self.digest_bytes)
            del(ubinascii)
            self.finished = True
        return self.hex_bytes

def new(key, msg=None, digestmod=None):
    """Create a new hashing object and return it.

    key: The starting key for the hash.
    msg: if available, will immediately be hashed into the object's starting
    state.

    You can now feed arbitrary strings into the object using its update()
    method, and can ask for the hash value only once by calling its digest()
    method.
    """
    return HMAC(key, msg, digestmod)

def compare_digest(a, b, double_hmac=True, digestmod=b'sha256'):
    """Test two digests for equality in a more secure way than "==".

    This employs two main defenses, a double HMAC with a nonce (if available)
    to blind the timing side channel (to only leak unpredictable information
    to the side channel) and a constant time comparison.
    https://paragonie.com/blog/2015/11/preventing-timing-attacks-on-string-comparison-with-double-hmac-strategy

    The comparison is designed to run in constant time to
    avoid leaking information through the timing side channel.
    The constant time nature of this algorithm could be undermined by current
    or future MicroPython optimizations which is why it is (by default)
    additionally protected by the double HMAC.

    It takes as input the output of digest() or hexdigest() of two
    different HMAC objects, or bytes or a bytearray representing a
    precalculated digest.
    """
    if not isinstance(a, (bytes, bytearray)) or not isinstance(b, (bytes, bytearray)):
        raise TypeError("Expected bytes or bytearray, but got {} and {}".format(type(a).__name__, type(b).__name__))

    if len(a) != len(b):
        raise ValueError("This method is only for comparing digests of equal length")

    if double_hmac:
        try:
            import uos
            nonce = uos.urandom(64)
        except ImportError:
            double_hmac = False
        except AttributeError:
            double_hmac = False

    if double_hmac:
        a = new(nonce, a, digestmod).digest()
        b = new(nonce, b, digestmod).digest()

    result = 0
    for index, byte_value in enumerate(a):
        result |= byte_value ^ b[index]
    return result == 0

def test():
    """Test suite for the HMAC module"""
    run_tests = False
    try:
        from test_hmac import test_sha_vectors, test_sha256_rfc4231, test_compare_digest
        run_tests = True
    except ImportError:
        raise AssertionError('test_hmac not found, skipping all tests.')

    if run_tests:
        test_sha_vectors()
        test_sha256_rfc4231()
        test_compare_digest()
