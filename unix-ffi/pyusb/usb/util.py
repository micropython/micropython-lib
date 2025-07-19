# MicroPython USB host library, compatible with PyUSB.
# MIT license; Copyright (c) 2021-2024 Damien P. George

import usb.control


def claim_interface(device, interface):
    device._claim_interface(interface)


def get_string(device, index):
    bs = usb.control.get_descriptor(device, 254, 3, index, 0)
    s = ""
    for i in range(2, bs[0] & 0xFE, 2):
        s += chr(bs[i] | bs[i + 1] << 8)
    return s
