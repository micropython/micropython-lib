"""
Demo of BMI270 Legacy Configuration features

Owen Carter, Jan 2026
"""

from bmi270_legacy import BMI270_LEGACY

from machine import I2C, Pin
from time import sleep_ms, ticks_ms, ticks_diff

# This lets us sense user input in the repl console
from sys import stdin
from select import poll, POLLIN

stdinpoll = poll()
stdinpoll.register(stdin, POLLIN)


def helptxt():
    print(' "p" to pause, "?" for this help, "x" to exit')
    print(' "+" / "-" to increase / decrease frequency')
    print("Enable/Disable Features:")
    print(' "1", "2", "3": single/double/triple tap detection')
    print(' "a": Any motion detection')
    print(' "s": Significant motion detection')
    print(' "n": No motion detection')
    print(' "f": Flat detection')
    print(' "h": High-G detection')
    print(' "l": Low-G detection')
    print(' "v": Activity')
    print(' "c": Step Counting')
    print(' "w": Interrupt every step')
    print(' "W": Interrupt every 40 steps')
    print("Orientation is pre-enabled")
    print(' "o": Orientation')
    print("Device Control:")
    print(' "R" / "r": Dump feature / device registers')
    print(' "!": Reset the device')


def dump_regs():
    """Debug function, use as needed. Gives formatted feature register dump"""
    for register in range(0x80):
        reg = imu._read_reg(register)
        print("0x{0:02X} :: 0b{1:08b} :: 0x{1:02X}".format(register, reg))


def dump_f_regs():
    """Debug function, use as needed. Gives formatted feature register dump"""
    for page in range(8):
        for word in range(8):
            reg = imu._f_read_word(page, word)
            print(
                "{0} 0x{1:02X} :: 0b{2:016b} :: 0x{2:04X}".format(
                    "{}::".format(page) if word == 0 else "   ", 0x30 + (word * 2), reg
                )
            )


def show_data():
    """Dump a dataline with formatted info"""
    interrupts = imu.interrupts()  # get interrupts before status
    orient, face = imu.orientation()
    steps = imu.step_count()
    activity = imu.activity()
    ms = ticks_ms() % 1000
    s = ticks_ms() // 1000
    m = s // 60
    print("{:02d}:{:02d}.{:03d}: ".format(m % 60, s % 60, ms), end="")
    print("{} steps ({}), {} ({})".format(steps, activity, orient, face), end="")
    if "tap" in interrupts:
        interrupts[interrupts.index("tap")] = "tap_{}".format(imu.taps())
    if len(interrupts) != 0:
        print(", Int: {}".format(interrupts), end="")
    print()


def data_loop(freq=float(2)):
    "Simply loop until repl input detected"

    def toggle(enabler):
        return bool(enabler(not enabler(None)))

    paused = False
    taps = []
    start = ticks_ms()
    while True:
        cmd = ""
        while len(stdinpoll.poll(0)) == 0 and ticks_diff(ticks_ms(), start) < (1000 / freq):
            pass
        start = ticks_ms()
        while len(stdinpoll.poll(0)) > 0:
            cmd += stdin.read(1)
        if len(cmd) > 0:
            c = cmd[0]
            show_data()
            if c in ("x", "X"):
                break
            elif c == "?":
                helptxt()
            elif c in ("p", "P"):
                paused = not paused
                print("Paused :: {}".format(paused))
            elif c == "r":
                dump_regs()
            elif c == "R":
                dump_f_regs()
            elif c in ("-", "_"):
                freq = freq / 2
                print("freq- (~{} Hz)".format(freq))
            elif c in ("+", "="):
                freq = min(4096, freq * 2)
                print("freq+ ({} Hz)".format(freq))
            elif c in ("1", "2", "3"):
                if int(c) in taps:
                    taps.remove(int(c))
                else:
                    taps.append(int(c))
                imu.tap_enable(*taps)
                print("Taps set to: {}".format(taps))
            elif c == "o":
                print("Orientation enable: {}".format(toggle(imu.orientation_enable)))
            elif c == "v":
                print("Activity tracking enable: {}".format(toggle(imu.activity_enable)))
            elif c == "c":
                print("Step count enable: {}".format(toggle(imu.step_count_enable)))
            elif c == "w":
                imu.step_settings(watermark=0)
                imu.step_count_reset()
                print("single step detect enabled, counter reset")
            elif c == "W":
                imu.step_settings(watermark=2)
                print("step watermark enabled at 2 (40 steps)")
            elif c == "h":
                print("High G enable: {}".format(toggle(imu.high_g_enable)))
            elif c == "l":
                print("Low G enable: {}".format(toggle(imu.low_g_enable)))
            elif c == "a":
                print("Any motion enable: {}".format(toggle(imu.anymotion_enable)))
            elif c == "s":
                print("Significant motion enable: {}".format(toggle(imu.sigmotion_enable)))
            elif c == "n":
                print("No motion enable: {}".format(toggle(imu.nomotion_enable)))
            elif c == "f":
                print("Flat enable: {}".format(toggle(imu.flat_enable)))
            elif c == "!":
                print("\n## Reset ##\n")
                imu.reset()
                # all settings will be lost; re-apply
                imu.sensor_settings()  # defaults to previous settings..
                imu.feature_interrupt_mask()
                imu.device_interrupt_mask()
        else:
            start = ticks_ms()
            if not paused:
                show_data()


print("Init: ", end="")

# Set up the I2C bus
# - Adjust pins here to suit your system

i2c = I2C(sda=Pin(31), scl=Pin(32))

# The bmi270 defaults to address 0x68
imu_address = 0x68

# Init in I2C mode
imu = BMI270_LEGACY(i2c, address=imu_address)

print(" Complete")

# Inform if device needed a reset and configuration load
if imu.reset_flag:
    print("warning: Device was reset during init")

sleep_ms(100)  # it pays to wait for an initial reading.

# Interrupt setup  (interrupts must be 'unmasked' on at least one pin to flagged)
# Unmask all feature interrupts on both pins
imu.feature_interrupt_mask()
# Unmask device error interrupts on both pins
imu.device_interrupt_mask()

# No electrical signal will be seen on the interrupt output pins
# until they are enabled and drive properties defined
# imu.int1_pin_setup(False)
# imu.int2_pin_setup(False)

# You can change feature report output attributes (eg to use integers, or localize the text)
# imu.ORIENTATIONS = [0, 1, 2, 3]
# imu.FACEDIRECTIONS = [True, False]
# imu.ACTIVITIES= ['stil', 'lopend', 'rennend', 'onbekend']

# make taps more sensitive
imu.tap_settings(sense_threshold=2)

# orientation can be made low asymmetric, and blocking lowered.
# - to understand these options refer to the bmi270-legacy application notes`
imu.orientation_settings(mode=2, blocking=2)

# Show any pending interrupts.
print("\nStartup interrupts: {}".format(imu.interrupts()))

# Enable orientation tracking by default
imu.orientation_enable(True)
# other features will be off (after reset) or in their previous state

# Now start loop
helptxt()
data_loop()
