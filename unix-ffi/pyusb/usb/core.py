# MicroPython USB host library, compatible with PyUSB.
# MIT license; Copyright (c) 2021-2024 Damien P. George

import sys
import ffi
import uctypes

if sys.maxsize >> 32:
    UINTPTR_SIZE = 8
    UINTPTR = uctypes.UINT64
else:
    UINTPTR_SIZE = 4
    UINTPTR = uctypes.UINT32


def _align_word(x):
    return (x + UINTPTR_SIZE - 1) & ~(UINTPTR_SIZE - 1)


ptr_descriptor = (0 | uctypes.ARRAY, 1 | UINTPTR)

libusb_device_descriptor = {
    "bLength": 0 | uctypes.UINT8,
    "bDescriptorType": 1 | uctypes.UINT8,
    "bcdUSB": 2 | uctypes.UINT16,
    "bDeviceClass": 4 | uctypes.UINT8,
    "bDeviceSubClass": 5 | uctypes.UINT8,
    "bDeviceProtocol": 6 | uctypes.UINT8,
    "bMaxPacketSize0": 7 | uctypes.UINT8,
    "idVendor": 8 | uctypes.UINT16,
    "idProduct": 10 | uctypes.UINT16,
    "bcdDevice": 12 | uctypes.UINT16,
    "iManufacturer": 14 | uctypes.UINT8,
    "iProduct": 15 | uctypes.UINT8,
    "iSerialNumber": 16 | uctypes.UINT8,
    "bNumConfigurations": 17 | uctypes.UINT8,
}

libusb_config_descriptor = {
    "bLength": 0 | uctypes.UINT8,
    "bDescriptorType": 1 | uctypes.UINT8,
    "wTotalLength": 2 | uctypes.UINT16,
    "bNumInterfaces": 4 | uctypes.UINT8,
    "bConfigurationValue": 5 | uctypes.UINT8,
    "iConfiguration": 6 | uctypes.UINT8,
    "bmAttributes": 7 | uctypes.UINT8,
    "MaxPower": 8 | uctypes.UINT8,
    "interface": _align_word(9) | UINTPTR,  # array of libusb_interface
    "extra": (_align_word(9) + UINTPTR_SIZE) | UINTPTR,
    "extra_length": (_align_word(9) + 2 * UINTPTR_SIZE) | uctypes.INT,
}

libusb_interface = {
    "altsetting": 0 | UINTPTR,  # array of libusb_interface_descriptor
    "num_altsetting": UINTPTR_SIZE | uctypes.INT,
}

libusb_interface_descriptor = {
    "bLength": 0 | uctypes.UINT8,
    "bDescriptorType": 1 | uctypes.UINT8,
    "bInterfaceNumber": 2 | uctypes.UINT8,
    "bAlternateSetting": 3 | uctypes.UINT8,
    "bNumEndpoints": 4 | uctypes.UINT8,
    "bInterfaceClass": 5 | uctypes.UINT8,
    "bInterfaceSubClass": 6 | uctypes.UINT8,
    "bInterfaceProtocol": 7 | uctypes.UINT8,
    "iInterface": 8 | uctypes.UINT8,
    "endpoint": _align_word(9) | UINTPTR,
    "extra": (_align_word(9) + UINTPTR_SIZE) | UINTPTR,
    "extra_length": (_align_word(9) + 2 * UINTPTR_SIZE) | uctypes.INT,
}

libusb = ffi.open("libusb-1.0.so")
libusb_init = libusb.func("i", "libusb_init", "p")
libusb_exit = libusb.func("v", "libusb_exit", "p")
libusb_get_device_list = libusb.func("i", "libusb_get_device_list", "pp")  # return is ssize_t
libusb_free_device_list = libusb.func("v", "libusb_free_device_list", "pi")
libusb_get_device_descriptor = libusb.func("i", "libusb_get_device_descriptor", "pp")
libusb_get_config_descriptor = libusb.func("i", "libusb_get_config_descriptor", "pBp")
libusb_free_config_descriptor = libusb.func("v", "libusb_free_config_descriptor", "p")
libusb_open = libusb.func("i", "libusb_open", "pp")
libusb_set_configuration = libusb.func("i", "libusb_set_configuration", "pi")
libusb_claim_interface = libusb.func("i", "libusb_claim_interface", "pi")
libusb_control_transfer = libusb.func("i", "libusb_control_transfer", "pBBHHpHI")


def _new(sdesc):
    buf = bytearray(uctypes.sizeof(sdesc))
    s = uctypes.struct(uctypes.addressof(buf), sdesc)
    return s


