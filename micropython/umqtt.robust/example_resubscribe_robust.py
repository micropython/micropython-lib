import umqtt.robust
import time

# A common expectation of the robust client is that it should re-subscribe to
# topics after a reconnect(). This feature adds to code size and isn't required
# in all circumstances, so hasn't been included by default.

# You can easily inherit from umqtt.robust.MQTTClient to add this feature...


class MyMQTTClient(umqtt.robust.MQTTClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.topics = []

    def connect(self, clean_session=True):
        if not super().connect(clean_session):
            # Session was not restored - need to resubscribe
            for topic in self.topics:
                self.subscribe(topic)

            return False  # Session was not restored

        return True  # Session was restored

    def subscribe(self, topic):
        print("Subscribing to", topic)
        super().subscribe(topic)
        if topic not in self.topics:
            self.topics.append(topic)


# Change the server to test on your MQTT broker
c = MyMQTTClient("test_client", "localhost", keepalive=5)
c.DEBUG = True

c.set_callback(print)

c.connect()
c.subscribe(b"test/topic/a")

c.publish(b"test/topic/a", b"message 1")
c.wait_msg()

# Connection breaks once keepalive expires
time.sleep(8)

c.publish(b"test/topic/a", b"message 2")  # publish() doesn't detect OSError, message 2 is lost
c.check_msg()  # check_msg() detects OSError and will reconnect()

c.publish(b"test/topic/a", b"message 3")
c.wait_msg()
