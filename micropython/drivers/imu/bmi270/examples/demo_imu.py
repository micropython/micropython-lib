"""
Interactive demo for BMI270 bsic IMU data
- columnar output is easier to read and compare as device moves
- on the fly speed adjustment and pausing
- Numeric / Visual modes
- Powersave modes
"""

from bmi270 import BMI270
# or:
# from bmi270_legacy import BMI270_LEGACY as BMI270

from machine import I2C, Pin
from time import sleep_ms, ticks_ms, ticks_diff

# This lets us sense user input in the repl console
from sys import stdin
from select import poll, POLLIN

stdinpoll = poll()
stdinpoll.register(stdin, POLLIN)

# Set up the I2C bus
# - adjust pins to suit your system
SYS_SDA = 31
SYS_SCL = 32
sys_i2c = I2C(0, sda=Pin(SYS_SDA), scl=Pin(SYS_SCL))

# The bmi270 is on the I2C bus
imu_address = 0x68

print("Init:", end="")
start = ticks_ms()

# Init in I2C mode.
imu = BMI270(sys_i2c, address=imu_address)

duration = ticks_diff(ticks_ms(), start)
print(" Completed in {}ms".format(duration))
if imu.reset_flag:
    print("Device was reset/re-initialised")


def show_help():
    print('"l" / "L" to enable / disable low power mode')
    print('"b" to show visual bars instead of values,')
    print('"+" / "-" to increase / decrease frequency,')
    print('"p" to pause, "?" for help, "x" to exit.\n')


afmt = "> 5.1f"
gfmt = "> 4.0f"


def show_data():
    ms = ticks_ms() % 1000
    s = ticks_ms() // 1000
    m = s // 60
    print("{:02d}:{:02d}.{:03d}".format(m % 60, s % 60, ms), end="")
    print(" | Accel: X={1:{0:}}, Y={2:{0:}}, Z={3:{0:}}".format(afmt, *imu.accel()), end="")
    print(" | Gyro: X={1:{0:}}, Y={2:{0:}}, Z={3:{0:}}".format(gfmt, *imu.gyro()), end="")
    print(" | Temp:{:> 5.1f}°".format(imu.temperature()))


def bar(val, scale, char):
    v = int(val * scale)
    start = min(0, max(-10, v))
    end = max(0, min(10, v))
    return "{}{}{}".format(" " * (10 + start), char * ((end - start) + 1), " " * (10 - end))


afac = 8
gfac = 0.05


def show_bars():
    ms = ticks_ms() % 1000
    s = ticks_ms() // 1000
    m = s // 60
    print("{:02d}:{:02d}.{:03d}".format(m % 60, s % 60, ms), end="")
    x, y, z = imu.accel()
    print(
        " | Accel: {} {} {}".format(bar(x, afac, "X"), bar(y, afac, "Y"), bar(z, afac, "Z")),
        end="",
    )
    x, y, z = imu.gyro()
    print(" | Gyro: {} {} {}".format(bar(x, gfac, "x"), bar(y, gfac, "y"), bar(z, gfac, "z")))


def data_loop(freq=float(8)):
    "Simply loop showing imu data until repl input detected"
    paused = False
    bars = False
    show_help()
    start = ticks_ms()
    while True:
        cmd = ""
        while ticks_diff(ticks_ms(), start) < (1000 / freq) and len(cmd) == 0:
            while len(stdinpoll.poll(0)) > 0:
                cmd += stdin.read(1)
                sleep_ms(50)
        if len(cmd) > 0:
            if cmd[0] in ("x", "X"):
                break
            if cmd[0] in ("?", "h"):
                show_help()
            elif cmd[0] in ("p", "P"):
                paused = not paused
                print("Paused :: {}".format(paused))
            elif cmd[0] in ("-", "_"):
                freq = freq / 2
                print("freq- ({} Hz)".format(freq))
            elif cmd[0] in ("+", "="):
                freq = min(4096, freq * 2)
                print("freq+ ({} Hz)".format(freq))
            elif cmd[0] in ("b", "B"):
                bars = not bars
            elif cmd[0] == "l":
                imu.power(powersave=True)
                print("Advanced PowerSave enabled")
            elif cmd[0] == "L":
                imu.power(powersave=False)
                print("Advanced PowerSave disabled")
        if not paused:
            if bars:
                show_bars()
            else:
                show_data()
        start = ticks_ms()


# Run the main data loop
data_loop()
