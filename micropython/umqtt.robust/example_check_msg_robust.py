import umqtt.robust
import time

# Instantiate an MQTTClient with a keepalive time of 5 seconds (to help us test
# what happens to check_msg() with a broken connection)
m = umqtt.robust.MQTTClient(host="localhost", debug=True, keepalive=5)

m.connect()

# Wait for the broker to consider us dead
time.sleep(6)

# This should initiate a reconnect() and return immediately
m.check_msg()
