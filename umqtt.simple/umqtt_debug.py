from umqtt.simple import MQTTClient
from ubinascii import hexlify


class debug_socket:
    def __init__(self, sock):
        self.sock = sock
    
    def read(self, len):
        data = self.sock.read(len)
        print("RECV:", hexlify(data, ':').decode())
        return data

    def write(self, data, len=None):
        print("SEND:", hexlify(data, ':').decode())
        if len is None:
            return self.sock.write(data)
        else:
            return self.sock.write(data, len)

    def __getattr__(self, name):
        return getattr(self.sock, name)


class DebugMQTTClient(MQTTClient):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._sock = None

    @property
    def sock(self):
        return self._sock

    @sock.setter
    def sock(self, val):
        if val:
            val = debug_socket(val)
        self._sock = val
