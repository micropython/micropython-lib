# MIT license; Copyright (c) 2023 Jim Mussared
# Originally ported from CPython by Paul Sokolovsky

from ._sha import sha

_SHA_BLOCKSIZE = const(128)


ROR64 = (
    lambda x, y: (((x & 0xFFFFFFFFFFFFFFFF) >> (y & 63)) | (x << (64 - (y & 63))))
    & 0xFFFFFFFFFFFFFFFF
)
Ch = lambda x, y, z: (z ^ (x & (y ^ z)))
Maj = lambda x, y, z: (((x | y) & z) | (x & y))
S = lambda x, n: ROR64(x, n)
R = lambda x, n: (x & 0xFFFFFFFFFFFFFFFF) >> n
Sigma0 = lambda x: (S(x, 28) ^ S(x, 34) ^ S(x, 39))
Sigma1 = lambda x: (S(x, 14) ^ S(x, 18) ^ S(x, 41))
Gamma0 = lambda x: (S(x, 1) ^ S(x, 8) ^ R(x, 7))
Gamma1 = lambda x: (S(x, 19) ^ S(x, 61) ^ R(x, 6))


class sha512(sha):
    digest_size = digestsize = 64
    block_size = _SHA_BLOCKSIZE
    _iv = [
        0x6A09E667F3BCC908,
        0xBB67AE8584CAA73B,
        0x3C6EF372FE94F82B,
        0xA54FF53A5F1D36F1,
        0x510E527FADE682D1,
        0x9B05688C2B3E6C1F,
        0x1F83D9ABFB41BD6B,
        0x5BE0CD19137E2179,
    ]

    def _transform(self):
        W = []

        d = self._data
        for i in range(0, 16):
            W.append(
                (d[8 * i] << 56)
                + (d[8 * i + 1] << 48)
                + (d[8 * i + 2] << 40)
                + (d[8 * i + 3] << 32)
                + (d[8 * i + 4] << 24)
                + (d[8 * i + 5] << 16)
                + (d[8 * i + 6] << 8)
                + d[8 * i + 7]
            )

        for i in range(16, 80):
            W.append(
                (Gamma1(W[i - 2]) + W[i - 7] + Gamma0(W[i - 15]) + W[i - 16]) & 0xFFFFFFFFFFFFFFFF
            )

        ss = self._digest[:]

        def RND(a, b, c, d, e, f, g, h, i, ki):
            t0 = (h + Sigma1(e) + Ch(e, f, g) + ki + W[i]) & 0xFFFFFFFFFFFFFFFF
            t1 = (Sigma0(a) + Maj(a, b, c)) & 0xFFFFFFFFFFFFFFFF
            d = (d + t0) & 0xFFFFFFFFFFFFFFFF
            h = (t0 + t1) & 0xFFFFFFFFFFFFFFFF
            return d & 0xFFFFFFFFFFFFFFFF, h & 0xFFFFFFFFFFFFFFFF

        ss[3], ss[7] = RND(
            ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], 0, 0x428A2F98D728AE22
        )
        ss[2], ss[6] = RND(
            ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], 1, 0x7137449123EF65CD
        )
        ss[1], ss[5] = RND(
            ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], 2, 0xB5C0FBCFEC4D3B2F
        )
        ss[0], ss[4] = RND(
            ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], 3, 0xE9B5DBA58189DBBC
        )
        ss[7], ss[3] = RND(
            ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], 4, 0x3956C25BF348B538
        )
        ss[6], ss[2] = RND(
            ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], 5, 0x59F111F1B605D019
        )
        ss[5], ss[1] = RND(
            ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], 6, 0x923F82A4AF194F9B
        )
        ss[4], ss[0] = RND(
            ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], 7, 0xAB1C5ED5DA6D8118
        )
        ss[3], ss[7] = RND(
            ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], 8, 0xD807AA98A3030242
        )
        ss[2], ss[6] = RND(
            ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], 9, 0x12835B0145706FBE
        )
        ss[1], ss[5] = RND(
            ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], 10, 0x243185BE4EE4B28C
        )
        ss[0], ss[4] = RND(
            ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], 11, 0x550C7DC3D5FFB4E2
        )
        ss[7], ss[3] = RND(
            ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], 12, 0x72BE5D74F27B896F
        )
        ss[6], ss[2] = RND(
            ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], 13, 0x80DEB1FE3B1696B1
        )
        ss[5], ss[1] = RND(
            ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], 14, 0x9BDC06A725C71235
        )
        ss[4], ss[0] = RND(
            ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], 15, 0xC19BF174CF692694
        )
        ss[3], ss[7] = RND(
            ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], 16, 0xE49B69C19EF14AD2
        )
        ss[2], ss[6] = RND(
            ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], 17, 0xEFBE4786384F25E3
        )
        ss[1], ss[5] = RND(
            ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], 18, 0x0FC19DC68B8CD5B5
        )
        ss[0], ss[4] = RND(
            ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], 19, 0x240CA1CC77AC9C65
        )
        ss[7], ss[3] = RND(
            ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], 20, 0x2DE92C6F592B0275
        )
        ss[6], ss[2] = RND(
            ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], 21, 0x4A7484AA6EA6E483
        )
        ss[5], ss[1] = RND(
            ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], 22, 0x5CB0A9DCBD41FBD4
        )
        ss[4], ss[0] = RND(
            ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], 23, 0x76F988DA831153B5
        )
        ss[3], ss[7] = RND(
            ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], 24, 0x983E5152EE66DFAB
        )
        ss[2], ss[6] = RND(
            ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], 25, 0xA831C66D2DB43210
        )
        ss[1], ss[5] = RND(
            ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], 26, 0xB00327C898FB213F
        )
        ss[0], ss[4] = RND(
            ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], 27, 0xBF597FC7BEEF0EE4
        )
        ss[7], ss[3] = RND(
            ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], 28, 0xC6E00BF33DA88FC2
        )
        ss[6], ss[2] = RND(
            ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], 29, 0xD5A79147930AA725
        )
        ss[5], ss[1] = RND(
            ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], 30, 0x06CA6351E003826F
        )
        ss[4], ss[0] = RND(
            ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], 31, 0x142929670A0E6E70
        )
        ss[3], ss[7] = RND(
            ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], 32, 0x27B70A8546D22FFC
        )
        ss[2], ss[6] = RND(
            ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], 33, 0x2E1B21385C26C926
        )
        ss[1], ss[5] = RND(
            ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], 34, 0x4D2C6DFC5AC42AED
        )
        ss[0], ss[4] = RND(
            ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], 35, 0x53380D139D95B3DF
        )
        ss[7], ss[3] = RND(
            ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], 36, 0x650A73548BAF63DE
        )
        ss[6], ss[2] = RND(
            ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], 37, 0x766A0ABB3C77B2A8
        )
        ss[5], ss[1] = RND(
            ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], 38, 0x81C2C92E47EDAEE6
        )
        ss[4], ss[0] = RND(
            ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], 39, 0x92722C851482353B
        )
        ss[3], ss[7] = RND(
            ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], 40, 0xA2BFE8A14CF10364
        )
        ss[2], ss[6] = RND(
            ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], 41, 0xA81A664BBC423001
        )
        ss[1], ss[5] = RND(
            ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], 42, 0xC24B8B70D0F89791
        )
        ss[0], ss[4] = RND(
            ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], 43, 0xC76C51A30654BE30
        )
        ss[7], ss[3] = RND(
            ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], 44, 0xD192E819D6EF5218
        )
        ss[6], ss[2] = RND(
            ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], 45, 0xD69906245565A910
        )
        ss[5], ss[1] = RND(
            ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], 46, 0xF40E35855771202A
        )
        ss[4], ss[0] = RND(
            ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], 47, 0x106AA07032BBD1B8
        )
        ss[3], ss[7] = RND(
            ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], 48, 0x19A4C116B8D2D0C8
        )
        ss[2], ss[6] = RND(
            ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], 49, 0x1E376C085141AB53
        )
        ss[1], ss[5] = RND(
            ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], 50, 0x2748774CDF8EEB99
        )
        ss[0], ss[4] = RND(
            ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], 51, 0x34B0BCB5E19B48A8
        )
        ss[7], ss[3] = RND(
            ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], 52, 0x391C0CB3C5C95A63
        )
        ss[6], ss[2] = RND(
            ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], 53, 0x4ED8AA4AE3418ACB
        )
        ss[5], ss[1] = RND(
            ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], 54, 0x5B9CCA4F7763E373
        )
        ss[4], ss[0] = RND(
            ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], 55, 0x682E6FF3D6B2B8A3
        )
        ss[3], ss[7] = RND(
            ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], 56, 0x748F82EE5DEFB2FC
        )
        ss[2], ss[6] = RND(
            ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], 57, 0x78A5636F43172F60
        )
        ss[1], ss[5] = RND(
            ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], 58, 0x84C87814A1F0AB72
        )
        ss[0], ss[4] = RND(
            ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], 59, 0x8CC702081A6439EC
        )
        ss[7], ss[3] = RND(
            ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], 60, 0x90BEFFFA23631E28
        )
        ss[6], ss[2] = RND(
            ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], 61, 0xA4506CEBDE82BDE9
        )
        ss[5], ss[1] = RND(
            ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], 62, 0xBEF9A3F7B2C67915
        )
        ss[4], ss[0] = RND(
            ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], 63, 0xC67178F2E372532B
        )
        ss[3], ss[7] = RND(
            ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], 64, 0xCA273ECEEA26619C
        )
        ss[2], ss[6] = RND(
            ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], 65, 0xD186B8C721C0C207
        )
        ss[1], ss[5] = RND(
            ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], 66, 0xEADA7DD6CDE0EB1E
        )
        ss[0], ss[4] = RND(
            ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], 67, 0xF57D4F7FEE6ED178
        )
        ss[7], ss[3] = RND(
            ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], 68, 0x06F067AA72176FBA
        )
        ss[6], ss[2] = RND(
            ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], 69, 0x0A637DC5A2C898A6
        )
        ss[5], ss[1] = RND(
            ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], 70, 0x113F9804BEF90DAE
        )
        ss[4], ss[0] = RND(
            ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], 71, 0x1B710B35131C471B
        )
        ss[3], ss[7] = RND(
            ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], 72, 0x28DB77F523047D84
        )
        ss[2], ss[6] = RND(
            ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], 73, 0x32CAAB7B40C72493
        )
        ss[1], ss[5] = RND(
            ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], 74, 0x3C9EBE0A15C9BEBC
        )
        ss[0], ss[4] = RND(
            ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], 75, 0x431D67C49C100D4C
        )
        ss[7], ss[3] = RND(
            ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], 76, 0x4CC5D4BECB3E42B6
        )
        ss[6], ss[2] = RND(
            ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], 77, 0x597F299CFC657E2A
        )
        ss[5], ss[1] = RND(
            ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], 78, 0x5FCB6FAB3AD6FAEC
        )
        ss[4], ss[0] = RND(
            ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], 79, 0x6C44198C4A475817
        )

        for i in range(len(self._digest)):
            self._digest[i] = (self._digest[i] + ss[i]) & 0xFFFFFFFFFFFFFFFF

    def _update(self, buffer):
        if isinstance(buffer, str):
            raise TypeError("Unicode strings must be encoded before hashing")
        count = len(buffer)
        buffer_idx = 0
        clo = (self._count_lo + (count << 3)) & 0xFFFFFFFF
        if clo < self._count_lo:
            self._count_hi += 1
        self._count_lo = clo

        self._count_hi += count >> 29

        if self._local:
            i = _SHA_BLOCKSIZE - self._local
            if i > count:
                i = count

            # copy buffer
            for x in enumerate(buffer[buffer_idx : buffer_idx + i]):
                self._data[self._local + x[0]] = x[1]

            count -= i
            buffer_idx += i

            self._local += i
            if self._local == _SHA_BLOCKSIZE:
                self._transform()
                self._local = 0
            else:
                return

        while count >= _SHA_BLOCKSIZE:
            # copy buffer
            self._data = bytearray(buffer[buffer_idx : buffer_idx + _SHA_BLOCKSIZE])
            count -= _SHA_BLOCKSIZE
            buffer_idx += _SHA_BLOCKSIZE
            self._transform()

        # copy buffer
        pos = self._local
        self._data[pos : pos + count] = buffer[buffer_idx : buffer_idx + count]
        self._local = count

    def _final(self):
        lo_bit_count = self._count_lo
        hi_bit_count = self._count_hi
        count = (lo_bit_count >> 3) & 0x7F
        self._data[count] = 0x80
        count += 1
        if count > _SHA_BLOCKSIZE - 16:
            # zero the bytes in data after the count
            self._data = self._data[:count] + bytes(_SHA_BLOCKSIZE - count)
            self._transform()
            # zero bytes in data
            self._data = bytearray(_SHA_BLOCKSIZE)
        else:
            self._data = self._data[:count] + bytes(_SHA_BLOCKSIZE - count)

        self._data[112] = 0
        self._data[113] = 0
        self._data[114] = 0
        self._data[115] = 0
        self._data[116] = 0
        self._data[117] = 0
        self._data[118] = 0
        self._data[119] = 0

        self._data[120] = (hi_bit_count >> 24) & 0xFF
        self._data[121] = (hi_bit_count >> 16) & 0xFF
        self._data[122] = (hi_bit_count >> 8) & 0xFF
        self._data[123] = (hi_bit_count >> 0) & 0xFF
        self._data[124] = (lo_bit_count >> 24) & 0xFF
        self._data[125] = (lo_bit_count >> 16) & 0xFF
        self._data[126] = (lo_bit_count >> 8) & 0xFF
        self._data[127] = (lo_bit_count >> 0) & 0xFF

        self._transform()

        dig = bytearray()
        for i in self._digest:
            for j in range(8):
                dig.append((i >> ((7 - j) * 8)) & 0xFF)
        return dig
