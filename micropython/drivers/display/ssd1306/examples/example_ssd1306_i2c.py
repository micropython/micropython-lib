# MicroPython SSD1306 display via I2C protocol example
#
# This example demonstrates how to configure SSD1306 OLED display
# via I2C protocol.
#
#
# To run this example:
# 1. Connect your SSD1306 display with the microcontroller.
#    (In this example an ESP32 is used with pins: SCL = Pin 22, SDA = Pin 21.
#    Note that IC pin numbering may not map with the board's pin numbers.
#    Please refer the boards datasheet.)
#
# 2. Make sure `ssd1306` is installed via: mpremote mip install ssd1306
#    (Alternatively, you can copy ssd1306.py to your board.)
#
# 3. Run the example via: mpremote run example_ssd1306_i2c.py
#    (You can also copy this file to the board and run it.)
#
# 4. Observe the output on your SSD1306 OLED display.
#
# MIT license; Copyright (c) 2024 Tharuka Pavith.

import ssd1306
from machine import Pin, SoftI2C
from time import sleep_ms, localtime
from micropython import const

# I2C is deprecated. Therefore, use SoftI2C
i2c = SoftI2C(scl=Pin(22), sda=Pin(21))

# SSD1306 OLED display dimensions
WIDTH = const(128)
HEIGHT = const(64)

disp = ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c)  # Create SSD1306 display object

disp.invert(False)  # Toggle this True/False to invert pixels
disp.contrast(20)  # Set contrast

while True:
    yy, mm, dd, hr, mn, sec, *ext = localtime()  # Unpack the localtime tuple
    disp.text("MicroPython", 5, 4)  # Set text starting from x=5, y=4 coordinates
    disp.text(f"Time :{hr}:{mn}:{sec}", 5, 20)  # Set time text
    disp.text(f"Date :{dd}/{mm}/{yy}", 5, 40)  # Set date text
    disp.show()  # Update the display

    sleep_ms(1000)

    disp.fill(0)  # Make all pixels low (depends on inverted or not)
