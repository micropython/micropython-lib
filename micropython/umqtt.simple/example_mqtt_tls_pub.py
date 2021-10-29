from umqtt.simple import MQTTClient

# Test reception e.g. with:
# mosquitto_sub -t foo_topic

def main(server="localhost"):
    # NOTE: Checking server certificate is DISABLE
    ssl_params = {"server_hostname": server}
    c = MQTTClient("umqtt_client",
                   server=server,
                   port=8883,
                   user="<username>",
                   password="<password>",
                   keepalive=60,
                   ssl=True,
                   ssl_params=ssl_params)
    c.connect()
    c.publish(b"foo_topic", b"hello")
    c.disconnect()


if __name__ == "__main__":
    main()
