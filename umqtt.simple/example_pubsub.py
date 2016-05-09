import time
from umqtt.simple import MQTTClient

def sub_cb(topic, msg):
    print((topic, msg))

c = MQTTClient("uqmtt_client", "localhost")
c.connect()
c.subscribe(b"foo_topic")
c.publish(b"foo_topic", b"hello")
while 1:
    c.wait_msg()
c.disconnect()
