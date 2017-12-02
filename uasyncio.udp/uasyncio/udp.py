import uerrno
import usocket
from uasyncio.core import *


DEBUG = 0
log = None

def set_debug(val):
    global DEBUG, log
    DEBUG = val
    if val:
        import logging
        log = logging.getLogger("uasyncio.udp")


class UdpSocket:

    def __init__(self, s):
        self.s = s

    def recv(self, n):
        try:
            yield IORead(self.s)
            return self.s.recv(n)
        except:
            #print("recv: exc, cleaning up")
            #print(uasyncio.core._event_loop.objmap, uasyncio.core._event_loop.poller)
            #uasyncio.core._event_loop.poller.dump()
            yield IOReadDone(self.s)
            #print(uasyncio.core._event_loop.objmap)
            #uasyncio.core._event_loop.poller.dump()
            raise

    def recvfrom(self, n):
        try:
            yield IORead(self.s)
            return self.s.recvfrom(n)
        except:
            #print("recv: exc, cleaning up")
            #print(uasyncio.core._event_loop.objmap, uasyncio.core._event_loop.poller)
            #uasyncio.core._event_loop.poller.dump()
            yield IOReadDone(self.s)
            #print(uasyncio.core._event_loop.objmap)
            #uasyncio.core._event_loop.poller.dump()
            raise

    def asendto(self, buf, addr=None):
        while 1:
            res = self.s.sendto(buf, 0, addr)
            #print("send res:", res)
            if res == len(buf):
                return
            print("asento: IOWrite")
            yield IOWrite(self.s)

    def aclose(self):
        yield IOReadDone(self.s)
        self.s.close()


def udp_socket(host=None, port=None):
    if DEBUG and __debug__:
        log.debug("udp_socket(%s, %s)", host, port)
    s = usocket.socket(usocket.AF_INET, usocket.SOCK_DGRAM)
    s.setblocking(False)
    if host and port:
        ai = usocket.getaddrinfo(host, port)
        addr = ai[0][-1]
        try:
            s.connect(addr)
        except OSError as e:
            if e.args[0] != uerrno.EINPROGRESS:
                raise
        if DEBUG and __debug__:
            log.debug("udp_socket: After connect")
    return UdpSocket(s)
    yield
