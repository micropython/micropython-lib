# LSM6DSOX Basic Example.
import time
from lsm6dsox import LSM6DSOX

from machine import Pin, I2C

lsm = LSM6DSOX(I2C(0, scl=Pin(13), sda=Pin(12)))
# Or init in SPI mode.
# lsm = LSM6DSOX(SPI(5), cs=Pin(10))

while True:
    print("Accelerometer: x:{:>8.3f} y:{:>8.3f} z:{:>8.3f}".format(*lsm.accel()))
    print("Gyroscope:     x:{:>8.3f} y:{:>8.3f} z:{:>8.3f}".format(*lsm.gyro()))
    print("")
    time.sleep_ms(100)
