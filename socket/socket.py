from usocket import *
import usocket as _socket


_GLOBAL_DEFAULT_TIMEOUT = 30
IPPROTO_IP = 0
IP_ADD_MEMBERSHIP = 35
IP_DROP_MEMBERSHIP = 36

error = OSError

def _resolve_addr(addr):
    if isinstance(addr, (bytes, bytearray)):
        return addr
    if len(addr) != 2:
        raise NotImplementedError("Only IPv4 supported")
    a = "0.0.0.0" if addr[0] == "" else addr[0]
    a = getaddrinfo(a, addr[1], _socket.AF_INET)
    return a[0][4]

def inet_aton(addr):
    return inet_pton(AF_INET, addr)

def create_connection(addr, timeout=None, source_address=None):
    s = socket()
    #print("Address:", addr)
    ais = getaddrinfo(addr[0], addr[1])
    #print("Address infos:", ais)
    for ai in ais:
        try:
            s.connect(ai[4])
            return s
        except:
            pass


class socket(_socket.socket):

    def bind(self, addr):
        return super().bind(_resolve_addr(addr))

    def connect(self, addr):
        return super().connect(_resolve_addr(addr))

    def sendall(self, *args):
        return self.send(*args)
