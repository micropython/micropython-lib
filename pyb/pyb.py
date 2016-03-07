class LED:

    def __init__(self, id):
        self.f = open("/sys/class/leds/%s/brightness" % id, "r+b")

    def on(self):
        self.f.write(b"255")

    def off(self):
        self.f.write(b"0")

    def set(self, v):
        self.f.write(b"{}".format(0 if v < 0 else 255 if v > 255 else v))

    def get(self):
        self.f.seek(0)
        return int(self.f.read())

    def toggle(self):
        self.set(255 if self.get() else 0)
