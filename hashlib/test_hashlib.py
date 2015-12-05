from hashlib._sha256 import test as sha256_test
from hashlib._sha512 import test as sha512_test
import hashlib

hashlib.sha224()
hashlib.sha256()
hashlib.sha384()
hashlib.sha512()

sha256_test()
sha512_test()

print("OK")
