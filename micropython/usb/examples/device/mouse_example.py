# MicroPython USB Mouse example
#
# This example uses the usb-device-mouse package for the MouseInterface class.
# This can be installed with:
#
# mpremote mip install usb-device-mouse
#
# To implement a more complex mouse, copy the
# usb-device-mouse/usb/device/mouse.py file into your own project and modify
# MouseInterface.
#
# MIT license; Copyright (c) 2023-2024 Angus Gratton
import time
import usb.device
from usb.device.mouse import MouseInterface


def mouse_example():
    m = MouseInterface()

    # Note: builtin_driver=True means that if there's a USB-CDC REPL
    # available then it will appear as well as the HID device.
    usb.device.get().init(m, builtin_driver=True)

    # wait for host to enumerate as a HID device...
    while not m.is_open():
        time.sleep_ms(100)

    time.sleep_ms(2000)

    print("Moving...")
    m.move_by(-100, 0)
    m.move_by(-100, 0)
    time.sleep_ms(500)

    print("Clicking...")
    m.click_right(True)
    time.sleep_ms(200)
    m.click_right(False)

    print("Done!")


mouse_example()
