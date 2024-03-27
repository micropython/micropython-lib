# MicroPython USB Mouse module
#
# MIT license; Copyright (c) 2023-2024 Angus Gratton
from micropython import const
import struct

from usb.device.hid import HIDInterface

_INTERFACE_PROTOCOL_MOUSE = const(0x02)


class MouseInterface(HIDInterface):
    # A basic three button USB mouse HID interface
    def __init__(self, interface_str="MicroPython Mouse"):
        super().__init__(
            _MOUSE_REPORT_DESC,
            protocol=_INTERFACE_PROTOCOL_MOUSE,
            interface_str=interface_str,
        )
        self._l = False  # Left button
        self._m = False  # Middle button
        self._r = False  # Right button

    def send_report(self, dx=0, dy=0):
        b = 0
        if self._l:
            b |= 1 << 0
        if self._r:
            b |= 1 << 1
        if self._m:
            b |= 1 << 2
        # Note: This allocates the bytes object 'report' each time a report is
        # sent.
        #
        # However, at the moment the HIDInterface class doesn't keep track of each
        # transfer after it's submitted. So reusing a bytearray() creates a risk
        # of a race condition if a new report transfer is submitted using the
        # same buffer, before the previous one has completed.
        report = struct.pack("Bbb", b, dx, dy)

        super().send_report(report)

    def click_left(self, down=True):
        self._l = down
        self.send_report()

    def click_middle(self, down=True):
        self._m = down
        self.send_report()

    def click_right(self, down=True):
        self._r = down
        self.send_report()

    def move_by(self, dx, dy):
        if not -127 <= dx <= 127:
            raise ValueError("dx")
        if not -127 <= dy <= 127:
            raise ValueError("dy")
        self.send_report(dx, dy)


# Basic 3-button mouse HID Report Descriptor.
# This is cribbed from Appendix E.10 of the HID v1.11 document.
_MOUSE_REPORT_DESC = bytes(
    [
        0x05,
        0x01,  # Usage Page (Generic Desktop)
        0x09,
        0x02,  # Usage (Mouse)
        0xA1,
        0x01,  # Collection (Application)
        0x09,
        0x01,  # Usage (Pointer)
        0xA1,
        0x00,  # Collection (Physical)
        0x05,
        0x09,  # Usage Page (Buttons)
        0x19,
        0x01,  # Usage Minimum (01),
        0x29,
        0x03,  # Usage Maximun (03),
        0x15,
        0x00,  # Logical Minimum (0),
        0x25,
        0x01,  # Logical Maximum (1),
        0x95,
        0x03,  # Report Count (3),
        0x75,
        0x01,  # Report Size (1),
        0x81,
        0x02,  # Input (Data, Variable, Absolute), ;3 button bits
        0x95,
        0x01,  # Report Count (1),
        0x75,
        0x05,  # Report Size (5),
        0x81,
        0x01,  # Input (Constant), ;5 bit padding
        0x05,
        0x01,  # Usage Page (Generic Desktop),
        0x09,
        0x30,  # Usage (X),
        0x09,
        0x31,  # Usage (Y),
        0x15,
        0x81,  # Logical Minimum (-127),
        0x25,
        0x7F,  # Logical Maximum (127),
        0x75,
        0x08,  # Report Size (8),
        0x95,
        0x02,  # Report Count (2),
        0x81,
        0x06,  # Input (Data, Variable, Relative), ;2 position bytes (X & Y)
        0xC0,  # End Collection,
        0xC0,  # End Collection
    ]
)
