import utime
from . import simple

class MQTTClient(simple.MQTTClient):

    DELAY = 2
    DEBUG = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscriptions = []

    def delay(self, i):
        utime.sleep(self.DELAY)

    def log(self, in_reconnect, e):
        if self.DEBUG:
            if in_reconnect:
                print("mqtt reconnect: %r" % e)
            else:
                print("mqtt: %r" % e)

    def reconnect(self):
        i = 0
        while 1:
            try:
                ret = super().connect(False)
                if not ret:
                    for topic, qos in self.subscriptions:
                        if self.DEBUG:
                            print("mqtt resubscribe: %r" % topic)
                        super().subscribe(topic, qos)
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

    def subscribe(self, topic, qos=0):
        while 1:
            try:
                ret = super().subscribe(topic, qos)
                self.subscriptions.append((topic, qos))
                return ret
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
