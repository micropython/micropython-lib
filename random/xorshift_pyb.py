from under_random import UnderRandom
from xorshift import XorShift128

class XorShiftPyb(XorShift128):

    # From https://en.wikipedia.org/wiki/Xorshift#Example_implementation
    # #include <stdint.h>
    #
    # /* These state variables must be initialized so that they are not all zero. */
    # uint32_t x, y, z, w;
    #
    # uint32_t xorshift128(void) {
    #         uint32_t t = x ^ (x << 11);
    #         x = y; y = z; z = w;
    #         return w = w ^ (w >> 19) ^ t ^ (t >> 8);
    #     }

    @staticmethod
    @micropython.asm_thumb
    def _step(r0):             # r0 is the base addr of the state array "a"
        mov(r7, r0)             # r7 is base addr of a
        ldr(r0, [r7, 0])        # r0 is x
        mov(r1, r0)             # r1 is x
        mov(r6, 11)             # r6 is 11
        lsl(r1, r6)             # r1 is x << 11
        eor(r0, r1)             # r0 is x ^ (x << 11)
        str(r0, [r7, 16])       # t is x ^ (x << 11)
        ldr(r0, [r7,  4])       # r0 is y
        str(r0, [r7,  0])       # x = y
        ldr(r0, [r7,  8])       # r0 is z
        str(r0, [r7,  4])       # y = z
        ldr(r0, [r7, 12])       # r0 is w
        str(r0, [r7,  8])       # z = w
        mov(r5, r0)             # r5 is w
        mov(r6, 19)
        lsr(r5, r6)             # r5 is w >> 19
        eor(r0, r5)             # r0 is w ^ (w >> 19)
        ldr(r5, [r7, 16])       # r5 is t
        eor(r0, r5)             # r0 is w ^ (w >> 19) ^ t
        mov(r6, 8)
        lsr(r5, r6)             # r5 is t >> 8
        eor(r0, r5)             # r0 is w ^ (w >> 19) ^ t ^ (t >> 8)
        str(r0, [r7, 12])       # w = w ^ (w >> 19) ^ t ^ (t >> 8)
        eor(r6, r6)
        movt(r6, 0xc000)
        bic(r0, r6)             # r0 is only 30 bits of result


class Random(UnderRandom, XorShiftPyb):
    pass
