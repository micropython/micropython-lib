# MicroPython USB MIDI example
#
# This example demonstrates creating a custom MIDI device.
#
# To run this example:
#
# 1. Make sure `usb-device-midi` is installed via: mpremote mip install usb-device-midi
#
# 2. Run the example via: mpremote run midi_example.py
#
# 3. mpremote will exit with an error after the previous step, because when the
#    example runs the existing USB device disconnects and then re-enumerates with
#    the MIDI interface present. At this point, the example is running.
#
# 4. To see output from the example, re-connect: mpremote connect PORTNAME
#
#
# MIT license; Copyright (c) 2023-2024 Angus Gratton
import usb.device
from usb.device.midi import MIDIInterface
import time


class MIDIExample(MIDIInterface):
    # Very simple example event handler functions, showing how to receive note
    # and control change messages sent from the host to the device.
    #
    # If you need to send MIDI data to the host, then it's fine to instantiate
    # MIDIInterface class directly.

    def on_open(self):
        super().on_open()
        print("Device opened by host")

    def on_note_on(self, channel, pitch, vel):
        print(f"RX Note On channel {channel} pitch {pitch} velocity {vel}")

    def on_note_off(self, channel, pitch, vel):
        print(f"RX Note Off channel {channel} pitch {pitch} velocity {vel}")

    def on_control_change(self, channel, controller, value):
        print(f"RX Control channel {channel} controller {controller} value {value}")


m = MIDIExample()
# Remove builtin_driver=True if you don't want the MicroPython serial REPL available.
usb.device.get().init(m, builtin_driver=True)

print("Waiting for USB host to configure the interface...")

while not m.is_open():
    time.sleep_ms(100)

print("Starting MIDI loop...")

# TX constants
CHANNEL = 0
PITCH = 60
CONTROLLER = 64

control_val = 0

while m.is_open():
    time.sleep(1)
    print(f"TX Note On channel {CHANNEL} pitch {PITCH}")
    m.note_on(CHANNEL, PITCH)  # Velocity is an optional third argument
    time.sleep(0.5)
    print(f"TX Note Off channel {CHANNEL} pitch {PITCH}")
    m.note_off(CHANNEL, PITCH)
    time.sleep(1)
    print(f"TX Control channel {CHANNEL} controller {CONTROLLER} value {control_val}")
    m.control_change(CHANNEL, CONTROLLER, control_val)
    control_val += 1
    if control_val == 0x7F:
        control_val = 0
    time.sleep(1)

print("USB host has reset device, example done.")
