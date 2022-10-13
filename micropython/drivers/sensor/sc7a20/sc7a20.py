# SC7A20 driver for MicroPython on ESP8266/ESP32
# MIT license; Copyright (c) 2022 WEMOS.CC

from micropython import const


WHO_AM_I_REG = const(0x0F)
CTRL_REG1 = const(0x20)
CTRL_REG2 = const(0x21)
CTRL_REG3 = const(0x22)
ADDR_STATUS_REG = const(0x27)
OUT_X_L_REG = const(0x28)
OUT_X_H_REG = const(0x29)
OUT_Y_L_REG = const(0x2A)
OUT_Y_H_REG = const(0x2B)
OUT_Z_L_REG = const(0x2C)
OUT_Z_H_REG = const(0x2D)

CHIP_ID = const(0x11)


class SC7A20:
    def __init__(self, i2c, address=0x18):
        self.bus = i2c
        self.slv_addr = address
        self.buf = bytearray(6)
        self.bus.writeto_mem(self.slv_addr, CTRL_REG1, b"\x27")  # 10hz

    def _12bitComplement(self, msb, lsb):
        # temp=0x0000
        temp = msb << 8 | lsb
        temp = temp >> 4
        # 只有高12位有效
        temp = temp & 0x0FFF

        if temp & 0x0800:  # 负数 补码==>原码
            temp = temp & 0x07FF  # 屏弊最高位
            temp = ~temp
            temp = temp + 1
            temp = temp & 0x07FF
            temp = -temp  # 还原最高位

        return temp

    def measure(self):

        self.buf = self.bus.readfrom_mem(self.slv_addr, OUT_X_L_REG, 6)
        accel_X = self._12bitComplement(self.buf[1], self.buf[0])
        accel_Y = self._12bitComplement(self.buf[3], self.buf[2])
        accel_Z = self._12bitComplement(self.buf[5], self.buf[4])
        return accel_X, accel_Y, accel_Z
