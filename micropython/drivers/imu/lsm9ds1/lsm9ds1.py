"""
The MIT License (MIT)

Copyright (c) 2013, 2014 Damien P. George
Copyright (c) 2022-2023 Ibrahim Abdelkader <iabdalkader@openmv.io>

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


LSM9DS1 - 9DOF inertial sensor of STMicro driver for MicroPython.
The sensor contains an accelerometer / gyroscope / magnetometer
Uses the internal FIFO to store up to 16 gyro/accel data, use the iter_accel_gyro generator to access it.

Example usage:

import time
from lsm9ds1 import LSM9DS1
from machine import Pin, I2C

imu = LSM9DS1(I2C(1, scl=Pin(15), sda=Pin(14)))

while (True):
    #for g,a in imu.iter_accel_gyro(): print(g,a)    # using fifo
    print('Accelerometer: x:{:>8.3f} y:{:>8.3f} z:{:>8.3f}'.format(*imu.accel()))
    print('Magnetometer:  x:{:>8.3f} y:{:>8.3f} z:{:>8.3f}'.format(*imu.magnet()))
    print('Gyroscope:     x:{:>8.3f} y:{:>8.3f} z:{:>8.3f}'.format(*imu.gyro()))
    print("")
    time.sleep_ms(100)
"""
import array
from micropython import const


_WHO_AM_I = const(0xF)
_CTRL_REG1_G = const(0x10)
_INT_GEN_SRC_G = const(0x14)
_OUT_TEMP = const(0x15)
_OUT_G = const(0x18)
_CTRL_REG4_G = const(0x1E)
_STATUS_REG = const(0x27)
_OUT_XL = const(0x28)
_FIFO_CTRL_REG = const(0x2E)
_FIFO_SRC = const(0x2F)
_OFFSET_REG_X_M = const(0x05)
_CTRL_REG1_M = const(0x20)
_OUT_M = const(0x28)
_ACCEL_SCALE = const((2, 16, 4, 8))
_GYRO_SCALE = const((245, 500, 2000))
_MAGNET_SCALE = const((4, 8, 12, 16))
_ODR_IMU = const((0, 14.9, 59.5, 119, 238, 476, 952))
_ODR_MAGNET = const((0.625, 1.25, 2.5, 5, 10, 20, 40, 80))


