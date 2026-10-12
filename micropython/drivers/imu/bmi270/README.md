------------
    License: 3-clause BSD, see https://opensource.org/licenses/BSD-3-Clause

    Homepage:  https://codeberg.org/easytarget/bmi270-micropython
    Datasheet: ./reference/bmi270-base-datasheet.pdf

---------------------------

# Micropython driver for the BMI270 IMU

## [`bmi270.py`](bmi270.py)
Homepage: [Here](https://codeberg.org/easytarget/bmi270-micropython)

Original BMI270 driver on the micropython library had limited functionality and some issues with size and speed during init.

This driver retains the original features:
*   Setting Sensor Ranges and Output Data Rates at init
*   Reading Accelerometer and Gyroscope reeadings

Enhancements from original driver:
*   Modifying Sensor Ranges and Output Data Rates (ODR) during use.
*   Entering 'adavnced powersave mode' and enabling / disabling specific sensors and filter power modes.
*   Device internal `temperature()` method has been added.

Some minor code cleanup has been done; more consistent use of constants and names applied, etc.

## Install

Install by copying `bmi270.py` to the root (or import path) of your device in your IDE.
*   Or install with **MIP**
    *   `mip install https://github.com/micropython/micropython-lib/blob/master/micropython/drivers/imu/bmi270/bmi270.py`
    *   run this on the device itself (when connected via WiFi/Network)
*   You can also use mip via **mpremote**:
    *   `mpremote mip install https://github.com/micropython/micropython-lib/blob/master/micropython/drivers/imu/bmi270/bmi270.py`
    *   run this on the commandline of your host PC/system

## Demos and Example
*   [`demo_imu.py`](demo_imu.py) : demonstrates the IMU (Accelerometer and Gyroscope) detector
    *   Press 'b' for a visual/bars mode

### test.py:
```python
import time
from bmi270 import BMI270
from machine import Pin, I2C

# Init in I2C mode, adjust pins as needed
imu = BMI270(I2C(1, scl=Pin(32), sda=Pin(31))

while (True):
    print('Accelerometer: x:{:>6.3f}  y:{:>6.3f}  z:{:>6.3f}'.format(*imu.accel()))
    print('Gyroscope:     x:{:>6.3f}  y:{:>6.3f}  z:{:>6.3f}'.format(*imu.gyro()))
    print('Temperature: {:>4.1f}'.format(imu.temperature()))
    print("")
    time.sleep_ms(100)
```

## Reference
See the [BMI270](https://www.bosch-sensortec.com/products/motion-sensors/imus/bmi270/) documentation at the Bosch site.

### Datasheets:
*   Main datasheet with base feature config: [bmi270-base-datasheet.pdf](./reference/bmi270-base-datasheet.pdf)
    *   Detailed documentation for interrupt pin and power mode control is in this sheet
*   Application note for FIFO mode (no features): [bmi270-fifo-appication-note.pdf](./reference/bmi270-fifo-appication-note.pdf)
*   Application note for legacy features config [bmi270-legacy-appication-note.pdf](./reference/bmi270-legacy-appication-note.pdf)

### Official reference API (C):
https://github.com/boschsensortec/BMI270_SensorAPI

# Usage:

## Classes; Objects and Attributes

```python
class BMI270()
```

#### init()

```python
def __init__(i2c,
             address = 0x68,
             gyro_odr = 100,
             gyro_scale = 2000,
             accel_odr = 100,
             accel_scale = 4,
             force_reset = False,
             bmm_magnet = None)
```

Initializes Device, Gyro and Accelerometer.
*   `i2c`: `machine.I2C()` bus object
*   `address`: I2C address, default 0x68
*   `gyro_odr`:  Hz (0.78, 1.5, 3.1, 6.25, 12.5, 25, 50, **100**, 200, 400, 800, 1600)
*   `gyro_scale`:  dps (125, 250, 500, 1000, **2000**)
*   `accel_odr`: Hz (0.78, 1.5, 3.1, 6.25, 12.5, 25, 50, **100**, 200, 400, 800, 1600)
*   `accel_scale`: g (+/-2, **+/-4**, +/-8, +/-16)
*   `force_reset`: Forces a reset and reinitialisation of the device
*   `bmm_magnet`:  allows passing of a magnetometer device, provided for compatibility

#### sensor\_settings()

```python
def sensor_settings(gyro_odr=None,
                    gyro_scale=None,
                    accel_odr=None,
                    accel_scale=None)
```

Sets or modifies sensor Output Data Rates (ODR) and Scale
*   Values are as specified during `init()`
*   `None` indicates the setting should be left as-is

#### power()

```python
def power(powersave=None,
          accel=None,
          gyro=None,
          acc_filter=None,
          gyr_filter=None,
          gyr_noise=None)
```

Set power modes;
*   See `base` datasheet section 4.5 'Power Modes' (page 26)
*   `None` indicates the setting should be left as-is

Disabling the gyroscope produces greatest savings

*   `powersave` = device 'advanced power save' mode, default `False`
*   `accel` = enable/disable accellerometer, default `True`
*   `gyro` = enable/disable gyroscope, default `True`
*   `acc_filter` = powresave mode for accel filter, default `True`
*   `gyr_filter` = powresave mode for gyro filter, default `True`
*   `gyr_noise` = powersave mode for gyro noise filter, default `False`

Note that gesture detection features in the extended configs do not use the gyroscope

#### gyro()

```python
def gyro()
```

Returns gyroscope vector in degrees/sec.

#### accel()

```python
def accel()
```

Returns acceleration vector in gravity units (9.81m/s^2).

#### magnet()

```python
def magnet()
```

Compatibility method, generally unused: Returns magnetometer vector if a magnetomter has been attached and configured at init.

#### temperature()

```python
def temperature()
```

Returns temperature value in degrees C. This is the chip temperature, not environmental.

