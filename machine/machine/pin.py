import umachine

class Pin(umachine.PinBase):

    IN = "in"
    OUT = "out"

    def __init__(self, no, dir=IN):
        pref = "/sys/class/gpio/gpio{}/".format(no)
        dirf = pref + "direction"
        try:
            f = open(dirf, "w")
        except OSError:
            with open("/sys/class/gpio/export", "w") as f:
                f.write(str(no))
            f = open(dirf, "w")
        f.write(dir)
        self.f = open(pref + "value", "rw")

    def value(self, v=None):
        if v is None:
            return self.f.read(1) == "1"
        self.f.write(str(v))

    def deinit(self):
        self.f.close()
