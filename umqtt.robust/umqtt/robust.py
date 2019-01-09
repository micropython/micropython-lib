import utime
from . import simple

class MQTTClient(simple.MQTTClient):

    DELAY = 2
    DEBUG = False

    def delay(self, i):
        """
        Sleeps the thread for 2 seconds.

        :param i: Does not seem to be used.
        :return: None
        """
        utime.sleep(self.DELAY)

    def log(self, in_reconnect: bool, e: Exception):
        """
        Simple logging function.

        :param in_reconnect: Boolean flag for if function is called in reconnect.
        :type in_reconnect: bool
        :param e: Exception that occured.
        :type e: Exception
        :return:None
        """
        if self.DEBUG:
            if in_reconnect:
                print("mqtt reconnect: %r" % e)
            else:
                print("mqtt: %r" % e)

    def reconnect(self):
        """
        Reconnects to MQTT broker.

        :return: Call to super method connect. Connection response.
        :rtype: int
        """
        i = 0
        while 1:
            try:
                return super().connect(False)
            except OSError as e:
                self.log(True, e)
                i += 1
                self.delay(i)

    def publish(self, topic: str, msg: str, retain=False, qos=0):
        """
        Calls super publish method. If this method fails,
        the error is logged and then the client attempts to reconnect
        to the MQTT broker.

        :param topic: Topic you wish to publish to. Takes the form "path/to/topic"
        :type topic: str
        :param msg: Message to publish to topic.
        :type msg: str
        :param retain: Have the MQTT broker retain the message.
        :type retain: bool
        :param qos: Sets quality of service level. Accepts values 0 to 2. PLEASE NOTE qos=2 is not actually supported.
        :type qos: int
        :return: None
        """
        while 1:
            try:
                return super().publish(topic, msg, retain, qos)
            except OSError as e:
                self.log(False, e)
            self.reconnect()

    def wait_msg(self):
        """
        Calls super wait_msg. In the event of an exception, the
        exception is logged and then the client attempts to
        reconnect to the MQTT broker.

        :return:None
        """
        while 1:
            try:
                return super().wait_msg()
            except OSError as e:
                self.log(False, e)
            self.reconnect()
