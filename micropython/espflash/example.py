import espflash
from machine import Pin
from machine import UART

if __name__ == "__main__":
    reset = Pin(3, Pin.OUT)
    gpio0 = Pin(2, Pin.OUT)
    uart = UART(1, 115200, tx=Pin(8), rx=Pin(9), timeout=350)

    md5sum = b"9a6cf1257769c9f1af08452558e4d60e"
    path = "NINA_W102-v1.5.0-Nano-RP2040-Connect.bin"

    esp = espflash.ESPFlash(reset, gpio0, uart)
    # Enter bootloader download mode, at 115200
    esp.bootloader()
    # Can now chage to higher/lower baudrate
    esp.set_baudrate(921600)
    # Must call this first before any flash functions.
    esp.flash_attach()
    # Read flash size
    size = esp.flash_read_size()
    # Configure flash parameters.
    esp.flash_config(size)
    # Write firmware image from internal storage.
    esp.flash_write_file(path)
    # Compares file and flash MD5 checksum.
    esp.flash_verify_file(path, md5sum)
    # Resets the ESP32 chip.
    esp.reboot()
