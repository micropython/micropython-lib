import ffi
import _libc


libc = _libc.get()

fcntl_l = libc.func("i", "fcntl", "iil")
fcntl_s = libc.func("i", "fcntl", "iip")
ioctl_l = libc.func("i", "ioctl", "iil")
ioctl_s = libc.func("i", "ioctl", "iip")


def fcntl(fd, op, arg):
    if type(arg) is int:
        return fcntl_l(fd, op, arg)
    else:
        return fcntl_s(fd, op, arg)


def ioctl(fd, op, arg):
    if type(arg) is int:
        return ioctl_l(fd, op, arg)
    else:
        return ioctl_s(fd, op, arg)
