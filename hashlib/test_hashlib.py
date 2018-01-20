from hashlib.sha256 import test as sha256_test
from hashlib.sha512 import test as sha512_test


sha256_test()
sha512_test()

from hashlib import new
from hashlib.sha256 import sha256 as pure_sha256

assert new('sha256', 'abc').digest() == pure_sha256('abc').digest() \
            == b'\xbax\x16\xbf\x8f\x01\xcf\xeaAA@\xde]\xae"#\xb0\x03a\xa3\x96\x17z\x9c\xb4\x10\xffa\xf2\x00\x15\xad'

assert hasattr(new('sha512'), 'digest')
assert hasattr(new('sha256'), 'digest')
assert hasattr(new('sha224'), 'digest')
assert hasattr(new('sha384'), 'digest')

print("OK")
