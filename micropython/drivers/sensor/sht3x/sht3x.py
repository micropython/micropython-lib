# SHT3x driver for MicroPython on ESP8266/ESP32
# MIT license; Copyright (c) 2022 WEMOS.CC

import utime


class SHT3X:
    def __init__(self, i2c, address=0x45):
        self.bus = i2c
        self.slv_addr = address
        self.buf = bytearray(6)

    def measure(self):
        self.bus.writeto(self.slv_addr, b"\x24\x00")
        utime.sleep(1)
        self.buf = self.bus.readfrom(self.slv_addr, 6)

    def humidity(self):
        humidity_raw = self.buf[3] << 8 | self.buf[4]
        humidity = 100.0 * float(humidity_raw) / 65535.0
        return humidity

    def temperature(self):
        temperature_raw = self.buf[0] << 8 | self.buf[1]
        temperature = (175.0 * float(temperature_raw) / 65535.0) - 45
        return temperature
