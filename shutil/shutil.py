# Reimplement, because CPython3.3 impl is rather bloated
import os


def rmtree(top):
    for path, dirs, files in os.walk(top, False):
        for f in files:
            os.unlink(path + "/" + f)
        os.rmdir(path)

def copyfileobj(src, dest, length=512):
    buf = bytearray(length)
    while True:
        sz = src.readinto(buf)
        if not sz:
            break
        if sz == length:
            dest.write(buf)
        else:
            b = memoryview(buf)[:sz]
            dest.write(b)
