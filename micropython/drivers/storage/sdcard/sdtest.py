# Test for sdcard block protocol
# Peter hinch 30th Jan 2016
import machine
import os
import sdcard


def sdtest():
    """this test requires specific hardware, so is not run by CI"""
    spi = machine.SPI(1)
    spi.init()  # Ensure right baudrate
    sd = sdcard.SDCard(spi, machine.Pin.board.X21)  # Compatible with PCB
    vfs = os.VfsFat(sd)
    os.mount(vfs, "/fc")
    print("Filesystem check")
    print(os.listdir("/fc"))

    line = "abcdefghijklmnopqrstuvwxyz\n"
    lines = line * 200  # 5400 chars
    short = "1234567890\n"

    fn = "/fc/rats.txt"
    print()
    print("Multiple block read/write")
    with open(fn, "w") as f:
        n = f.write(lines)
        print(n, "bytes written")
        n = f.write(short)
        print(n, "bytes written")
        n = f.write(lines)
        print(n, "bytes written")

    with open(fn, "r") as f:
        result1 = f.read()
        print(len(result1), "bytes read")

    fn = "/fc/rats1.txt"
    print()
    print("Single block read/write")
    with open(fn, "w") as f:
        n = f.write(short)  # one block
        print(n, "bytes written")

    with open(fn, "r") as f:
        result2 = f.read()
        print(len(result2), "bytes read")

    os.umount("/fc")

    print()
    print("Verifying data read back")
    success = True
    if result1 == "".join((lines, short, lines)):
        print("Large file Pass")
    else:
        print("Large file Fail")
        success = False
    if result2 == short:
        print("Small file Pass")
    else:
        print("Small file Fail")
        success = False
    print()
    print("Tests", "passed" if success else "failed")


class MockSDCard(sdcard.SDCard):
    """instantiates a sdcard object without talking to hardware"""

    def __init__(self, spi, cs, baudrate=100_000):
        super().__init__(spi, cs, baudrate=baudrate)

    def init_card(self, baudrate):
        """yeah, this is where we're just going to skip the whole hardware initalization thing"""
        self.baudrate = baudrate


def test_parse_csd(mockSD):
    """test the parse_csd function"""
    csd_tests = [
        {
            "name": "64g card",
            "sectors": 122191872,
            "csd": bytearray(b"@\x0e\x002[Y\x00\x01\xd2\x1f\x7f\x80\n@\x00S"),
        },
        {
            "name": "128g card",
            "sectors": 244277248,
            "csd": bytearray(b"@\x0e\x002[Y\x00\x03\xa3\xd7\x7f\x80\n@\x00A"),
        },
    ]

    for test in csd_tests:
        mockSD.parse_csd(test["csd"])
        sectors = mockSD.ioctl(4, None)
        assert sectors == test["sectors"], "Failed to parse csd for test {}, {} != {}".format(
            test["name"], sectors, test["sectors"]
        )


def run_tests():
    mockSD = MockSDCard(None, None)
    test_parse_csd(mockSD)
    print("OK")


run_tests()
