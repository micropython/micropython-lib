# MicroPython USB Keyboard simple "Hello" example
#
# Simulates a keyboard pressing "H", "e", "l", "l", "o" in sequence, then exits.
#
# To run this example:
#
# 1. Make sure `usb-device-keyboard` is installed via: mpremote mip install usb-device-keyboard
#
# 2. Run the example via: mpremote run keyboard_hello_example.py
#
# 3. mpremote will exit with an error after the previous step, because when the
#    example runs the existing USB device disconnects and then re-enumerates with
#    the keyboard interface present. At this point, the example is running.
#
# 4. The example should stop running after USB has enumerated and it has typed Hello.
#    At this point it will be possible to access the REPL again, but if you re-initialise
#    USB then it will exit with an error again.
#
# For a more complex keyboard example that includes LED support, see keyboard_pin_example.py.
#
# MIT license; Copyright (c) 2026 Angus Gratton
import usb.device
from usb.device.keyboard import KeyboardInterface, KeyCode as KC
import time


def keyboard_example():
    # Sequence to type.
    #
    # See 'class KeyCode' in usb-device-keyboard/usb/device/keyboard.py for
    # the list of key codes
    SEQUENCE = [
        (KC.LEFT_SHIFT, KC.H),
        (KC.E,),
        (KC.L,),
        (KC.L,),
        (KC.O,),
    ]

    # Register the keyboard interface and re-enumerate
    k = KeyboardInterface()
    usb.device.get().init(k, builtin_driver=True)

    print("Waiting for keyboard to enumerate...")
    while not k.is_open():
        time.sleep_ms(100)

    # Give the host a moment to be ready to receive keys (this delay can be shorter on most hosts)
    time.sleep_ms(1000)

    print("Typing sequence...")
    for keys in SEQUENCE:
        # wait for host to process any pending keyboard events
        while k.busy():
            time.sleep_ms(10)

        k.send_keys(keys)
        time.sleep_ms(20)

        # After setting a key code, need to un-set to release the key again.
        # For this example we release all keys by sending an empty
        # tuple of key codes
        k.send_keys(())

        # Add a visible delay between each key
        time.sleep_ms(500)

    print("Done")


keyboard_example()
