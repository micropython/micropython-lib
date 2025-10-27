# MicroPython USB CDC REPL example
#
# Example demonstrating how to use os.dupterm() to provide the
# MicroPython REPL on a dynamic CDCInterface() serial port.
#
# To run this example:
#
# 1. Make sure `usb-device-cdc` is installed via: mpremote mip install usb-device-cdc
#
# 2. Run the example via: mpremote run cdc_repl_example.py
#
# 3. mpremote will exit with an error after the previous step, because when the
#    example runs the existing USB device disconnects and then re-enumerates with
#    the second serial port. If you check (for example by running mpremote connect
#    list) then you should now see two USB serial devices.
#
# 4. Connect to one of the new ports: mpremote connect PORTNAME
#
#    It may be necessary to type Ctrl-B to exit the raw REPL mode and resume the
#    interactive REPL after mpremote connects.
#
# MIT license; Copyright (c) 2023-2024 Angus Gratton
import os
import time
import usb.device
from usb.device.cdc import CDCInterface

cdc = CDCInterface()
cdc.init(timeout=0)  # zero timeout makes this non-blocking, suitable for os.dupterm()

# pass builtin_driver=True so that we get the built-in USB-CDC alongside,
# if it's available.
usb.device.get().init(cdc, builtin_driver=True)

print("Waiting for USB host to configure the interface...")

# wait for host enumerate as a CDC device...
while not cdc.is_open():
    time.sleep_ms(100)

# Note: This example doesn't wait for the host to access the new CDC port,
# which could be done by polling cdc.dtr, as this will block the REPL
# from resuming while this code is still executing.

print("CDC port enumerated, duplicating REPL...")

old_term = os.dupterm(cdc)
