from usocket import *
import usocket as _socket


_GLOBAL_DEFAULT_TIMEOUT = 30

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

    def sendall(self, *args):
        return self.send(*args)
