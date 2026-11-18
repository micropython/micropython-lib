#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
I2C EEPROM driver for AT24Cxx

Requires an I2C bus, for further details check
https://github.com/brainelectronics/micropython-eeprom

Example usage:
    from eeprom import EEPROM
    from machine import I2C, Pin

    # define custom I2C interface, default is 'I2C(0)'
    # check the docs of your device for further details and pin infos
    i2c = I2C(0, scl=Pin(13), sda=Pin(12), freq=800000)
    eeprom = EEPROM(addr=0x50, at24x=32, i2c=i2c)   # AT24C32 on 0x50

    # get LCD infos/properties
    print("EEPROM is on I2C address 0x{0:02x}".format(eeprom.addr))
    print("EEPROM has {} pages of {} bytes".format(eeprom.pages, eeprom.bpp))
    print("EEPROM size is {} bytes ".format(eeprom.capacity))

    # read 1 byte from address 4
    eeprom.read(4)

    # read 10 byte from address 7
    eeprom.read(7, 10)

EEPROM data sheet: https://ww1.microchip.com/downloads/en/DeviceDoc/doc0336.pdf

MIT License
Copyright (c) 2018 Mike Causer
Extended 2023 by brainelectronics

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# system packages
from machine import I2C
from time import sleep_ms


class _Subscriptable:
    def __getitem__(self, item):
        return None


_subscriptable = _Subscriptable()

List = _subscriptable
Optional = _subscriptable
Union = _subscriptable


