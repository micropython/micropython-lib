# NeoPixel driver for MicroPython
# MIT license; Copyright (c) 2016 Damien P. George, 2021 Jim Mussared

from machine import bitstream


class NeoPixel:
    # G R B W
    ORDER = (1, 0, 2, 3)

    def __init__(self, pin, n, bpp=3, timing=1, brightness: float = None):
        self.pin = pin
        self.n = n
        self.bpp = bpp
        self.brightness = (
            min(max(brightness, 0.0), 1.0) if brightness is not None else None
        )
        self.buf = bytearray(n * bpp)
        self.pin.init(pin.OUT)
        # Timing arg can either be 1 for 800kHz or 0 for 400kHz,
        # or a user-specified timing ns tuple (high_0, low_0, high_1, low_1).
        self.timing = (
            ((400, 850, 800, 450) if timing else (800, 1700, 1600, 900))
            if isinstance(timing, int)
            else timing
        )

    def _apply_brightness(self, v):
        if self.brightness is not None:
            return tuple(round(c * self.brightness) for c in v)
        return v

    def __len__(self):
        return self.n

    def __setitem__(self, i, v):
        offset = i * self.bpp
        v = self._apply_brightness(v)
        for i in range(self.bpp):
            self.buf[offset + self.ORDER[i]] = v[i]

    def __getitem__(self, i):
        offset = i * self.bpp
        return tuple(self.buf[offset + self.ORDER[i]] for i in range(self.bpp))

    def fill(self, v):
        v = self._apply_brightness(v)
        b = self.buf
        l = len(self.buf)
        bpp = self.bpp
        for i in range(bpp):
            c = v[i]
            j = self.ORDER[i]
            while j < l:
                b[j] = c
                j += bpp

    def set_brightness(self, b: float):
        self.brightness = min(max(b, 0.0), 1.0)
        # This may look odd but because __getitem__ and __setitem__ handle all the
        # brightness logic already, we can offload the work to those methods.
        for i in range(self.n):
            self[i] = self[i]

    def write(self):
        # BITSTREAM_TYPE_HIGH_LOW = 0
        bitstream(self.pin, 0, self.timing, self.buf)
