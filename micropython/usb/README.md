# USB Drivers

These packages allow implementing USB functionality on a MicroPython system
using pure Python code.

Currently only USB device is implemented, not USB host.

## USB Device support

### Support

USB Device support depends on the low-level
[machine.USBDevice](https://docs.micropython.org/en/latest/library/machine.USBDevice.html)
class. This class is new and not supported on all ports, so please check the
documentation for your MicroPython version. It is possible to implement a USB
device using only the low-level USBDevice class. However, the packages here are
higher level and easier to use.

For more information about how to install packages, or "freeze" them into a
firmware image, consult the [MicroPython documentation on "Package
management"](https://docs.micropython.org/en/latest/reference/packages.html).

### Examples

The [examples/device](examples/device) directory in this repo has a range of
examples. After installing necessary packages, you can download an example and
run it with `mpremote run EXAMPLE_FILENAME.py` ([mpremote
docs](https://docs.micropython.org/en/latest/reference/mpremote.html#mpremote-command-run)).

#### Unexpected serial disconnects

If you normally connect to your MicroPython device over a USB serial port ("USB
CDC"), then running a USB example will disconnect mpremote when the new USB
device configuration activates and the serial port has to temporarily
disconnect. It is likely that mpremote will print an error. The example should
still start running, if necessary then you can reconnect with mpremote and type
Ctrl-B to restore the MicroPython REPL and/or Ctrl-C to stop the running
example.

If you use `mpremote run` again while a different USB device configuration is
already active, then the USB serial port may disconnect immediately before the
example runs. This is because mpremote has to soft-reset MicroPython, and when
the existing USB device is reset then the entire USB port needs to reset. If
this happens, run the same `mpremote run` command again.

We plan to add features to `mpremote` so that this limitation is less
disruptive. Other tools that communicate with MicroPython over the serial port
will encounter similar issues when runtime USB is in use.

### Initialising runtime USB

The overall pattern for enabling USB devices at runtime is:

1. Instantiate the Interface objects for your desired USB device.
2. Call `usb.device.get()` to get the singleton object for the high-level USB device.
3. Call `init(...)` to pass the desired interfaces as arguments, plus any custom
   keyword arguments to configure the overall device.

An example, similar to [mouse_example.py](examples/device/mouse_example.py):

```py
    m = usb.device.mouse.MouseInterface()
    usb.device.get().init(m, builtin_driver=True)
```

Setting `builtin_driver=True` means that any built-in USB serial port will still
be available. Otherwise, you may permanently lose access to MicroPython until
the next time the device resets.

See [Unexpected serial disconnects](#Unexpected-serial-disconnects), above, for
an explanation of possible errors or disconnects when the runtime USB device
initialises.

Placing the call to `usb.device.get().init()` into the `boot.py` of the
MicroPython file system allows the runtime USB device to initialise immediately
on boot, before any built-in USB. This is a feature (not a bug) and allows you
full control over the USB device, for example to only enable USB HID and prevent
REPL access to the system.

However, note that calling this function on boot without `builtin_driver=True`
will make the MicroPython USB serial interface permanently inaccessible until
you "safe mode boot" (on supported boards) or completely erase the flash of your
device.

### Package usb-device

This base package contains the common implementation components for the other
packages, and can be used to implement new and different USB interface support.
All of the other `usb-device-<name>` packages depend on this package, and it
will be automatically installed as needed.

Specicially, this package provides the `usb.device.get()` function for accessing
the Device singleton object, and the `usb.device.core` module which contains the
low-level classes and utility functions for implementing new USB interface
drivers in Python. The best examples of how to use the core classes is the
source code of the other USB device packages.

### Package usb-device-keyboard

This package provides the `usb.device.keyboard` module. See
[keyboard_example.py](examples/device/keyboard_example.py) for an example
program.

### Package usb-device-mouse

This package provides the `usb.device.mouse` module. See
[mouse_example.py](examples/device/mouse_example.py) for an example program.

### Package usb-device-hid

This package provides the `usb.device.hid` module. USB HID (Human Interface
Device) class allows creating a wide variety of device types. The most common
are mouse and keyboard, which have their own packages in micropython-lib.
However, using the usb-device-hid package directly allows creation of any kind
of HID device.

See [hid_custom_keypad_example.py](examples/device/hid_custom_keypad_example.py)
for an example of a Keypad HID device with a custom HID descriptor.

### Package usb-device-cdc

This package provides the `usb.device.cdc` module. USB CDC (Communications
Device Class) is most commonly used for virtual serial port USB interfaces, and
that is what is supported here.

The example [cdc_repl_example.py](examples/device/cdc_repl_example.py)
demonstrates how to add a second USB serial interface and duplicate the
MicroPython REPL between the two.

### Package usb-device-midi

This package provides the `usb.device.midi` module. This allows implementing
USB MIDI devices in MicroPython.

The example [midi_example.py](examples/device/midi_example.py) demonstrates how
to create a simple MIDI device to send MIDI data to and from the USB host.

### Limitations

#### Buffer thread safety

The internal Buffer class that's used by most of the USB device classes expects data
to be written to it (i.e. sent to the host) by only one thread. Bytes may be
lost from the USB transfers if more than one thread (or a thread and a callback)
try to write to the buffer simultaneously.

If writing USB data from multiple sources, your code may need to add
synchronisation (i.e. locks).
