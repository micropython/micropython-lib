from umqtt.simple import MQTTClient
#from umqtt_debug import DebugMQTTClient as MQTTClient

# Test reception e.g. with:
# mosquitto_sub -t foo_topic

def main(server="localhost", topic="foo_topic", msg="hello", qos=0):
    c = MQTTClient("umqtt_client", server)
    c.connect()
    c.publish(topic.encode('utf-8'), msg.encode('utf-8'), qos=int(qos))
    c.disconnect()

if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
