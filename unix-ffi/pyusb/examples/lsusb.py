# Simple example to list attached USB devices.

import usb.core

for device in usb.core.find(find_all=True):
    print("ID {:04x}:{:04x}".format(device.idVendor, device.idProduct))
    for cfg in device:
        print(
            "  config numitf={} value={} attr={} power={}".format(
                cfg.bNumInterfaces, cfg.bConfigurationValue, cfg.bmAttributes, cfg.bMaxPower
            )
        )
        for itf in cfg:
            print(
                "    interface class={} subclass={}".format(
                    itf.bInterfaceClass, itf.bInterfaceSubClass
                )
            )