class Interface:
    def __init__(self, descr):
        # Public attributes.
        self.bInterfaceClass = descr.bInterfaceClass
        self.bInterfaceSubClass = descr.bInterfaceSubClass
        self.iInterface = descr.iInterface
        self.extra_descriptors = uctypes.bytes_at(descr.extra, descr.extra_length)


class Configuration:
    def __init__(self, dev, cfg_idx):
        cfgs = _new(ptr_descriptor)
        if libusb_get_config_descriptor(dev._dev, cfg_idx, cfgs) != 0:
            libusb_exit(0)
            raise Exception
        descr = uctypes.struct(cfgs[0], libusb_config_descriptor)

        # Extract all needed info because descr is going to be free'd at the end.
        self._itfs = []
        itf_array = uctypes.struct(
            descr.interface, (0 | uctypes.ARRAY, descr.bNumInterfaces, libusb_interface)
        )
        for i in range(descr.bNumInterfaces):
            itf = itf_array[i]
            alt_array = uctypes.struct(
                itf.altsetting,
                (0 | uctypes.ARRAY, itf.num_altsetting, libusb_interface_descriptor),
            )
            for j in range(itf.num_altsetting):
                alt = alt_array[j]
                self._itfs.append(Interface(alt))

        # Public attributes.
        self.bNumInterfaces = descr.bNumInterfaces
        self.bConfigurationValue = descr.bConfigurationValue
        self.bmAttributes = descr.bmAttributes
        self.bMaxPower = descr.MaxPower
        self.extra_descriptors = uctypes.bytes_at(descr.extra, descr.extra_length)

        # Free descr memory in the driver.
        libusb_free_config_descriptor(cfgs[0])

    def __iter__(self):
        return iter(self._itfs)


class Device:
    _TIMEOUT_DEFAULT = 1000

    def __init__(self, dev, descr):
        self._dev = dev
        self._num_cfg = descr.bNumConfigurations
        self._handle = None
        self._claim_itf = set()

        # Public attributes.
        self.idVendor = descr.idVendor
        self.idProduct = descr.idProduct

    def __iter__(self):
        for i in range(self._num_cfg):
            yield Configuration(self, i)

    def __getitem__(self, i):
        return Configuration(self, i)

    def _open(self):
        if self._handle is None:
            # Open the USB device.
            handle = _new(ptr_descriptor)
            if libusb_open(self._dev, handle) != 0:
                libusb_exit(0)
                raise Exception
            self._handle = handle[0]

    def _claim_interface(self, i):
        if libusb_claim_interface(self._handle, i) != 0:
            libusb_exit(0)
            raise Exception

    def set_configuration(self):
        # Select default configuration.
        self._open()
        cfg = Configuration(self, 0).bConfigurationValue
        ret = libusb_set_configuration(self._handle, cfg)
        if ret != 0:
            libusb_exit(0)
            raise Exception

    def ctrl_transfer(
        self, bmRequestType, bRequest, wValue=0, wIndex=0, data_or_wLength=None, timeout=None
    ):
        if data_or_wLength is None:
            l = 0
            data = bytes()
        elif isinstance(data_or_wLength, int):
            l = data_or_wLength
            data = bytearray(l)
        else:
            l = len(data_or_wLength)
            data = data_or_wLength
        self._open()
        if wIndex & 0xFF not in self._claim_itf:
            self._claim_interface(wIndex & 0xFF)
            self._claim_itf.add(wIndex & 0xFF)
        if timeout is None:
            timeout = self._TIMEOUT_DEFAULT
        ret = libusb_control_transfer(
            self._handle, bmRequestType, bRequest, wValue, wIndex, data, l, timeout * 1000
        )
        if ret < 0:
            libusb_exit(0)
            raise Exception
        if isinstance(data_or_wLength, int):
            return data
        else:
            return ret


def find(*, find_all=False, custom_match=None, idVendor=None, idProduct=None):
    if libusb_init(0) < 0:
        raise Exception

    devs = _new(ptr_descriptor)
    count = libusb_get_device_list(0, devs)
    if count < 0:
        libusb_exit(0)
        raise Exception

    dev_array = uctypes.struct(devs[0], (0 | uctypes.ARRAY, count | UINTPTR))
    descr = _new(libusb_device_descriptor)
    devices = None
    for i in range(count):
        libusb_get_device_descriptor(dev_array[i], descr)
        if idVendor and descr.idVendor != idVendor:
            continue
        if idProduct and descr.idProduct != idProduct:
            continue
        device = Device(dev_array[i], descr)
        if custom_match and not custom_match(device):
            continue
        if not find_all:
            return device
        if not devices:
            devices = []
        devices.append(device)
    return devices
