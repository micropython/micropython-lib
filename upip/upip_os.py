import ffi
import array
import struct
import upip_errno
import upip_stat as stat_
import upip__libc
try:
    from _os import *
except:
    pass


libc = upip__libc.get()

errno_ = libc.var("i", "errno")
chdir_ = libc.func("i", "chdir", "s")
mkdir_ = libc.func("i", "mkdir", "si")
rename_ = libc.func("i", "rename", "ss")
unlink_ = libc.func("i", "unlink", "s")
rmdir_ = libc.func("i", "rmdir", "s")
getcwd_ = libc.func("s", "getcwd", "si")
opendir_ = libc.func("P", "opendir", "s")
readdir_ = libc.func("P", "readdir", "P")
open_ = libc.func("i", "open", "sii")
read_ = libc.func("i", "read", "ipi")
write_ = libc.func("i", "write", "iPi")
close_ = libc.func("i", "close", "i")
access_ = libc.func("i", "access", "si")
fork_ = libc.func("i", "fork", "")
pipe_ = libc.func("i", "pipe", "p")
_exit_ = libc.func("v", "_exit", "i")
getpid_ = libc.func("i", "getpid", "")
waitpid_ = libc.func("i", "waitpid", "ipi")
system_ = libc.func("i", "system", "s")
getenv_ = libc.func("s", "getenv", "P")

R_OK = const(4)
W_OK = const(2)
X_OK = const(1)
F_OK = const(0)

O_ACCMODE  = 0o0000003
O_RDONLY   = 0o0000000
O_WRONLY   = 0o0000001
O_RDWR     = 0o0000002
O_CREAT    = 0o0000100
O_EXCL     = 0o0000200
O_NOCTTY   = 0o0000400
O_TRUNC    = 0o0001000
O_APPEND   = 0o0002000
O_NONBLOCK = 0o0004000

error = OSError
name = "posix"
sep = "/"
curdir = "."
pardir = ".."
environ = {"WARNING": "NOT_IMPLEMENTED"}


def check_error(ret):
    # Return True is error was EINTR (which usually means that OS call
    # should be restarted).
    if ret == -1:
        e = errno_.get()
        if e == upip_errno.EINTR:
            return True
        raise OSError(e)

def raise_error():
    raise OSError(errno_.get())


def getcwd():
    buf = bytearray(512)
    return getcwd_(buf, 512)

def mkdir(name, mode=0o777):
    e = mkdir_(name, mode)
    check_error(e)

def rename(old, new):
    e = rename_(old, new)
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
        raise OSError(upip_errno.EEXIST)
    s = ""
    for c in name.split("/"):
        s += c + "/"
        try:
            mkdir(s)
        except OSError as e:
            if e.args[0] != upip_errno.EEXIST:
                raise

def ilistdir_ex(path="."):
    dir = opendir_(path)
    if not dir:
        raise_error()
    res = []
    dirent_fmt = "LLHB256s"
    while True:
        dirent = readdir_(dir)
        if not dirent:
            break
        dirent = ffi.as_bytearray(dirent, struct.calcsize(dirent_fmt))
        dirent = struct.unpack(dirent_fmt, dirent)
        yield dirent

def listdir(path="."):
    is_str = type(path) is not bytes
    res = []
    for dirent in ilistdir_ex(path):
        fname = dirent[4].split(b'\0', 1)[0]
        if fname != b"." and fname != b"..":
            if is_str:
                fname = fsdecode(fname)
            res.append(fname)
    return res

def walk(top, topdown=True):
    files = []
    dirs = []
    for dirent in ilistdir_ex(top):
        mode = dirent[3] << 12
        fname = dirent[4].split(b'\0', 1)[0]
        if stat_.S_ISDIR(mode):
            if fname != b"." and fname != b"..":
                dirs.append(fsdecode(fname))
        else:
            files.append(fsdecode(fname))
    if topdown:
        yield top, dirs, files
    for d in dirs:
        yield from walk(top + "/" + d, topdown)
    if not topdown:
        yield top, dirs, files

def open(n, flags, mode=0o777):
    r = open_(n, flags, mode)
    check_error(r)
    return r

def read(fd, n):
    buf = bytearray(n)
    r = read_(fd, buf, n)
    check_error(r)
    return bytes(buf[:r])

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

def chdir(dir):
    r = chdir_(dir)
    check_error(r)

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

def system(command):
    r = system_(command)
    check_error(r)
    return r

def getenv(var, default=None):
    var = getenv_(var)
    if var is None:
        return default
    return var

def fsencode(s):
    if type(s) is bytes:
        return s
    return bytes(s, "utf-8")

def fsdecode(s):
    if type(s) is str:
        return s
    return str(s, "utf-8")


def urandom(n):
    with open("/dev/urandom", "rb") as f:
        return f.read(n)
