import micropython
from uctypes import addressof

# ruff: noqa: F821 - @asm_thumb and @viper decorator adds names to function scope

# https://electronics.stackexchange.com/questions/321304/how-to-use-the-data-crc-of-sd-cards-in-spi-mode
# for sd bit mode
import array

_sd_crc16_table = array.array("H", (0 for _ in range(256)))
# /* Generate CRC16 table */
# for (byt = 0U; byt < 256U; byt ++){
#  crc = byt << 8;
#  for (bit = 0U; bit < 8U; bit ++){
#   crc <<= 1;
#   if ((crc & 0x10000U) != 0U){ crc ^= 0x1021U; }
#  }
#  sd_crc16_table[byt] = (crc & 0xFFFFU);
# }
for byt in range(256):
    crc = byt << 8
    for bit in range(8):
        crc = crc << 1
        if (crc & 0x10000) != 0:
            crc ^= 0x1021
    _sd_crc16_table[byt] = crc & 0xFFFF


# /* Running CRC16 calculation for a byte. */
# static unsigned int sd_crc16_byte(unsigned int crcval, unsigned int byte)
# {
#  return (sd_crc16_table[(byte ^ (crcval >> 8)) & 0xFFU] ^ (crcval << 8)) & 0xFFFFU;
# }


@micropython.viper
def crc16_viper(crc: int, data) -> int:
    dp = ptr8(addressof(data))
    tp = ptr16(addressof(_sd_crc16_table))
    nn = int(len(data))
    idx = 0
    while idx < nn:
        crc = ((crc << 8) & 0xFFFF) ^ tp[((crc >> 8) ^ dp[idx]) & 0xFF]
        idx += 1
    return crc


try:  # if we have asm_thumb, this goes faster

    @micropython.asm_thumb
    def _crc_loop_16(r0, r1, r2, r3) -> int:
        # r0 is data  address
        # r1 is table address
        # r2 is CRC
        # r3 is count
        mov(r4, 0)
        mvn(r4, r4)  # all ones now
        mov(r7, 16)
        lsr(r4, r7)  # R4 = half-word of ones
        mov(r5, 0xFF)  # used for byte masking
        label(loop)
        mov(r6, r2)  # copy current CRC
        mov(r7, 8)
        lsr(r6, r7)  # crc >> 8
        ldrb(r7, [r0, 0])  # fetch new byte dp[idx]
        add(r0, 1)  # push to next byte address
        eor(r6, r7)  # r6 = (crc>>8) ^ dp[idx]
        and_(r6, r5)  # mask byte ( (crc>>8) ^ dp[idx]) & 0xff
        add(r6, r6, r6)  # double for table offset
        add(r6, r6, r1)  # table data address
        ldrh(r6, [r6, 0])  # fetch table syndrome
        mov(r7, 8)
        lsl(r2, r7)  # CRC << 8
        and_(r2, r4)  # (crc << 8) & 0xffff)
        eor(r2, r6)  # new CRC
        sub(r3, 1)
        bne(loop)
        mov(r0, r2)

    @micropython.viper
    def crc16(crc: int, data) -> int:
        return int(
            _crc_loop_16(
                int(addressof(data)),
                int(addressof(_sd_crc16_table)),
                crc,
                int(len(data)),
            )
        )

except:
    # wrapper to allow the pure-python implementation to be accessed by the right name if asm_thumb doesn't work
    @micropython.viper
    def crc16(crc: int, data) -> int:
        return int(crc16_viper(crc, data))


# def test_speed():
#     data = b"\xaa"*1024
#     import time
#     crc = 0
#     start = time.ticks_us()
#     for i in range(1024):
#         crc = crc16(crc, data)
#     print("asm crc speed = ", f"{crc:08x}", 2**20 / (time.ticks_diff(time.ticks_us(), start) / 1e6), "bytes/s")
#
#     crc = 0
#     start = time.ticks_us()
#     for i in range(1024):
#         crc = crc16_viper(crc, data)
#     print("py  crc speed = ", f"{crc:08x}", 2**20 / (time.ticks_diff(time.ticks_us(), start) / 1e6), "bytes/s")
