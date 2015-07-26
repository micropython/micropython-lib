from usocket import *
import usocket as _socket


_GLOBAL_DEFAULT_TIMEOUT = 30
IPPROTO_IP = 0
IP_ADD_MEMBERSHIP = 35
IP_DROP_MEMBERSHIP = 36


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

    def sendall(self, *args):
        return self.send(*args)
