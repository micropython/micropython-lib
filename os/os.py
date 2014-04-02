import ffi


libc = ffi.open("libc.so.6")

errno = libc.var("i", "errno")
mkdir_ = libc.func("i", "mkdir", "si")


def mkdir(name, mode=0o777):
    e = mkdir_(name, mode)
    if not e:
        return
    raise OSError(errno.get())
