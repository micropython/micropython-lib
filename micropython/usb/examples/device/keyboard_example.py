# MicroPython USB Keyboard example
#
# To run this example:
#
# 1. Check the KEYS assignment below, and connect buttons or switches to the
#    assigned GPIOs. You can change the entries as needed, look up the reference
#    for your board to see what pins are available. Note that the example uses
#    "active low" logic, so pressing a switch or button should switch the
#    connected pin to Ground (0V).
#
# 2. Make sure `usb-device-keyboard` is installed via: mpremote mip install usb-device-keyboard
#
# 3. Run the example via: mpremote run keyboard_example.py
#
# 4. mpremote will exit with an error after the previous step, because when the
#    example runs the existing USB device disconnects and then re-enumerates with
#   the keyboard interface present. At this point, the example is running.
#
# 5. The example doesn't print anything to the serial port, but to stop it first
#    re-connect: mpremote connect PORTNAME
#
# 6. Type Ctrl-C to interrupt the running example and stop it. You may have to
#    also type Ctrl-B to restore the interactive REPL.
#
# To implement a keyboard with different USB HID characteristics, copy the
# usb-device-keyboard/usb/device/keyboard.py file into your own project and modify
# KeyboardInterface.
#
# MIT license; Copyright (c) 2024 Angus Gratton
import usb.device
from usb.device.keyboard import KeyboardInterface, KeyCode, LEDCode
from machine import Pin
import time

# Tuples mapping Pin inputs to the KeyCode each input generates
#
# (Big keyboards usually multiplex multiple keys per input with a scan matrix,
# but this is a simple example.)
KEYS = (
    (Pin.cpu.GPIO10, KeyCode.CAPS_LOCK),
    (Pin.cpu.GPIO11, KeyCode.LEFT_SHIFT),
    (Pin.cpu.GPIO12, KeyCode.M),
    (Pin.cpu.GPIO13, KeyCode.P),
    # ... add more pin to KeyCode mappings here if needed
)

# Tuples mapping Pin outputs to the LEDCode that turns the output on
LEDS = (
    (Pin.board.LED, LEDCode.CAPS_LOCK),
    # ... add more pin to LEDCode mappings here if needed
)


class ExampleKeyboard(KeyboardInterface):
    def on_led_update(self, led_mask):
        # print(hex(led_mask))
        for pin, code in LEDS:
            # Set the pin high if 'code' bit is set in led_mask
            pin(code & led_mask)


def keyboard_example():
    # Initialise all the pins as active-low inputs with pullup resistors
    for pin, _ in KEYS:
        pin.init(Pin.IN, Pin.PULL_UP)

    # Initialise all the LEDs as active-high outputs
    for pin, _ in LEDS:
        pin.init(Pin.OUT, value=0)

    # Register the keyboard interface and re-enumerate
    k = ExampleKeyboard()
    usb.device.get().init(k, builtin_driver=True)

    print("Entering keyboard loop...")

    keys = []  # Keys held down, reuse the same list object
    prev_keys = [None]  # Previous keys, starts with a dummy value so first
    # iteration will always send
    while True:
        if k.is_open():
            keys.clear()
            for pin, code in KEYS:
                if not pin():  # active-low
                    keys.append(code)
            if keys != prev_keys:
                # print(keys)
                k.send_keys(keys)
                prev_keys.clear()
                prev_keys.extend(keys)

        # This simple example scans each input in an infinite loop, but a more
        # complex implementation would probably use a timer or similar.
        time.sleep_ms(1)


keyboard_example()
