import ffi
import array


libc = ffi.open("libc.so.6")

errno = libc.var("i", "errno")
mkdir_ = libc.func("i", "mkdir", "si")
read_ = libc.func("i", "read", "ipi")
write_ = libc.func("i", "write", "iPi")
close_ = libc.func("i", "close", "i")
fork_ = libc.func("i", "fork", "")
pipe_ = libc.func("i", "pipe", "p")
_exit_ = libc.func("v", "_exit", "i")


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

def close(fd):
    r = close_(fd)
    check_error(r)
    return r


def fork():
    r = fork_()
    check_error(r)
    return r

def pipe():
    a = array.array('i', [0, 0])
    r = pipe_(a)
    check_error(r)
    return a[0], a[1]

def _exit(n):
    _exit_(n)
