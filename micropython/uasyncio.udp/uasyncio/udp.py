import usocket
from uasyncio import core


DEBUG = 0
log = None

def set_debug(val):
    global DEBUG, log
    DEBUG = val
    if val:
        import logging
        log = logging.getLogger("uasyncio.udp")

def socket(af=usocket.AF_INET):
    s = usocket.socket(af, usocket.SOCK_DGRAM)
    s.setblocking(False)
    return s

def recv(s, n):
    try:
        yield core.IORead(s)
        return s.recv(n)
    except:
        #print("recv: exc, cleaning up")
        #print(uasyncio.core._event_loop.objmap, uasyncio.core._event_loop.poller)
        #uasyncio.core._event_loop.poller.dump()
        yield core.IOReadDone(s)
        #print(uasyncio.core._event_loop.objmap)
        #uasyncio.core._event_loop.poller.dump()
        raise

def recvfrom(s, n):
    try:
        yield core.IORead(s)
        return s.recvfrom(n)
    except:
        #print("recv: exc, cleaning up")
        #print(uasyncio.core._event_loop.objmap, uasyncio.core._event_loop.poller)
        #uasyncio.core._event_loop.poller.dump()
        yield core.IOReadDone(s)
        #print(uasyncio.core._event_loop.objmap)
        #uasyncio.core._event_loop.poller.dump()
        raise

def sendto(s, buf, addr=None):
    while 1:
        res = s.sendto(buf, addr)
        #print("send res:", res)
        if res == len(buf):
            return
        print("sendto: IOWrite")
        yield core.IOWrite(s)

def close(s):
    yield core.IOReadDone(s)
    s.close()
