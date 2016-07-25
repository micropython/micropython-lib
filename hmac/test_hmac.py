""" Tests for the MicroPython HMAC module """
from hmac import HMAC, new, compare_digest
import uhashlib as _hashlib

# This is the failUnlessEqual method from unittest.TestCase
def assertEqual(first, second): 
    """Fail if the two objects are unequal as determined by the '==' 
    operator. 
    """ 
    if not first == second: 
        raise AssertionError('%r != %r' % (first, second))

# Using the tests from 
# https://github.com/python/cpython/blob/3.5/Lib/test/test_hmac.py
# with as few changes as possible to ensure correctness and parity with 
# Python stdlib version.
def test_sha_vectors():
    def shatest(key, data, digest):
        h = HMAC(key, data, digestmod=_hashlib.sha1)
        assertEqual(h.hexdigest().upper(), digest.upper())
        assertEqual(h.name, "hmac-sha1")
        assertEqual(h.digest_size, 20)
        assertEqual(h.block_size, 64)

        h = HMAC(key, data, digestmod='sha1')
        assertEqual(h.hexdigest().upper(), digest.upper())
        assertEqual(h.name, "hmac-sha1")
        assertEqual(h.digest_size, 20)
        assertEqual(h.block_size, 64)


    shatest(b"\x0b" * 20,
            b"Hi There",
            b"b617318655057264e28bc0b6fb378c8ef146be00")

    shatest(b"Jefe",
            b"what do ya want for nothing?",
            b"effcdf6ae5eb2fa2d27416d5f184df9c259a7c79")

    shatest(b"\xAA" * 20,
            b"\xDD" * 50,
            b"125d7342b9ac11cd91a39af48aa17b4f63f175d3")

    shatest(bytes(range(1, 26)),
            b"\xCD" * 50,
            b"4c9007f4026250c6bc8414f9bf50c86c2d7235da")

    shatest(b"\x0C" * 20,
            b"Test With Truncation",
            b"4c1a03424b55e07fe7f27be1d58bb9324a9a5a04")

    shatest(b"\xAA" * 80,
            b"Test Using Larger Than Block-Size Key - Hash Key First",
            b"aa4ae5e15272d00e95705637ce8a3b55ed402112")

    shatest(b"\xAA" * 80,
            (b"Test Using Larger Than Block-Size Key "
             b"and Larger Than One Block-Size Data"),
             b"e8e99d0f45237d786d6bbaa7965c7808bbff1a91")

def _rfc4231_test_cases(hashfunc, hash_name, digest_size, block_size):
    def hmactest(key, data, hexdigests):
        hmac_name = "hmac-" + hash_name
        h = HMAC(key, data, digestmod=hashfunc)
        assertEqual(h.hexdigest().lower(), hexdigests[hashfunc])
        assertEqual(h.name, hmac_name)
        assertEqual(h.digest_size, digest_size)
        assertEqual(h.block_size, block_size)

        h = HMAC(key, data, digestmod=hash_name)
        assertEqual(h.hexdigest().lower(), hexdigests[hashfunc])
        assertEqual(h.name, hmac_name)
        assertEqual(h.digest_size, digest_size)
        assertEqual(h.block_size, block_size)

    hmactest(key = b'\x0b'*20,
             data = b'Hi There',
             hexdigests = {
               _hashlib.sha256: b'b0344c61d8db38535ca8afceaf0bf12b'
                               b'881dc200c9833da726e9376c2e32cff7'
             })

    hmactest(key = b'Jefe',
             data = b'what do ya want for nothing?',
             hexdigests = {
               _hashlib.sha256: b'5bdcc146bf60754e6a042426089575c7'
                               b'5a003f089d2739839dec58b964ec3843'
             })

    hmactest(key = b'\xaa'*20,
             data = b'\xdd'*50,
             hexdigests = {
               _hashlib.sha256: b'773ea91e36800e46854db8ebd09181a7'
                               b'2959098b3ef8c122d9635514ced565fe'
             })

    hmactest(key = bytes(x for x in range(0x01, 0x19+1)),
             data = b'\xcd'*50,
             hexdigests = {
               _hashlib.sha256: b'82558a389a443c0ea4cc819899f2083a'
                               b'85f0faa3e578f8077a2e3ff46729665b'
             })

    hmactest(key = b'\xaa'*131,
             data = b'Test Using Larger Than Block-Siz'
                    b'e Key - Hash Key First',
             hexdigests = {
               _hashlib.sha256: b'60e431591ee0b67f0d8a26aacbf5b77f'
                               b'8e0bc6213728c5140546040f0ee37f54'
             })

    hmactest(key = b'\xaa'*131,
             data = b'This is a test using a larger th'
                    b'an block-size key and a larger t'
                    b'han block-size data. The key nee'
                    b'ds to be hashed before being use'
                    b'd by the HMAC algorithm.',
             hexdigests = {
               _hashlib.sha256: b'9b09ffa71b942fcb27635fbcd5b0e944'
                               b'bfdc63644f0713938a7f51535c3a35e2'
             })


