import ffi
import ustruct as struct
import os
import errno
import _libc


libc = _libc.get()

#int epoll_create(int size);
epoll_create = libc.func("i", "epoll_create", "i")
#int epoll_ctl(int epfd, int op, int fd, struct epoll_event *event);
epoll_ctl = libc.func("i", "epoll_ctl", "iiiP")
#int epoll_wait(int epfd, struct epoll_event *events, int maxevents, int timeout);
epoll_wait = libc.func("i", "epoll_wait", "ipii")

EPOLLIN = 0x001
EPOLLPRI = 0x002
EPOLLOUT = 0x004
EPOLLERR = 0x008
EPOLLHUP = 0x010
EPOLLRDHUP = 0x2000
EPOLLONESHOT = 1 << 30
EPOLLET  = 1 << 31

EPOLL_CTL_ADD = 1
EPOLL_CTL_DEL = 2
EPOLL_CTL_MOD = 3

# TODO: struct epoll_event's 2nd member is union of uint64_t, etc.
# On x86, uint64_t is 4-byte aligned, on many other platforms - 8-byte.
# Until uctypes module can assign native struct offset, use dirty hack
# below.
# TODO: Get rid of all this dirtiness, move it on C side
if _libc.bitness > 32:
    # On x86_64, epoll_event is packed struct
    epoll_event = "<IO"
elif struct.calcsize("IQ") == 12:
    epoll_event = "IO"
else:
    epoll_event = "QO"

class Epoll:

    def __init__(self, epfd):
        self.epfd = epfd
        self.evbuf = struct.pack(epoll_event, 0, None)
        self.registry = {}

    def register(self, fd, eventmask=EPOLLIN|EPOLLPRI|EPOLLOUT, retval=None):
        "retval is extension to stdlib, value to use in results from .poll()."
        if retval is None:
            retval = fd
        s = struct.pack(epoll_event, eventmask, retval)
        r = epoll_ctl(self.epfd, EPOLL_CTL_ADD, fd, s)
        if r == -1 and os.errno_.get() == errno.EEXIST:
            r = epoll_ctl(self.epfd, EPOLL_CTL_MOD, fd, s)
        os.check_error(r)
        # We must keep reference to retval, or it may be GCed. And we must
        # keep mapping from fd to retval to be able to get rid of this retval
        # reference later.
        self.registry[fd] = retval

    def unregister(self, fd):
        # Pass dummy event structure, to workaround kernel bug
        r = epoll_ctl(self.epfd, EPOLL_CTL_DEL, fd, self.evbuf)
        os.check_error(r)
        del self.registry[fd]

    def poll(self, timeout=-1):
        s = bytearray(self.evbuf)
        while True:
            n = epoll_wait(self.epfd, s, 1, timeout)
            if not os.check_error(n):
                break
            # TODO: what about timeout value?
        res = []
        if n > 0:
            vals = struct.unpack(epoll_event, s)
            res.append((vals[1], vals[0]))
        return res

    def close(self):
        os.close(self.epfd)


def epoll(sizehint=4):
    fd = epoll_create(sizehint)
    os.check_error(fd)
    return Epoll(fd)
