import utime
from . import simple

class MQTTClient(simple.MQTTClient):

    DELAY = 2
    DEBUG = False

    def delay(self, i):
        utime.sleep(self.DELAY)

    def log(self, in_reconnect, e):
        if self.DEBUG:
            if in_reconnect:
                print("mqtt reconnect: %r" % e)
            else:
                print("mqtt: %r" % e)

    def connect(self, clean_session=True):
        self.block = True
        super().connect(clean_session)

    def reconnect(self):
        i = 0
        while 1:
            try:
                ret = super().connect(False)
                if not self.block:
                    self.sock.setblocking(False)
                return ret
            except OSError as e:
                self.log(True, e)
                i += 1
                self.delay(i)

    def publish(self, topic, msg, retain=False, qos=0):
        while 1:
            try:
                return super().publish(topic, msg, retain, qos)
            except OSError as e:
                self.log(False, e)
            self.reconnect()

    def wait_msg(self):
        while 1:
            try:
                return super().wait_msg()
            except OSError as e:
                self.log(False, e)
            self.reconnect()


    def check_msg(self):
        # memorizing the non blocking state in case of connection failure,
        # we don't want to get stuck after reconnection
        self.block = False
        ret = super().check_msg()
        self.block = True
        return ret