def test_sha256_rfc4231():
    _rfc4231_test_cases(_hashlib.sha256, 'sha256', 32, 64)

def test_compare_digest():
    h = new(b'key', b'message', 'sha256')
    i = new(b'key', b'message', 'sha256')
    j = new(b'key', b'not the message', 'sha256')
    digest = b"n\x9e\xf2\x9bu\xff\xfc[z\xba\xe5'\xd5\x8f\xda\xdb/\xe4.r\x19\x01\x19v\x91sC\x06_X\xedJ"
    not_digest = b'\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa'
    hexdigest = b'6e9ef29b75fffc5b7abae527d58fdadb2fe42e7219011976917343065f58ed4a'
    not_hexdigest = b'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'

    # Positive Tests
    assertEqual(compare_digest(h.digest(), i.digest()), True)
    assertEqual(compare_digest(h.digest(), digest), True)
    assertEqual(compare_digest(h.hexdigest(), hexdigest), True)
    assertEqual(compare_digest(h.digest(), i.digest(), double_hmac=False), True)
    assertEqual(compare_digest(h.digest(), i.digest(), digestmod='sha1'), True)
    assertEqual(compare_digest(h.hexdigest(), i.hexdigest(), digestmod='sha1'), True)
    assertEqual(compare_digest(h.hexdigest(), hexdigest, digestmod='sha1'), True)
    assertEqual(compare_digest(h.digest(), i.digest(), digestmod='sha256'), True)
    assertEqual(compare_digest(h.digest(), i.digest(), digestmod=b'sha256'), True)
    assertEqual(compare_digest(h.hexdigest(), i.hexdigest(), digestmod='sha256'), True)
    assertEqual(compare_digest(h.digest(), digest, digestmod='sha256'), True)

    # Negative Tests
    assertEqual(compare_digest(h.digest(), j.digest()), False)
    assertEqual(compare_digest(h.digest(), not_digest), False)
    assertEqual(compare_digest(h.hexdigest(), not_hexdigest), False)
    assertEqual(compare_digest(h.digest(), j.digest(), double_hmac=False), False)
    assertEqual(compare_digest(h.digest(), j.digest(), digestmod='sha1'), False)
    assertEqual(compare_digest(h.hexdigest(), j.hexdigest(), digestmod='sha1'), False)
    assertEqual(compare_digest(h.hexdigest(), not_hexdigest, digestmod='sha1'), False)
    assertEqual(compare_digest(h.digest(), j.digest(), digestmod='sha256'), False)
    assertEqual(compare_digest(h.digest(), j.digest(), digestmod=b'sha256'), False)
    assertEqual(compare_digest(h.hexdigest(), j.hexdigest(), digestmod='sha256'), False)
    assertEqual(compare_digest(h.digest(), not_digest, digestmod='sha256'), False)
