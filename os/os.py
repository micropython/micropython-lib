import ffi


libc = ffi.open("libc.so.6")

errno = libc.var("i", "errno")
mkdir_ = libc.func("i", "mkdir", "si")
read_ = libc.func("i", "read", "ipi")
write_ = libc.func("i", "write", "iPi")


def check_error(ret):
    if ret == -1:
        raise OSError(errno.get())


def mkdir(name, mode=0o777):
    e = mkdir_(name, mode)
    check_error(e)

def read(fd, n):
    buf = bytearray(n)
    r = read_(fd, buf, n)
    check_error(r)
    return buf[:r]

def write(fd, buf):
    r = write_(fd, buf, len(buf))
    check_error(r)
    return r
