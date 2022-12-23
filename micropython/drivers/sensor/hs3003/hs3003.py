"""
The MIT License (MIT)

Copyright (c) 2023 Arduino SA

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

HS3003 driver for MicroPython.

Example usage:

import time
from hs3003 import HS3003
from machine import Pin, I2C

bus = I2C(1, scl=Pin(15), sda=Pin(14))
hts = HS3003(bus)

while True:
    rH   = hts.humidity()
    temp = hts.temperature()
    print ("rH: %.2f%% T: %.2fC" %(rH, temp))
    time.sleep_ms(100)
"""

import struct


class HS3003:
    def __init__(self, bus, address=0x44):
        self.bus = bus
        self.address = address

    def _read_data(self):
        # Init measurement mode
        self.bus.writeto(self.address, b"")
        # Data fetch
        return struct.unpack(">HH", self.bus.readfrom(self.address, 4))

    def humidity(self):
        """Returns the relative humidity in percent."""
        h, t = self._read_data()
        return ((h & 0x3FFF) / 16383) * 100

    def temperature(self):
        """Returns the temperature in degrees Celsius."""
        h, t = self._read_data()
        return ((t >> 2) / 16383) * 165 - 40