class EEPROM(object):
    """Driver for AT24Cxx I2C EEPROM"""

    def __init__(
        self,
        addr: int = 0x50,
        pages: int = 128,
        bpp: int = 32,
        i2c: Optional[I2C] = None,
        at24x: int = 0,
    ) -> None:
        """
        Constructs a new instance

        :param      addr:   The I2C bus address of the EEPROM
        :type       addr:   int
        :param      pages:  The number of pages of the EEPROM
        :type       pages:  int
        :param      bpp:    The bytes per page
        :type       bpp:    int
        :param      i2c:    I2C object
        :type       i2c:    I2C
        :param      at24x:  The specific AT24Cxx, either 32, 64, 128, 256, 512
        :type       at24x:  int
        """
        self._addr = addr

        standard_eeproms = {
            32: [128, 32],  # 4KiB 32Kbits, 128 pages, 32 bytes/page
            64: [256, 32],  # 8KiB 64Kbits, 256 pages, 32 bytes/page
            128: [256, 64],  # 16KiB 128Kbits, 256 pages, 64 bytes/page
            256: [512, 64],  # 32KiB 256Kbits, 512 pages, 64 bytes/page
            512: [512, 128],  # 64KiB 512Kbits, 512 pages, 128 bytes/page
        }

        if at24x in standard_eeproms:
            self._pages, self._bpp = standard_eeproms[at24x]
        else:
            self._pages = pages
            self._bpp = bpp

        if i2c is None:
            # default assignment, check the docs
            self._i2c = I2C(0)
        else:
            self._i2c = i2c

    @property
    def addr(self) -> int:
        """
        Get the EEPROM I2C bus address

        :returns:   EEPROM I2C bus address
        :rtype:     int
        """
        return self._addr

    @property
    def capacity(self) -> int:
        """
        Get the storage capacity of the EEPROM

        :returns:   EEPROM capacity of the EEPROM in bytes
        :rtype:     int
        """
        return self._pages * self._bpp

    @property
    def pages(self) -> int:
        """
        Get the number of EEPROM pages

        :returns:   Number of pages of the EEPROM
        :rtype:     int
        """
        return self._pages

    @property
    def bpp(self) -> int:
        """
        Get the bytes per page of the EEPROM

        :returns:   Bytes per pages of the EEPROM
        :rtype:     int
        """
        return self._bpp

    def length(self) -> int:
        """
        Get the EEPROM length

        :returns:   Number of cells in the EEPROM
        :rtype:     int
        """
        return self.capacity

    def read(self, addr: int, nbytes: int = 1) -> bytes:
        """
        Read bytes from the EEPROM

        :param      addr:    The start address
        :type       addr:    int
        :param      nbytes:  The number of bytes to read
        :type       nbytes:  int

        :returns:   Data of EEPROM
        :rtype:     bytes
        """
        if addr > self.capacity or addr < 0:
            raise ValueError(
                "Read address {} outside of device address range {}".format(addr, self.capacity)
            )

        if addr + nbytes > self.capacity:
            raise ValueError(
                "Last read address {} outside of device address range {}".format(
                    addr + nbytes, self.capacity
                )
            )

        return self._i2c.readfrom_mem(self._addr, addr, nbytes, addrsize=16)

    def write(self, addr: int, buf: Union[bytes, List[int], str]) -> None:
        """
        Write data to the EEPROM

        :param      addr:  The start address
        :type       addr:  int
        :param      buf:   The buffer to write to the EEPROM
        :type       buf:   Union[bytes, List[int], str]
        """
        offset = addr % self._bpp
        partial = 0

        if addr > self.capacity or addr < 0:
            raise ValueError(
                "Write address {} outside of device address range {}".format(addr, self.capacity)
            )

        if addr + len(buf) > self.capacity:
            raise ValueError(
                "Last data at {} does not fit into device address range {}".format(
                    addr + len(buf), self.capacity
                )
            )

        # partial page write
        if offset > 0:
            partial = self._bpp - offset
            self._i2c.writeto_mem(self._addr, addr, buf[0:partial], addrsize=16)
            sleep_ms(5)
            addr += partial

        # full page write
        for i in range(partial, len(buf), self._bpp):
            self._i2c.writeto_mem(
                self._addr, addr + i - partial, buf[i : i + self._bpp], addrsize=16
            )
            sleep_ms(5)

    def update(self, addr: int, buf: Union[bytes, List[int], str]) -> None:
        """
        Update data in EEPROM

        :param      addr:  The start address
        :type       addr:  int
        :param      buf:   The buffer to write to the EEPROM
        :type       buf:   Union[bytes, List[int], str]
        """
        for idx, ele in enumerate(buf):
            this_addr = addr + idx

            if isinstance(ele, int):
                this_val = ele.to_bytes(1, "big")
            else:
                this_val = str(ele).encode()

            current_value = self.read(addr=this_addr)  # returns bytes
            if current_value != this_val:
                self.write(addr=this_addr, buf=this_val)
            #     print("{}: {} -> {}".
            #           format(this_addr, current_value, this_val))
            # else:
            #     print("No need to update value at {}".format(this_addr))

    def wipe(self) -> None:
        """Wipe the complete EEPROM"""
        page_buff = b"\xff" * self.bpp
        for i in range(self.pages):
            self.write(i * self.bpp, page_buff)

    def print_pages(self, addr: int, nbytes: int) -> None:
        """
        Print pages content with boundaries.

        :param      addr:    The start address
        :type       addr:    int
        :param      nbytes:  The number of bytes to read
        :type       nbytes:  int
        """
        unknown_data_first_page = addr % self.bpp
        unknown_data_last_page = self.bpp - (addr + nbytes) % self.bpp
        if unknown_data_last_page % self.bpp == 0:
            unknown_data_last_page = 0

        data = self.read(addr=addr, nbytes=nbytes)
        extended_data = b"?" * unknown_data_first_page + data + b"?" * unknown_data_last_page

        sliced_data = [
            extended_data[i : i + self.bpp] for i in range(0, len(extended_data), self.bpp)
        ]
        print("Page {:->4}: 0 {} {}".format("x", "-" * (self.bpp - len(str(self.bpp))), self.bpp))
        for idx, a_slice in enumerate(sliced_data):
            print("Page {:->4}: {}".format(idx, a_slice))
