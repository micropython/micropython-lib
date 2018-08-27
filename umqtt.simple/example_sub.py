import time
from umqtt.simple import MQTTClient
#from umqtt_debug import DebugMQTTClient as MQTTClient

# Publish test messages e.g. with:
# mosquitto_pub -t foo_topic -m hello

# Received messages from subscriptions will be delivered to this callback
def sub_cb(topic, msg):
    print((topic, msg))
    
def main(server="localhost", topic="foo_topic", qos=0, blocking=True):
    c = MQTTClient("umqtt_client", server)
    c.set_callback(sub_cb)
    c.connect()
    c.subscribe(topic.encode('utf-8'), int(qos))
    while True:
        if blocking:
            # Blocking wait for message
            c.wait_msg()
        else:
            # Non-blocking wait for message
            c.check_msg()
            # Then need to sleep to avoid 100% CPU usage (in a real
            # app other useful actions would be performed instead)
            time.sleep(1)

    c.disconnect()

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
