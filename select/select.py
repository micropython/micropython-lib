import ffi
import struct
import os
import errno


libc = ffi.open("libc.so.6")

#int epoll_create(int size);
epoll_create = libc.func("i", "epoll_create", "i")
#int epoll_ctl(int epfd, int op, int fd, struct epoll_event *event);
epoll_ctl = libc.func("i", "epoll_ctl", "iiip")
#int epoll_wait(int epfd, struct epoll_event *events, int maxevents, int timeout);
epoll_wait = libc.func("i", "epoll_wait", "ipii")

EPOLLIN = 0x001
EPOLLPRI = 0x002
EPOLLOUT = 0x004

EPOLL_CTL_ADD = 1
EPOLL_CTL_DEL = 2
EPOLL_CTL_MOD = 3


class Epoll:

    # Second value is actually of uint64_t size, so struct
    # will be smaller on 32bit, but seem to not segfault.
    epoll_event = "IO"

    def __init__(self, epfd):
        self.epfd = epfd
        self.evbuf = struct.pack(self.epoll_event, 0, 0)

    def register(self, fd, eventmask=EPOLLIN|EPOLLPRI|EPOLLOUT, retval=None):
        "retval is extension to stdlib, value to use in results from .poll()."
        if retval is None:
            retval = fd
        s = struct.pack(self.epoll_event, eventmask, retval)
        r = epoll_ctl(self.epfd, EPOLL_CTL_ADD, fd, s)
        if r == -1 and os.errno.get() == errno.EEXIST:
            r = epoll_ctl(self.epfd, EPOLL_CTL_MOD, fd, s)
        os.check_error(r)

    def poll(self, timeout=-1):
        s = bytearray(self.evbuf)
        n = epoll_wait(self.epfd, s, 1, timeout)
        os.check_error(n)
        res = []
        if n > 0:
            vals = struct.unpack(self.epoll_event, s)
            res.append((vals[1], vals[0]))
        return res


def epoll(sizehint=4):
    fd = epoll_create(sizehint)
    os.check_error(fd)
    return Epoll(fd)
