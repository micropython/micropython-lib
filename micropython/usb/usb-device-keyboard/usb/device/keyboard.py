# MIT license; Copyright (c) 2023-2024 Angus Gratton
from micropython import const
import time
import usb.device
from usb.device.hid import HIDInterface

_INTERFACE_PROTOCOL_KEYBOARD = const(0x01)

_KEY_ARRAY_LEN = const(6)  # Size of HID key array, must match report descriptor
_KEY_REPORT_LEN = const(_KEY_ARRAY_LEN + 2)  # Modifier Byte + Reserved Byte + Array entries


class KeyboardInterface(HIDInterface):
    # Synchronous USB keyboard HID interface

    def __init__(self):
        super().__init__(
            _KEYBOARD_REPORT_DESC,
            set_report_buf=bytearray(1),
            protocol=_INTERFACE_PROTOCOL_KEYBOARD,
            interface_str="MicroPython Keyboard",
        )
        self._key_reports = [
            bytearray(_KEY_REPORT_LEN),
            bytearray(_KEY_REPORT_LEN),
        ]  # Ping/pong report buffers
        self.numlock = False

    def on_set_report(self, report_data, _report_id, _report_type):
        self.on_led_update(report_data[0])

    def on_led_update(self, led_mask):
        # Override to handle keyboard LED updates. led_mask is bitwise ORed
        # together values as defined in LEDCode.
        pass

    def send_keys(self, down_keys, timeout_ms=100):
        # Update the state of the keyboard by sending a report with down_keys
        # set, where down_keys is an iterable (list or similar) of integer
        # values such as the values defined in KeyCode.
        #
        # Will block for up to timeout_ms if a previous report is still
        # pending to be sent to the host. Returns True on success.

        r, s = self._key_reports  # next report buffer to send, spare report buffer
        r[0] = 0  # modifier byte
        i = 2  # index for next key array item to write to
        for k in down_keys:
            if k < 0:  # Modifier key
                r[0] |= -k
            elif i < _KEY_REPORT_LEN:
                r[i] = k
                i += 1
            else:  # Excess rollover! Can't report
                r[0] = 0
                for i in range(2, _KEY_REPORT_LEN):
                    r[i] = 0xFF
                break

        while i < _KEY_REPORT_LEN:
            r[i] = 0
            i += 1

        if self.send_report(r, timeout_ms):
            # Swap buffers if the previous one is newly queued to send, so
            # any subsequent call can't modify that buffer mid-send
            self._key_reports[0] = s
            self._key_reports[1] = r
            return True
        return False


# HID keyboard report descriptor
#
# From p69 of http://www.usb.org/developers/devclass_docs/HID1_11.pdf
#
# fmt: off
_KEYBOARD_REPORT_DESC = (
    b'\x05\x01'     # Usage Page (Generic Desktop),
        b'\x09\x06'     # Usage (Keyboard),
    b'\xA1\x01'     # Collection (Application),
        b'\x05\x07'         # Usage Page (Key Codes);
            b'\x19\xE0'         # Usage Minimum (224),
            b'\x29\xE7'         # Usage Maximum (231),
            b'\x15\x00'         # Logical Minimum (0),
            b'\x25\x01'         # Logical Maximum (1),
            b'\x75\x01'         # Report Size (1),
            b'\x95\x08'         # Report Count (8),
            b'\x81\x02'         # Input (Data, Variable, Absolute), ;Modifier byte
            b'\x95\x01'         # Report Count (1),
            b'\x75\x08'         # Report Size (8),
            b'\x81\x01'         # Input (Constant), ;Reserved byte
            b'\x95\x05'         # Report Count (5),
            b'\x75\x01'         # Report Size (1),
        b'\x05\x08'         # Usage Page (Page# for LEDs),
            b'\x19\x01'         # Usage Minimum (1),
            b'\x29\x05'         # Usage Maximum (5),
            b'\x91\x02'         # Output (Data, Variable, Absolute), ;LED report
            b'\x95\x01'         # Report Count (1),
            b'\x75\x03'         # Report Size (3),
            b'\x91\x01'         # Output (Constant), ;LED report padding
            b'\x95\x06'         # Report Count (6),
            b'\x75\x08'         # Report Size (8),
            b'\x15\x00'         # Logical Minimum (0),
            b'\x25\x65'         # Logical Maximum(101),
        b'\x05\x07'         # Usage Page (Key Codes),
            b'\x19\x00'         # Usage Minimum (0),
            b'\x29\x65'         # Usage Maximum (101),
            b'\x81\x00'         # Input (Data, Array), ;Key arrays (6 bytes)
    b'\xC0'     # End Collection
)
# fmt: on


# Standard HID keycodes, as a pseudo-enum class for easy access
#
# Modifier keys are encoded as negative values
class KeyCode:
    A = 4
    B = 5
    C = 6
    D = 7
    E = 8
    F = 9
    G = 10
    H = 11
    I = 12
    J = 13
    K = 14
    L = 15
    M = 16
    N = 17
    O = 18
    P = 19
    Q = 20
    R = 21
    S = 22
    T = 23
    U = 24
    V = 25
    W = 26
    X = 27
    Y = 28
    Z = 29
    N1 = 30  # Standard number row keys
    N2 = 31
    N3 = 32
    N4 = 33
    N5 = 34
    N6 = 35
    N7 = 36
    N8 = 37
    N9 = 38
    N0 = 39
    ENTER = 40
    ESCAPE = 41
    BACKSPACE = 42
    TAB = 43
    SPACE = 44
    MINUS = 45  # - _
    EQUAL = 46  # = +
    OPEN_BRACKET = 47  # [ {
    CLOSE_BRACKET = 48  # ] }
    BACKSLASH = 49  # \ |
    HASH = 50  # # ~
    SEMICOLON = 51  # ; :
    QUOTE = 52  # ' "
    GRAVE = 53  # ` ~
    COMMA = 54  # , <
    DOT = 55  # . >
    SLASH = 56  # / ?
    CAPS_LOCK = 57
    F1 = 58
    F2 = 59
    F3 = 60
    F4 = 61
    F5 = 62
    F6 = 63
    F7 = 64
    F8 = 65
    F9 = 66
    F10 = 67
    F11 = 68
    F12 = 69
    PRINTSCREEN = 70
    SCROLL_LOCK = 71
    PAUSE = 72
    INSERT = 73
    HOME = 74
    PAGEUP = 75
    DELETE = 76
    END = 77
    PAGEDOWN = 78
    RIGHT = 79  # Arrow keys
    LEFT = 80
    DOWN = 81
    UP = 82
    KP_NUM_LOCK = 83
    KP_DIVIDE = 84
    KP_AT = 85
    KP_MULTIPLY = 85
    KP_MINUS = 86
    KP_PLUS = 87
    KP_ENTER = 88
    KP_1 = 89
    KP_2 = 90
    KP_3 = 91
    KP_4 = 92
    KP_5 = 93
    KP_6 = 94
    KP_7 = 95
    KP_8 = 96
    KP_9 = 97
    KP_0 = 98

    # HID modifier values (negated to allow them to be passed along with the normal keys)
    LEFT_CTRL = -0x01
    LEFT_SHIFT = -0x02
    LEFT_ALT = -0x04
    LEFT_UI = -0x08
    RIGHT_CTRL = -0x10
    RIGHT_SHIFT = -0x20
    RIGHT_ALT = -0x40
    RIGHT_UI = -0x80


# HID LED values
class LEDCode:
    NUM_LOCK = 0x01
    CAPS_LOCK = 0x02
    SCROLL_LOCK = 0x04
    COMPOSE = 0x08
    KANA = 0x10
