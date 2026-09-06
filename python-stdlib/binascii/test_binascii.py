from binascii import *
import time

data = b"zlutoucky kun upel dabelske ody"
h = hexlify(data)

if h != b"7a6c75746f75636b79206b756e207570656c20646162656c736b65206f6479":
    raise Exception("Error")

data2 = unhexlify(h)

if data2 != data:
    raise Exception("Error")

s = b"Hello from MicroPython!\n\xff\x80\xa0\xcf"
b64 = (
    b"\n",
    b"SA==\n",
    b"SGU=\n",
    b"SGVs\n",
    b"SGVsbA==\n",
    b"SGVsbG8=\n",
    b"SGVsbG8g\n",
    b"SGVsbG8gZg==\n",
    b"SGVsbG8gZnI=\n",
    b"SGVsbG8gZnJv\n",
    b"SGVsbG8gZnJvbQ==\n",
    b"SGVsbG8gZnJvbSA=\n",
    b"SGVsbG8gZnJvbSBN\n",
    b"SGVsbG8gZnJvbSBNaQ==\n",
    b"SGVsbG8gZnJvbSBNaWM=\n",
    b"SGVsbG8gZnJvbSBNaWNy\n",
    b"SGVsbG8gZnJvbSBNaWNybw==\n",
    b"SGVsbG8gZnJvbSBNaWNyb1A=\n",
    b"SGVsbG8gZnJvbSBNaWNyb1B5\n",
    b"SGVsbG8gZnJvbSBNaWNyb1B5dA==\n",
    b"SGVsbG8gZnJvbSBNaWNyb1B5dGg=\n",
    b"SGVsbG8gZnJvbSBNaWNyb1B5dGhv\n",
    b"SGVsbG8gZnJvbSBNaWNyb1B5dGhvbg==\n",
    b"SGVsbG8gZnJvbSBNaWNyb1B5dGhvbiE=\n",
    b"SGVsbG8gZnJvbSBNaWNyb1B5dGhvbiEK\n",
    b"SGVsbG8gZnJvbSBNaWNyb1B5dGhvbiEK/w==\n",
    b"SGVsbG8gZnJvbSBNaWNyb1B5dGhvbiEK/4A=\n",
    b"SGVsbG8gZnJvbSBNaWNyb1B5dGhvbiEK/4Cg\n",
    b"SGVsbG8gZnJvbSBNaWNyb1B5dGhvbiEK/4Cgzw==\n",
)

for i in range(len(s) + 1):
    substr = s[:i]
    enc = b2a_base64(substr)
    assert enc == b64[i]
    dec = a2b_base64(enc)
    assert dec == substr

start = time.time()
for x in range(100000):
    d = unhexlify(h)

print("100000 iterations in: " + str(time.time() - start))

print("OK")
