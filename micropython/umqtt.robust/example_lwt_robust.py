import umqtt.robust
import time

# Last will and testament (LWT) is commonly used to signal a device as being
# online or offline. This example builds on umqtt.robust to provide a more
# reliable connection with the MQTT broker and signal its status as being
# either Online or Offline. This feature adds to code size and isn't required
# in all circumstances, so hasn't been included by default.


class MyMQTTClient(umqtt.robust.MQTTClient):
    def connect(self, clean_session=True):
        self.set_last_will(b"tele/test/LWT", b"Offline", retain=True)
        try:
            return super().connect(clean_session)
        finally:
            self.publish(b"tele/test/LWT", b"Online", retain=True)


# Change the server to test on your MQTT broker
c = MyMQTTClient("test_client", "localhost", keepalive=5)
c.DEBUG = True

c.connect()

# wait_msg() only returns when a message is received, so this example
# highlights the LWT feature. In practical applications, the broker keeps
# the connection alive only if there is traffic from the client (ping(), etc.)
c.wait_msg()
