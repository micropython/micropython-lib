"""
LSM6DSOX IMU Pedometer Example.

This example demonstrates how to use the built-in pedometer feature of the LSM6DSOX IMU.
The pedometer counts the number of steps taken based on the accelerometer data
and can generate interrupts when a step is detected.

Copyright (C) Arduino s.r.l. and/or its affiliated companies
"""

import time
from lsm6dsox import LSM6DSOX

from machine import Pin, I2C

lsm = LSM6DSOX(I2C(0))
# Or init in SPI mode.
# lsm = LSM6DSOX(SPI(5), cs=Pin(10))

# Enable the pedometer feature, set debounce steps to 5, and enable interrupts on both INT1 and INT2.
# Default debounce steps is 10. This means that after a step is detected, the pedometer
# will ignore any new steps for the next 5 step detections. This can help to filter out
# false positives and improve step counting accuracy.
# If you just want to enable the pedometer, simply call lsm.pedometer_config(enable=True).
lsm.pedometer_config(debounce=5, int1_enable=True, int2_enable=True)

# Register interrupt handler on a Pin. e.g. D8
# The interrupt pins are push-pull outputs by default that go low when a step is detected.
# You can connect either INT1 or INT2 to the interrupt pin.
interrupt_pin = Pin("D8", Pin.IN)  # Change this to your desired interrupt pin.
interrupt_fired = False  # Flag to indicate if the interrupt has been fired.


def on_step_detected(pin):
    global interrupt_fired
    interrupt_fired = True


# Configure the interrupt pin to trigger on falling edge (active low) when a step is detected.
interrupt_pin.irq(trigger=Pin.IRQ_FALLING, handler=on_step_detected)

last_steps = None  # Keep track of the last step count to detect changes.

while True:
    if interrupt_fired:
        print("Step detected!")
        interrupt_fired = False  # Reset the flag after handling the interrupt.

    steps = lsm.steps()

    if steps != last_steps:
        print(f"Steps: {steps}")
        last_steps = steps

    time.sleep_ms(100)
