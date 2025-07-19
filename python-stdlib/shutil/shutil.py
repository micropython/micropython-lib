# Reimplement, because CPython3.3 impl is rather bloated
import os
from collections import namedtuple

_ntuple_diskusage = namedtuple("usage", ("total", "used", "free"))


def rmtree(d):
    if not d:
        raise ValueError

    for name, type, *_ in os.ilistdir(d):
        path = d + "/" + name
        if type & 0x4000:  # dir
            rmtree(path)
        else:  # file
            os.unlink(path)
    os.rmdir(d)


def copyfileobj(src, dest, length=512):
    if hasattr(src, "readinto"):
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
    else:
        while True:
            buf = src.read(length)
            if not buf:
                break
            dest.write(buf)


def disk_usage(path):
    bit_tuple = os.statvfs(path)
    blksize = bit_tuple[0]  # system block size
    total = bit_tuple[2] * blksize
    free = bit_tuple[3] * blksize
    used = total - free

    return _ntuple_diskusage(total, used, free)
