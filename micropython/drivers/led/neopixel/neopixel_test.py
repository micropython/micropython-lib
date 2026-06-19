import machine
import neopixel


def neopixel_test():
    np = neopixel.NeoPixel(machine.Pin(1), 3)
    print("Fill with a color.")
    np.fill((255, 128, 64))
    print("Verify the bytes to be written")
    expected = bytearray([255, 128, 64, 255, 128, 64, 255, 128, 64])
    actual = np.buf
    passed = "passed" if expected == actual else "failed"
    print(f"Initial fill: {passed}.")
    print()

    print("Change brightness of all pixels.")
    np.brightness(0.5)
    expected = bytearray([127, 64, 32, 127, 64, 32, 127, 64, 32])
    actual = np.buf
    passed = "passed" if expected == actual else "failed"
    print(f"Brightness change: {passed}.")
    print()

    print("Get current brightness.")
    expected = 0.5
    actual = np.brightness()
    passed = "passed" if expected == actual else "failed"
    print(f"Brightness get: {passed}.")
    print()