class LSM9DS1:
    def __init__(
        self,
        bus,
        address_imu=0x6B,
        address_magnet=0x1E,
        gyro_odr=952,
        gyro_scale=245,
        accel_odr=952,
        accel_scale=4,
        magnet_odr=80,
        magnet_scale=4,
    ):
        """Initalizes Gyro, Accelerometer and Magnetometer.
        bus: IMU bus
        address_imu: IMU I2C address.
        address_magnet: Magnetometer I2C address.
        gyro_odr: (0, 14.9Hz, 59.5Hz, 119Hz, 238Hz, 476Hz, 952Hz)
        gyro_scale: (245dps, 500dps, 2000dps )
        accel_odr: (0, 14.9Hz, 59.5Hz, 119Hz, 238Hz, 476Hz, 952Hz)
        accel_scale: (+/-2g, +/-4g, +/-8g, +-16g)
        magnet_odr: (0.625Hz, 1.25Hz, 2.5Hz, 5Hz, 10Hz, 20Hz, 40Hz, 80Hz)
        magnet_scale: (+/-4, +/-8, +/-12, +/-16)
        """
        self.bus = bus
        self.address_imu = address_imu
        self.address_magnet = address_magnet

        # Sanity checks
        if gyro_odr not in _ODR_IMU:
            raise ValueError("Invalid gyro sampling rate: %d" % gyro_odr)
        if gyro_scale not in _GYRO_SCALE:
            raise ValueError("Invalid gyro scaling: %d" % gyro_scale)

        if accel_odr not in _ODR_IMU:
            raise ValueError("Invalid accelerometer sampling rate: %d" % accel_odr)
        if accel_scale not in _ACCEL_SCALE:
            raise ValueError("Invalid accelerometer scaling: %d" % accel_scale)

        if magnet_odr not in _ODR_MAGNET:
            raise ValueError("Invalid magnet sampling rate: %d" % magnet_odr)
        if magnet_scale not in _MAGNET_SCALE:
            raise ValueError("Invalid magnet scaling: %d" % magnet_scale)

        if (self.magent_id() != b"=") or (self.gyro_id() != b"h"):
            raise OSError(
                "Invalid LSM9DS1 device, using address {}/{}".format(address_imu, address_magnet)
            )

        mv = memoryview(bytearray(6))

        # Configure Gyroscope.
        mv[0] = (_ODR_IMU.index(gyro_odr) << 5) | ((_GYRO_SCALE.index(gyro_scale)) << 3)
        mv[1:4] = b"\x00\x00\x00"
        self.bus.writeto_mem(self.address_imu, _CTRL_REG1_G, mv[:5])

        # Configure Accelerometer
        mv[0] = 0x38  # ctrl4 - enable x,y,z, outputs, no irq latching, no 4D
        mv[1] = 0x38  # ctrl5 - enable all axes, no decimation
        # ctrl6 - set scaling and sample rate of accel
        mv[2] = (_ODR_IMU.index(accel_odr) << 5) | ((_ACCEL_SCALE.index(accel_scale)) << 3)
        mv[3] = 0x00  # ctrl7 - leave at default values
        mv[4] = 0x4  # ctrl8 - leave at default values
        mv[5] = 0x2  # ctrl9 - FIFO enabled
        self.bus.writeto_mem(self.address_imu, _CTRL_REG4_G, mv)

        # fifo: use continous mode (overwrite old data if overflow)
        self.bus.writeto_mem(self.address_imu, _FIFO_CTRL_REG, b"\x00")
        self.bus.writeto_mem(self.address_imu, _FIFO_CTRL_REG, b"\xc0")

        # Configure Magnetometer
        mv[0] = 0x40 | (magnet_odr << 2)  # ctrl1: high performance mode
        mv[1] = _MAGNET_SCALE.index(magnet_scale) << 5  # ctrl2: scale, normal mode, no reset
        mv[2] = 0x00  # ctrl3: continous conversion, no low power, I2C
        mv[3] = 0x08  # ctrl4: high performance z-axis
        mv[4] = 0x00  # ctr5: no fast read, no block update
        self.bus.writeto_mem(self.address_magnet, _CTRL_REG1_M, mv[:5])

        self.gyro_scale = 32768 / gyro_scale
        self.accel_scale = 32768 / accel_scale
        self.scale_factor_magnet = 32768 / ((_MAGNET_SCALE.index(magnet_scale) + 1) * 4)

        # Allocate scratch buffer for efficient conversions and memread op's
        self.scratch_int = array.array("h", [0, 0, 0])

    def calibrate_magnet(self, offset):
        """
        offset is a magnet vector that will be subtracted by the magnetometer
        for each measurement. It is written to the magnetometer's offset register
        """
        import struct

        offset = [int(i * self.scale_factor_magnet) for i in offset]
        self.bus.writeto_mem(self.address_magnet, _OFFSET_REG_X_M, struct.pack("<HHH", offset))

    def gyro_id(self):
        return self.bus.readfrom_mem(self.address_imu, _WHO_AM_I, 1)

    def magent_id(self):
        return self.bus.readfrom_mem(self.address_magnet, _WHO_AM_I, 1)

    def magnet(self):
        """Returns magnetometer vector in gauss.
        raw_values: if True, the non-scaled adc values are returned
        """
        mv = memoryview(self.scratch_int)
        f = self.scale_factor_magnet
        self.bus.readfrom_mem_into(self.address_magnet, _OUT_M | 0x80, mv)
        return (mv[0] / f, mv[1] / f, mv[2] / f)

    def gyro(self):
        """Returns gyroscope vector in degrees/sec."""
        mv = memoryview(self.scratch_int)
        f = self.gyro_scale
        self.bus.readfrom_mem_into(self.address_imu, _OUT_G | 0x80, mv)
        return (mv[0] / f, mv[1] / f, mv[2] / f)

    def accel(self):
        """Returns acceleration vector in gravity units (9.81m/s^2)."""
        mv = memoryview(self.scratch_int)
        f = self.accel_scale
        self.bus.readfrom_mem_into(self.address_imu, _OUT_XL | 0x80, mv)
        return (mv[0] / f, mv[1] / f, mv[2] / f)

    def iter_accel_gyro(self):
        """A generator that returns tuples of (gyro,accelerometer) data from the fifo."""
        while True:
            fifo_state = int.from_bytes(
                self.bus.readfrom_mem(self.address_imu, _FIFO_SRC, 1), "big"
            )
            if fifo_state & 0x3F:
                # print("Available samples=%d" % (fifo_state & 0x1f))
                yield self.gyro(), self.accel()
            else:
                break
