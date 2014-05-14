import ffi
import array
import struct


libc = ffi.open("libc.so.6")

errno = libc.var("i", "errno")
mkdir_ = libc.func("i", "mkdir", "si")
opendir_ = libc.func("P", "opendir", "s")
readdir_ = libc.func("P", "readdir", "P")
read_ = libc.func("i", "read", "ipi")
write_ = libc.func("i", "write", "iPi")
close_ = libc.func("i", "close", "i")
access_ = libc.func("i", "access", "si")
fork_ = libc.func("i", "fork", "")
pipe_ = libc.func("i", "pipe", "p")
_exit_ = libc.func("v", "_exit", "i")
getpid_ = libc.func("i", "getpid", "")
waitpid_ = libc.func("i", "waitpid", "ipi")

R_OK = const(4)
W_OK = const(2)
X_OK = const(1)
F_OK = const(0)


def check_error(ret):
    if ret == -1:
        raise OSError(errno.get())


def mkdir(name, mode=0o777):
    e = mkdir_(name, mode)
    check_error(e)

def listdir(path="."):
    dir = opendir_(path)
    if not dir:
        check_error(e)
    res = []
    dirent_fmt = "iiHB256s"
    while True:
        dirent = readdir_(dir)
        if not dirent:
            break
        dirent = ffi.as_bytearray(dirent, struct.calcsize(dirent_fmt))
        dirent = struct.unpack(dirent_fmt, dirent)
        fname = str(dirent[4].split('\0', 1)[0], "ascii")
        if fname != "." and fname != "..":
            res.append(fname)
    return res

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

def access(path, mode):
    return access_(path, mode) == 0

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

def getpid():
    return getpid_()

def waitpid(pid, opts):
    a = array.array('i', [0])
    r = waitpid_(pid, a, opts)
    check_error(r)
    return (r, a[0])
