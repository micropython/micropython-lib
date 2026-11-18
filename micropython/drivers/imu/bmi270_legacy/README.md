------------
    License: 3-clause BSD, see https://opensource.org/licenses/BSD-3-Clause

    Homepage:  https://codeberg.org/easytarget/bmi270-micropython
    Datasheet: ./reference/bmi270-base-datasheet.pdf

---------------------------

# Micropython driver for the BMI270 IMU with Legacy (Tablet/Phone) features

## [`bmi270_legacy.py`](bmi270_legacy.py)
Homepage: [Here](https://codeberg.org/easytarget/bmi270-micropython)

Original BMI270 driver on the micropython library had limited functionality and some issues with size and speed during init.

This driver retains the original features:
*   Setting Sensor Ranges and Output Data Rates at init
*   Reading Accelerometer and Gyroscope reeadings

Enhancements from original driver:
*   Modifying Sensor Ranges and Output Data Rates (ODR) during use.
*   Entering 'adavnced powersave mode' and enabling / disabling specific sensors and filter power modes.
*   Device internal `temperature()` method has been added.

Provides all the features of the `base` driver, but has been extended to use the '**legacy**' config provided by Bosch
*   This config profile is optimised for Tablet and Phone devices (eg the Tab5 I am working with).
*   It is considerably larger than the 'fast' config (8k vs 328b), and the driver itself is unavoidably large, but is still fast to load at init().
*   There are other Bosch configs targeting wearables, watches and security monitoring.
    *   It would be possible to use the legacy driver as a template and create variants for them.

Working:
*   Acceleration and Gyro readings
*   Orientation, faceup/down, activity step counting and interrupts
*   No-motion, any-motion, significant-motion, flat, hi and low G detection with interrupts
*   Tap detection, settings and interrupt
*   Step detection and count watermark interrupts
*   Detailed options for orientation, motion and detectors
*   Device temperature
*   Interrupt pin mode setting and masking
*   PowerSave mode settings

Not Implemented:
*   Fast data logging (FIFO mode)
*   Gyro and acceleration calibration and advanced filtering
*   Slave (accessory)  devices; eg magnetometer
*   OIS (image stabilisation) slave mode
*   NVM settings memory
*   A few other advanced/obscure things this chip can do



## Install

Install by copying `bmi270_legacy.py` to the root (or import path) of your device in your IDE.
*   Or install with **MIP**
    *   `mip install https://github.com/micropython/micropython-lib/blob/master/micropython/drivers/imu/bmi270/bmi270_legacy.py`
    *   run this on the device itself (when connected via WiFi/Network)
*   You can also use mip via **mpremote**:
    *   `mpremote mip install https://github.com/micropython/micropython-lib/blob/master/micropython/drivers/imu/bmi270/bmi270_legacy.py`
    *   run this on the commandline of your host PC/system

## Demo and Example
*   [`demo_legacy.py`](demo_legacy.py) : demonstrates the orientation and activity detection features of the **legacy** profile
    *   See the 'commands summary' at startup, `p` to pause

### test.py:
```python
import time
from bmi270 import BMI270_LEGACY as BMI270
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
class BMI270_LEGACY()
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

### Interrupt Pin Control and Masking

#### device\_interrupt\_mask()

```python
def device_interrupt_mask(pin1=0b1000, pin2=0b1000)
```

Enable/disable device interrupts (4 bits)
*   Default is to enable device error interrupts on both pins, but data ready and fifo full interrupts are suppressed
    *   `0` - fifo full
    *   `1` - fifo watermark
    *   `2` - data ready
    *   `3` - error

#### feature\_interrupt\_mask()

```python
def feature_interrupt_mask(pin1=0b11111111, pin2=0b11111111)
```

Enable/disable feature interrupts (8 bits)
*   Default is to enable all feature interrupts on both interrupt output pins
*   Enable/Disable features to control which interrupts will be flagged
    *   `0` - significant motion
    *   `1` - step activity
    *   `2` - high and low G
    *   `3` - tap
    *   `4` - flat
    *   `5` - no motion
    *   `6` - any motion
    *   `7` - orientation

#### int1\_pin\_setup()

```python
def int1_pin_setup(enable, active_low=True, pushpull=True)
```

Set interrupt pin 1 electrical characteristics
*   Pin is disabled by default
*   see datasheet for full description

#### int2\_pin\_setup()

```python
def int2_pin_setup(enable, active_low=True, pushpull=True)
```

Set interrupt pin 2 electrical characteristics
*   Pin is disabled by default
*   see datasheet for full description

#### int\_pin\_latch()

```python
def int_pin_latch(latching=False)
```

Set the interrupt non-latching / latching flag

#### interrupts()

```python
def interrupts()
```

Report all active interrupt flags and values as appropriate
*   Possible feature interrupt flags are:
    *   `sig_motion`,`step_act`,`high_low_g`,`tap`,`flat`,`no_motion`,`any_motion`,`orientation`
    *   Note that some interrupts are combined (step/activity, hiG/loG, etc.)
*   There are also device level interrupts:
    *   `fifo_full`,`fifo_watermark`,`error`,`aux_data_ready`,`gyro_data_ready`,`accel_data_ready`
    *    see the datasheet(s) for more.
*   The attributes `FEATURE_INT_FLAGS` and `DEVICE_INT_FLAGS` reference these in the code

Note: In order to be flagged here the Feature *must* be enabled (`*_enable()` methods below) *AND* it *must* be assigned to one of the two interrupt pins (`feature_interrupt_mask()` above). This is a device limitation.

## Tap detection

#### taps()

```python
def taps()
```

Return last recorded tap.

#### tap\_enable()

```python
def tap_enable(*taps)
```

Enable the requested `taps` (list), and set `wait_timeout` true as needed

#### tap\_settings()

```python
def tap_settings(sense_threshold=9, maximum_duration=130, quiet_time=80, wait_timeout=False, axis=2)
```

Tap detection settings:
*   `threshold`in units of ~78mg
*   `duration` and `quiet_time` in units of 5ms
*   `wait_timeout`  guards against the 'first' tap of a double/triple tap causing an immediate interrupt
*   `axis` is one of `0`(X), `1`(Y) or `2`(Z, default)
*   see legacy application datasheet for full description

## Motion Detection

#### sigmotion\_enable()

```python
def sigmotion_enable(enable=None)
```

Enable sigmotion detection as required and return status

#### sigmotion\_settings()

```python
def sigmotion_settings(block_time=250)
```

Signifigent motion settings:
*  ` block_time` (trigger delay) in units of 20ms
*   see legacy application datasheet for full description

#### nomotion\_enable()

```python
def nomotion_enable(enable=None)
```

Enable nomotion detection as required and return status

#### nomotion\_settings()

```python
def nomotion_settings(duration=5, threshold=144, axes=0b111)
```

No motion settings:
*   `duration` in units of 20ms
*   `threshold` in units of 0.5mg
*   per-axis select, 3 bits; `x` = bit0, `y` = bit1, `z` = bit2
*   see legacy application datasheet for full description

#### anymotion\_enable()

```python
def anymotion_enable(enable=None)
```

Enable anymotion detection as required and return status

#### anymotion\_settings()

```python
def anymotion_settings(duration=5, threshold=170, axes=0b111)
```

Any motion detection settings:
*   `duration` in units of 20ms
*   `threshold` in units of 0.5mg
*   per-axis select, 3 bits; `x` = bit0, `y` = bit1, `z` = bit2
*   see legacy application datasheet for full description

#### high\_g\_enable()

```python
def high_g_enable(enable=None)
```

Enable high-G detection as required and return status

#### high\_g\_settings()

```python
def high_g_settings(duration=4, hysteresis=1000, threshold=10000, axes=0b111)
```

High G settings:
*   `duration` in units of 20ms
*   per-axis select, 3 bits; `x` = bit0, `y` = bit1, `z` = bit2
*   see legacy application datasheet for full description

#### low\_g\_enable()

```python
def low_g_enable(enable=None)
```

Enable low-G detection as required and return status

#### low\_g\_settings()

```python
def low_g_settings(duration=0, hysteresis=256, threshold=512)
```

Low G settings:
*   `duration` in units of 20ms
*   see legacy application datasheet for full description

## Orientation

#### attributes

```python
ORIENTATIONS = ['portrait_upright', 'landscape_left', 'portrait_upside_down', 'landscape_right']`
```
Defines possible device Orientation values

```python
FACEDIRECTIONS = ['face_down', 'face_up']
```
Defines the Face Up / Face Down states

#### orientation()

```python
def orientation()
```

Returns the orientation and face up/down status as strings
*   See the attributes above

#### orientation\_enable()

```python
def orientation_enable(enable=None)
```

Enable orientation and faceupdown detection and return current status

#### orientation\_settings()

```python
def orientation_settings(mode=0, blocking=3, theta=40, hysteresis=128)
```

Orientation settings, see the application note!
*   `mode` = `0` (normal), `1` (high asymmetric) or `2` (low asymmetric)
*   see legacy application datasheet for full description

#### flat\_enable()

```python
def flat_enable(enable=None)
```

Enable as required and return status

#### flat\_settings()

```python
def flat_settings(hold_time=32, theta=8, hysteresis=9, blocking=2)
```

Flat detection settings:
*   `hold_time` in units of 20ms
*   see legacy application datasheet for full description

## Step and Activity tracking

#### step\_count()

```python
def step_count()
```

Return step counter value as an integer

#### Attribute:
```python
ACTIVITIES = ['still', 'walking', 'running', 'unknown']
```
Defines the possible activity states

#### activity()

```python
def activity()
```

Return current activity status as a string:
*   See the `ACTIVITIES` attribute

#### step\_count\_enable()

```python
def step_count_enable(enable=None)
```

Enable step counting

#### activity\_enable()

```python
def activity_enable(enable=None)
```

Enable activity detection and return current status

#### step\_count\_reset()

```python
def step_count_reset()
```

Reset the step counter to zero

#### step\_settings()

```python
def step_settings(watermark=None)
```

Sets single step detection mode or a watermark for step counting
*   If `watermark` is None, no step interrupts
*   If `watermark` = 0 enable `step_detect` (interrupt on every step)
*   If it is a positive integer disable `step_detect` and flag an interrupt every (`watermark` * 20) steps

