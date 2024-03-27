# MicroPython USB HID custom Keypad example
#
# This example demonstrates creating a custom HID device with its own
# HID descriptor, in this case for a USB number keypad.
#
# For higher level examples that require less code to use, see mouse_example.py
# and keyboard_example.py
#
# To run this example:
#
# 1. Make sure `usb-device-hid` is installed via: mpremote mip install usb-device-hid
#
# 2. Run the example via: mpremote run hid_custom_keypad_example.py
#
# 3. mpremote will exit with an error after the previous step, because when the
#    example runs the existing USB device disconnects and then re-enumerates with
#    the custom HID interface present. At this point, the example is running.
#
# 4. To see output from the example, re-connect: mpremote connect PORTNAME
#
# MIT license; Copyright (c) 2023 Dave Wickham, 2023-2024 Angus Gratton
from micropython import const
import time
import usb.device
from usb.device.hid import HIDInterface

_INTERFACE_PROTOCOL_KEYBOARD = const(0x01)


def keypad_example():
    k = KeypadInterface()

    usb.device.get().init(k, builtin_driver=True)

    while not k.is_open():
        time.sleep_ms(100)

    while True:
        time.sleep(2)
        print("Press NumLock...")
        k.send_key("<NumLock>")
        time.sleep_ms(100)
        k.send_key()
        time.sleep(1)
        # continue
        print("Press ...")
        for _ in range(3):
            time.sleep(0.1)
            k.send_key(".")
            time.sleep(0.1)
            k.send_key()
        print("Starting again...")


class KeypadInterface(HIDInterface):
    # Very basic synchronous USB keypad HID interface

    def __init__(self):
        super().__init__(
            _KEYPAD_REPORT_DESC,
            set_report_buf=bytearray(1),
            protocol=_INTERFACE_PROTOCOL_KEYBOARD,
            interface_str="MicroPython Keypad",
        )
        self.numlock = False

    def on_set_report(self, report_data, _report_id, _report_type):
        report = report_data[0]
        b = bool(report & 1)
        if b != self.numlock:
            print("Numlock: ", b)
            self.numlock = b

    def send_key(self, key=None):
        if key is None:
            self.send_report(b"\x00")
        else:
            self.send_report(_key_to_id(key).to_bytes(1, "big"))


# See HID Usages and Descriptions 1.4, section 10 Keyboard/Keypad Page (0x07)
#
# This keypad example has a contiguous series of keys (KEYPAD_KEY_IDS) starting
# from the NumLock/Clear keypad key (0x53), but you can send any Key IDs from
# the table in the HID Usages specification.
_KEYPAD_KEY_OFFS = const(0x53)

_KEYPAD_KEY_IDS = [
    "<NumLock>",
    "/",
    "*",
    "-",
    "+",
    "<Enter>",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "0",
    ".",
]


def _key_to_id(key):
    # This is a little slower than making a dict for lookup, but uses
    # less memory and O(n) can be fast enough when n is small.
    return _KEYPAD_KEY_IDS.index(key) + _KEYPAD_KEY_OFFS


# HID Report descriptor for a numeric keypad
#
# fmt: off
_KEYPAD_REPORT_DESC = (
    b'\x05\x01'  # Usage Page (Generic Desktop)
        b'\x09\x07'  # Usage (Keypad)
    b'\xA1\x01'  # Collection (Application)
        b'\x05\x07'  # Usage Page (Keypad)
            b'\x19\x00'  # Usage Minimum (0)
            b'\x29\xFF'  # Usage Maximum (ff)
            b'\x15\x00'  # Logical Minimum (0)
            b'\x25\xFF'  # Logical Maximum (ff)
            b'\x95\x01'  # Report Count (1),
            b'\x75\x08'  # Report Size (8),
            b'\x81\x00'  # Input (Data, Array, Absolute)
        b'\x05\x08'  # Usage page (LEDs)
            b'\x19\x01'  # Usage Minimum (1)
            b'\x29\x01'  # Usage Maximum (1),
            b'\x95\x01'  # Report Count (1),
            b'\x75\x01'  # Report Size (1),
            b'\x91\x02'  # Output (Data, Variable, Absolute)
            b'\x95\x01'  # Report Count (1),
            b'\x75\x07'  # Report Size (7),
            b'\x91\x01'  # Output (Constant) - padding bits
    b'\xC0'  # End Collection
)
# fmt: on


keypad_example()
