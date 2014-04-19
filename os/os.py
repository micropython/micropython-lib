import ffi


libc = ffi.open("libc.so.6")

errno = libc.var("i", "errno")
mkdir_ = libc.func("i", "mkdir", "si")


def check_error(ret):
    if ret == -1:
        raise OSError(errno.get())


def mkdir(name, mode=0o777):
    e = mkdir_(name, mode)
    check_error(e)
