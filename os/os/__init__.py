import ffi
import array
import struct
import errno
import stat as stat_
try:
    from _os import *
except:
    pass


libc = ffi.open("libc.so.6")

errno_ = libc.var("i", "errno")
mkdir_ = libc.func("i", "mkdir", "si")
unlink_ = libc.func("i", "unlink", "s")
rmdir_ = libc.func("i", "rmdir", "s")
getwd_ = libc.func("s", "getwd", "s")
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


error = OSError

def check_error(ret):
    if ret == -1:
        raise OSError(errno_.get())

def raise_error():
    raise OSError(errno_.get())


def getcwd():
    buf = bytearray(512)
    return getwd_(buf)

def mkdir(name, mode=0o777):
    e = mkdir_(name, mode)
    check_error(e)

def unlink(name):
    e = unlink_(name)
    check_error(e)

def rmdir(name):
    e = rmdir_(name)
    check_error(e)

def makedirs(name, mode=0o777, exist_ok=False):
    exists = access(name, F_OK)
    if exists:
        if exist_ok:
            return
        raise OSError(errno.EEXIST)
    s = ""
    for c in name.split("/"):
        s += c + "/"
        try:
            mkdir(s)
        except OSError as e:
            if e.args[0] != errno.EEXIST:
                raise

def ilistdir_ex(path="."):
    dir = opendir_(path)
    if not dir:
        raise_error()
    res = []
    dirent_fmt = "iiHB256s"
    while True:
        dirent = readdir_(dir)
        if not dirent:
            break
        dirent = ffi.as_bytearray(dirent, struct.calcsize(dirent_fmt))
        dirent = struct.unpack(dirent_fmt, dirent)
        yield dirent

def listdir(path="."):
    res = []
    for dirent in ilistdir_ex(path):
        fname = str(dirent[4].split('\0', 1)[0], "ascii")
        if fname != "." and fname != "..":
            res.append(fname)
    return res

def walk(top, topdown=True):
    files = []
    dirs = []
    for dirent in ilistdir_ex(top):
        mode = dirent[3] << 12
        fname = str(dirent[4].split('\0', 1)[0], "ascii")
        if stat_.S_ISDIR(mode):
            if fname != "." and fname != "..":
                dirs.append(fname)
        else:
            files.append(fname)
    if topdown:
        yield top, dirs, files
    for d in dirs:
        yield from walk(top + "/" + d, topdown)
    if not topdown:
        yield top, dirs, files

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
