import machine
import neopixel


def neopixel_test():
    np = neopixel.NeoPixel(machine.Pin(1), 3)
    print("Fill with a color.")
    np.fill((255, 128, 64))
    print("Verify the bytes to be written")
    expected_bytearray = bytearray([255, 128, 64, 255, 128, 64, 255, 128, 64])
    actual_bytearray = np.buf
    print(
        f'Initial fill: {"passed" if expected_bytearray == actual_bytearray else "failed"}.'
    )
    print()

    print("Change brightness of all pixels.")
    np.brightness(0.5)
    expected_bytearray = bytearray([127, 64, 32, 127, 64, 32, 127, 64, 32])
    actual_bytearray = np.buf
    print(
        f'Brightness change: {"passed" if expected_bytearray == actual_bytearray else "failed"}.'
    )
    print()

    print("Get current brightness.")
    expected_brightness = 0.5
    actual_brightness = np.brightness()
    print(
        f'Brightness get: {"passed" if expected_brightness == actual_brightness else "failed"}.'
    )
    print()
