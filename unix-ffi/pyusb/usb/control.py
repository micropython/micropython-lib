# MicroPython USB host library, compatible with PyUSB.
# MIT license; Copyright (c) 2021-2024 Damien P. George


def get_descriptor(dev, desc_size, desc_type, desc_index, wIndex=0):
    wValue = desc_index | desc_type << 8
    d = dev.ctrl_transfer(0x80, 0x06, wValue, wIndex, desc_size)
    if len(d) < 2:
        raise Exception("invalid descriptor")
    return d
