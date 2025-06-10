# SD card setup

from machine import SPI, Pin, freq

freq(120_000_000)
print("freq:", freq())

import os
from sdcard import SDCard
import time

# the bus spi1 on these  pins on my test card

# I have cs on GP13 for this one
spi = SPI(1, 24_000_000, sck=Pin(14), mosi=Pin(15), miso=Pin(12))
spi.init()  # Ensure right baudrate

from crc16 import crc16

sd = SDCard(spi=spi, cs=Pin(13, Pin.OUT), baudrate=24_000_000, crc16_function=None)
vfs = os.VfsFat(sd)
os.mount(vfs, "/fc")


def sdtest():
    print("Filesystem check")
    print(os.listdir("/fc"))

    line = "abcdefghijklmnopqrstuvwxyz\n"
    lines = line * 200  # 5400 chars
    short = "1234567890\n"

    fn = "/fc/rats.txt"
    print()
    print("Multiple block read/write")
    loops = 1000
    t0 = time.ticks_ms()
    with open(fn, "w") as f:
        n = f.write(lines)
        print(n, "bytes written")
        n = f.write(short)
        print(n, "bytes written")
        for i in range(loops):
            n = f.write(lines)

    nbytes = loops * len(lines) + len(lines) + len(short)
    rate = 1000 * nbytes / time.ticks_diff(time.ticks_ms(), t0)
    print(nbytes, "bytes written at ", rate / 1e6, "MB/s")

    stat = os.stat(fn)
    filesize = stat[6]
    total = 0
    t0 = time.ticks_ms()

    readbuf = bytearray(8192)
    import uctypes

    with open(fn, "rb") as f:
        f.readinto(readbuf)
        big_readback = readbuf[: len(lines)]  # check a big chunk of data

    with open(fn, "rb") as f:
        while (count := f.readinto(readbuf)) != 0:
            total += count

    rate = 1000 * total / time.ticks_diff(time.ticks_ms(), t0)

    print("final file size", filesize, "expected", nbytes, "read", total, "rate=", rate / 1e6)

    fn = "/fc/rats1.txt"
    print()
    print("Single block read/write")
    with open(fn, "w") as f:
        n = f.write(short)  # one block
        print(n, "bytes written")

    with open(fn, "r") as f:
        result2 = f.read()
        print(len(result2), "bytes read")

    print()
    print("Verifying data read back")
    success = True
    if result2 == short:
        print("Small file Pass")
    else:
        print("Small file Fail")
        success = False
    if big_readback == lines:
        print("Big read Pass")
    else:
        print("Big readFail")
        success = False

    print()
    print("Tests", "passed" if success else "failed")


sdtest()

os.umount("/fc")
