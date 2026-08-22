#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#=======================================================================
# Author: Joachim Strömbergson
# Copyright (c) 2014, Secworks Sweden AB
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#=======================================================================

AES_128_ROUNDS = 10
AES_256_ROUNDS = 14


class AesCypher():
    sbox = [0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5,
            0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
            0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0,
            0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
            0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc,
            0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
            0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a,
            0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
            0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0,
            0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
            0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b,
            0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
            0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85,
            0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
            0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5,
            0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
            0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17,
            0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
            0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88,
            0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
            0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c,
            0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
            0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9,
            0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
            0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6,
            0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
            0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e,
            0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
            0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94,
            0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
            0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68,
            0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16]

    inv_sbox = [0x52, 0x09, 0x6a, 0xd5, 0x30, 0x36, 0xa5, 0x38,
                0xbf, 0x40, 0xa3, 0x9e, 0x81, 0xf3, 0xd7, 0xfb,
                0x7c, 0xe3, 0x39, 0x82, 0x9b, 0x2f, 0xff, 0x87,
                0x34, 0x8e, 0x43, 0x44, 0xc4, 0xde, 0xe9, 0xcb,
                0x54, 0x7b, 0x94, 0x32, 0xa6, 0xc2, 0x23, 0x3d,
                0xee, 0x4c, 0x95, 0x0b, 0x42, 0xfa, 0xc3, 0x4e,
                0x08, 0x2e, 0xa1, 0x66, 0x28, 0xd9, 0x24, 0xb2,
                0x76, 0x5b, 0xa2, 0x49, 0x6d, 0x8b, 0xd1, 0x25,
                0x72, 0xf8, 0xf6, 0x64, 0x86, 0x68, 0x98, 0x16,
                0xd4, 0xa4, 0x5c, 0xcc, 0x5d, 0x65, 0xb6, 0x92,
                0x6c, 0x70, 0x48, 0x50, 0xfd, 0xed, 0xb9, 0xda,
                0x5e, 0x15, 0x46, 0x57, 0xa7, 0x8d, 0x9d, 0x84,
                0x90, 0xd8, 0xab, 0x00, 0x8c, 0xbc, 0xd3, 0x0a,
                0xf7, 0xe4, 0x58, 0x05, 0xb8, 0xb3, 0x45, 0x06,
                0xd0, 0x2c, 0x1e, 0x8f, 0xca, 0x3f, 0x0f, 0x02,
                0xc1, 0xaf, 0xbd, 0x03, 0x01, 0x13, 0x8a, 0x6b,
                0x3a, 0x91, 0x11, 0x41, 0x4f, 0x67, 0xdc, 0xea,
                0x97, 0xf2, 0xcf, 0xce, 0xf0, 0xb4, 0xe6, 0x73,
                0x96, 0xac, 0x74, 0x22, 0xe7, 0xad, 0x35, 0x85,
                0xe2, 0xf9, 0x37, 0xe8, 0x1c, 0x75, 0xdf, 0x6e,
                0x47, 0xf1, 0x1a, 0x71, 0x1d, 0x29, 0xc5, 0x89,
                0x6f, 0xb7, 0x62, 0x0e, 0xaa, 0x18, 0xbe, 0x1b,
                0xfc, 0x56, 0x3e, 0x4b, 0xc6, 0xd2, 0x79, 0x20,
                0x9a, 0xdb, 0xc0, 0xfe, 0x78, 0xcd, 0x5a, 0xf4,
                0x1f, 0xdd, 0xa8, 0x33, 0x88, 0x07, 0xc7, 0x31,
                0xb1, 0x12, 0x10, 0x59, 0x27, 0x80, 0xec, 0x5f,
                0x60, 0x51, 0x7f, 0xa9, 0x19, 0xb5, 0x4a, 0x0d,
                0x2d, 0xe5, 0x7a, 0x9f, 0x93, 0xc9, 0x9c, 0xef,
                0xa0, 0xe0, 0x3b, 0x4d, 0xae, 0x2a, 0xf5, 0xb0,
                0xc8, 0xeb, 0xbb, 0x3c, 0x83, 0x53, 0x99, 0x61,
                0x17, 0x2b, 0x04, 0x7e, 0xba, 0x77, 0xd6, 0x26,
                0xe1, 0x69, 0x14, 0x63, 0x55, 0x21, 0x0c, 0x7d]


    def __init__(self, verbose = True, dump_vars = True):
        self.verbose = verbose
        self.dump_vars = dump_vars

    def check_block(self, expected, result):
        """
        Checks and reports if a result block matches expected block.

        Parameters
        ----------
        expected : tuple(int, int, int, int)
            Expected block
        result : tuple(int, int, int, int)
            Block to compare with expected result

        Returns
        -------
        int
            0 if block matches the expected block
            1 otherwise
        """
        if (expected[0] == result[0]) and  (expected[1] == result[1]) and\
          (expected[2] == result[2]) and  (expected[3] == result[3]):
            if self.verbose:
                print("OK. Result matches expected.")
                print("")
            return 0

        else:
            print("ERROR. Result does not match expected.")
            print("Expected:")
            self._print_block(expected)
            print("Got:")
            self._print_block(result)
            print("")
            return 1

    def aes_encipher_block(self, key, block):
        """
        Perform AES encipher operation for the given block using the
        given key length.

        Parameters
        ----------
        key : tuple
            128 or 256 bits key split in 32 bits words
        block : tuple(int, int, int, int)
            128 bits block split in 32 bits words

        Returns
        -------
        tuple(int, int, int, int)
            128 bits block, result from the encipher operation
        """

        # Get round keys based on the given key.
        if len(key) == 4:
            round_keys = self._key_gen128(key)
            num_rounds = AES_128_ROUNDS
        else:
            round_keys = self._key_gen256(key)
            num_rounds = AES_256_ROUNDS

        # Init round
        if self.verbose:
            print("  Initial AddRoundKeys round.")
        tmp_block4 = self._addroundkey(round_keys[0], block)

        # Main rounds
        for i in range(1 , (num_rounds)):
            if self.verbose:
                print("")
                print("  Round %02d" % i)
                print("  ---------")

            tmp_block1 = self._subbytes(tmp_block4)
            tmp_block2 = self._shiftrows(tmp_block1)
            tmp_block3 = self._mixcolumns(tmp_block2)
            tmp_block4 = self._addroundkey(round_keys[i], tmp_block3)


        # Final round
        if self.verbose:
            print("  Final round.")
        tmp_block1 = self._subbytes(tmp_block4)
        tmp_block2 = self._shiftrows(tmp_block1)
        tmp_block3 = self._addroundkey(round_keys[num_rounds], tmp_block2)

        return tmp_block3

    def aes_decipher_block(self, key, block):
        """
        Perform AES decipher operation for the given block
        using the given key length.

        Parameters
        ----------
        key : tuple
            128 or 256 bits key split in 32 bits words
        block : tuple(int, int, int, int)
            128 bits block split in 32 bits words

        Returns
        -------
        tuple(int, int, int, int)
            128 bits block, result from the decipher operation
        """
        tmp_block = block[:]

        # Get round keys based on the given key.
        if len(key) == 4:
            round_keys = self._key_gen128(key)
            num_rounds = AES_128_ROUNDS
        else:
            round_keys = self._key_gen256(key)
            num_rounds = AES_256_ROUNDS

            # Initial round
        if self.verbose:
            print("  Initial, partial round.")
        tmp_block1 = self._addroundkey(round_keys[len(round_keys) - 1], tmp_block)
        tmp_block2 = self._inv__shiftrows(tmp_block1)
        tmp_block4 = self._inv__subbytes(tmp_block2)

        # Main rounds
        for i in range(1 , (num_rounds)):
            if self.verbose:
                print("")
                print("  Round %02d" % i)
                print("  ---------")

            tmp_block1 = self._addroundkey(round_keys[(len(round_keys) - i - 1)], tmp_block4)
            tmp_block2 = self._inv__mixcolumns(tmp_block1)
            tmp_block3 = self._inv__shiftrows(tmp_block2)
            tmp_block4 = self._inv__subbytes(tmp_block3)

        # Final round
        if self.verbose:
            print("  Final AddRoundKeys round.")
        res_block = self._addroundkey(round_keys[0], tmp_block4)

        return res_block
    
    def _print_block(self, block):
        """
        Print the given block as four 32 bit words.
        """
        (w0, w1, w2, w3) = block
        print("0x%08x, 0x%08x, 0x%08x, 0x%08x" % (w0, w1, w2, w3))

    def _print_key(self, key):
        """
        Print the given key as on or two sets of four 32 bit words.
        """
        if len(key) == 8:
            (k0, k1, k2, k3, k4, k5, k6, k7) = key
            self._print_block((k0, k1, k2, k3))
            self._print_block((k4, k5, k6, k7))
        else:
            self._print_block(key)

    def _b2w(self, b0, b1, b2, b3):
        """
        Creates a word from the given bytes.
        """
        return (b0 << 24) + (b1 << 16) + (b2 << 8) + b3

    def _w2b(self, w):
        """
        Extracts the bytes in a word.
        """
        b0 = w >> 24
        b1 = w >> 16 & 0xff
        b2 = w >> 8 & 0xff
        b3 = w & 0xff
        return (b0, b1, b2, b3)

    def _gm2(self, b):
        """
        The specific Galois Multiplication by two for a given byte.
        """
        return ((b << 1) ^ (0x1b & ((b >> 7) * 0xff))) & 0xff

    def _gm3(self, b):
        """
        The specific Galois Multiplication by three for a given byte.
        """
        return self._gm2(b) ^ b

    def _gm4(self, b):
        """
        The specific Galois Multiplication by four for a given byte.
        """
        return self._gm2(self._gm2(b))

    def _gm8(self, b):
        """
        The specific Galois Multiplication by eight for a given byte.
        """
        return self._gm2(self._gm4(b))

    def _gm09(self, b):
        """
        The specific Galois Multiplication by nine for a given byte.
        """
        return self._gm8(b) ^ b

    def _gm11(self, b):
        """
        The specific Galois Multiplication by 11 for a given byte.
        """
        return self._gm8(b) ^ self._gm2(b) ^ b

    def _gm13(self, b):
        """
        The specific Galois Multiplication by 13 for a given byte.
        """
        return self._gm8(b) ^ self._gm4(b) ^ b

    def gm14(self, b):
        """
        The specific Galois Multiplication by 14 for a given byte.
        """
        return self._gm8(b) ^ self._gm4(b) ^ self._gm2(b)

    def _substw(self, w):
        """
        Returns a 32-bit word in which each of the bytes in the
        given 32-bit word has been used as lookup into the AES S-box.
        """
        (b0, b1, b2, b3) = self._w2b(w)
        s0 = self.sbox[b0]
        s1 = self.sbox[b1]
        s2 = self.sbox[b2]
        s3 = self.sbox[b3]
        res = self._b2w(s0, s1, s2, s3)

        if (self.verbose):
            print("Inside _substw:")
            print("b0 = 0x%02x, b1 = 0x%02x, b2 = 0x%02x, b3 = 0x%02x" %
                  (b0, b1, b2, b3))
            print("s0 = 0x%02x, s1 = 0x%02x, s2 = 0x%02x, s3 = 0x%02x" %
                  (s0, s1, s2, s3))
            print("res = 0x%08x" % (res))
        return res

    def _inv__substw(self, w):
        """
        Returns a 32-bit word in which each of the bytes in the
        given 32-bit word has been used as lookup into
        the inverse AES S-box.
        """
        (b0, b1, b2, b3) = self._w2b(w)
        s0 = self.inv_sbox[b0]
        s1 = self.inv_sbox[b1]
        s2 = self.inv_sbox[b2]
        s3 = self.inv_sbox[b3]
        res = self._b2w(s0, s1, s2, s3)

        if (self.verbose):
            print("Inside _inv__substw:")
            print("b0 = 0x%02x, b1 = 0x%02x, b2 = 0x%02x, b3 = 0x%02x" %
                (b0, b1, b2, b3))
            print("s0 = 0x%02x, s1 = 0x%02x, s2 = 0x%02x, s3 = 0x%02x" %
                (s0, s1, s2, s3))
            print("res = 0x%08x" % (res))
        return res

    def _rolx(self, w, x):
        """
        Rotate the given 32 bit word x bits left.
        """
        return ((w << x) | (w >> (32 - x))) & 0xffffffff

    def _next_128bit_key(self, prev_key, rcon):
        """
        Generate the next four key words for aes-128 based on given
        rcon and previous key words.
        """
        (w0, w1, w2, w3) = prev_key

        rol = self._rolx(w3, 8)
        subst = self._substw(rol)
        t = subst ^ (rcon << 24)

        k0 = w0 ^ t
        k1 = w1 ^ w0 ^ t
        k2 = w2 ^ w1 ^ w0 ^ t
        k3 = w3 ^ w2 ^ w1 ^ w0 ^ t

        if (self.verbose):
            print("Inside next 128bit key:")
            print("w0 = 0x%08x, w1 = 0x%08x, w2 = 0x%08x, w3 = 0x%08x" %
                  (w0, w1, w2, w3))
            print("rol = 0x%08x, subst = 0x%08x, rcon = 0x%02x, t = 0x%08x" %
                  (rol, subst, rcon, t))
            print("k0 = 0x%08x, k1 = 0x%08x, k2 = 0x%08x, k3 = 0x%08x" %
                  (k0, k1, k2, k3))
        return (k0, k1, k2, k3)

    def _key_gen128(self, key):
        """
        Generating the keys for 128 bit keys.
        """
        if self.verbose:
            print("Doing the 128 bit key expansion")

        round_keys = []
        round_keys.append(key)

        for i in range(10):
            round_keys.append(self._next_128bit_key(round_keys[i], self._get_rcon(i + 1)))

        if (self.verbose):
            print("Input key:")
            self._print_block(key)
            print("")

            print("Generated keys:")
            for k in round_keys:
                self._print_block(k)
            print("")

        return round_keys

    def _next_256bit_key_a(self, key0, key1, rcon):
        """
        Generate the next four key words for aes-256 using algorithm A
        based on given rcon and the previous two keys.
        """
        (w0, w1, w2, w3) = key0
        (w4, w5, w6, w7) = key1

        sw = self._substw(self._rolx(w7, 8))
        rw = (rcon << 24)
        t = sw ^ rw

        k0 = w0 ^ t
        k1 = w1 ^ w0 ^ t
        k2 = w2 ^ w1 ^ w0 ^ t
        k3 = w3 ^ w2 ^ w1 ^ w0 ^ t

        if (self.dump_vars):
            print("next_256bit_key_a:")
            print("w0 = 0x%08x, w0 = 0x%08x, w0 = 0x%08x, w0 = 0x%08x" % (w0, w1, w2, w3))
            print("w4 = 0x%08x, w5 = 0x%08x, w6 = 0x%08x, w7 = 0x%08x" % (w4, w5, w6, w7))
            print("t = 0x%08x, sw = 0x%08x, rw = 0x%08x" % (t, sw, rw))
            print("k0 = 0x%08x, k0 = 0x%08x, k0 = 0x%08x, k0 = 0x%08x" % (k0, k1, k2, k3))
            print("")

        return (k0, k1, k2, k3)

    def _next_256bit_key_b(self, key0, key1):
        """
        Generate the next four key words for aes-256 using algorithm B
        based on given previous eight keywords.
        """
        (w0, w1, w2, w3) = key0
        (w4, w5, w6, w7) = key1

        t = self._substw(w7)

        k0 = w0 ^ t
        k1 = w1 ^ w0 ^ t
        k2 = w2 ^ w1 ^ w0 ^ t
        k3 = w3 ^ w2 ^ w1 ^ w0 ^ t

        if (self.dump_vars):
            print("next_256bit_key_b:")
            print("w0 = 0x%08x, w0 = 0x%08x, w0 = 0x%08x, w0 = 0x%08x" % (w0, w1, w2, w3))
            print("w4 = 0x%08x, w5 = 0x%08x, w6 = 0x%08x, w7 = 0x%08x" % (w4, w5, w6, w7))
            print("t = 0x%08x" % (t))
            print("k0 = 0x%08x, k0 = 0x%08x, k0 = 0x%08x, k0 = 0x%08x" % (k0, k1, k2, k3))
            print("")

        return (k0, k1, k2, k3)

    def _key_gen256(self, key):
        """
        Generating the keys for 256 bit keys.
        """
        round_keys = []
        (k0, k1, k2, k3, k4, k5, k6, k7) = key

        round_keys.append((k0, k1, k2, k3))
        round_keys.append((k4, k5, k6, k7))

        j = 1
        for i in range(0, (AES_256_ROUNDS - 2), 2):
            k = self._next_256bit_key_a(round_keys[i], round_keys[i + 1], self._get_rcon(j))
            round_keys.append(k)
            k = self._next_256bit_key_b(round_keys[i + 1], round_keys[i + 2])
            round_keys.append(k)
            j += 1

        # One final key needs to be generated.
        k = self._next_256bit_key_a(round_keys[12], round_keys[13], self._get_rcon(7))
        round_keys.append(k)

        if (self.verbose):
            print("Input key:")
            self._print_block((k0, k1, k2, k3))
            self._print_block((k4, k5, k6, k7))
            print("")

            print("Generated keys:")
            for k in round_keys:
                self._print_block(k)
            print("")

        return round_keys

    def _get_rcon(self, round):
        """
        Function implementation of rcon. Calculates rcon for a
        given round. This could be implemented as an iterator.
        """
        rcon = 0x8d

        for i in range(0, round):
            rcon = ((rcon << 1) ^ (0x11b & - (rcon >> 7))) & 0xff

        return rcon

    def _addroundkey(self, key, block):
        """
        AES AddRoundKey block operation.
        Perform XOR combination of the given block and the given key.
        """
        (w0, w1, w2, w3) = block
        (k0, k1, k2, k3) = key

        res_block = (w0 ^ k0, w1 ^ k1, w2 ^ k2, w3 ^ k3)

        if (self.verbose):
            print("AddRoundKey key, block in and block out:")
            self._print_block(key)
            self._print_block(block)
            self._print_block(res_block)
            print("")

        return res_block

    def _mixw(self, w):
        """
        Perform bit mixing of the given words.
        """
        (b0, b1, b2, b3) = self._w2b(w)

        mb0 = self._gm2(b0) ^ self._gm3(b1) ^ b2           ^ b3
        mb1 = b0           ^ self._gm2(b1) ^ self._gm3(b2) ^ b3
        mb2 = b0           ^ b1           ^ self._gm2(b2) ^ self._gm3(b3)
        mb3 = self._gm3(b0) ^ b1           ^ b2           ^ self._gm2(b3)

        return self._b2w(mb0, mb1, mb2, mb3)

    def _mixcolumns(self, block):
        """
        AES MixColumns on the given block.
        """
        (c0, c1, c2, c3) = block

        mc0 = self._mixw(c0)
        mc1 = self._mixw(c1)
        mc2 = self._mixw(c2)
        mc3 = self._mixw(c3)

        res_block = (mc0, mc1, mc2, mc3)

        if (self.verbose):
            print("MixColumns block in and block out:")
            self._print_block(block)
            self._print_block(res_block)
            print("")

        return res_block

    def _subbytes(self, block):
        """
        AES SubBytes operation on the given block.
        """
        (w0, w1, w2, w3) = block

        res_block = (self._substw(w0), self._substw(w1),
                    self._substw(w2), self._substw(w3))

        if (self.verbose):
            print("SubBytes block in and block out:")
            self._print_block(block)
            self._print_block(res_block)
            print("")

        return res_block

    def _shiftrows(self, block):
        """
        AES ShiftRows block operation.
        """
        (w0, w1, w2, w3) = block

        c0 = self._w2b(w0)
        c1 = self._w2b(w1)
        c2 = self._w2b(w2)
        c3 = self._w2b(w3)

        ws0 = self._b2w(c0[0], c1[1],  c2[2],  c3[3])
        ws1 = self._b2w(c1[0], c2[1],  c3[2],  c0[3])
        ws2 = self._b2w(c2[0], c3[1],  c0[2],  c1[3])
        ws3 = self._b2w(c3[0], c0[1],  c1[2],  c2[3])

        res_block = (ws0, ws1, ws2, ws3)

        if (self.verbose):
            print("ShiftRows block in and block out:")
            self._print_block(block)
            self._print_block(res_block)
            print("")

        return res_block

    def _inv__mixw(self, w):
        """
        Perform inverse bit mixing of the given words.
        """
        (b0, b1, b2, b3) = self._w2b(w)

        mb0 = self.gm14(b0) ^ self._gm11(b1) ^ self._gm13(b2) ^ self._gm09(b3)
        mb1 = self._gm09(b0) ^ self.gm14(b1) ^ self._gm11(b2) ^ self._gm13(b3)
        mb2 = self._gm13(b0) ^ self._gm09(b1) ^ self.gm14(b2) ^ self._gm11(b3)
        mb3 = self._gm11(b0) ^ self._gm13(b1) ^ self._gm09(b2) ^ self.gm14(b3)

        return self._b2w(mb0, mb1, mb2, mb3)

    def _inv__mixcolumns(self, block):
        """
        AES Inverse MixColumns on the given block.
        """
        (c0, c1, c2, c3) = block

        mc0 = self._inv__mixw(c0)
        mc1 = self._inv__mixw(c1)
        mc2 = self._inv__mixw(c2)
        mc3 = self._inv__mixw(c3)

        res_block = (mc0, mc1, mc2, mc3)

        if (self.verbose):
            print("Inverse MixColumns block in and block out:")
            self._print_block(block)
            self._print_block(res_block)
            print("")

        return res_block

    def _inv__shiftrows(self, block):
        """
        AES inverse ShiftRows block operation.
        """
        (w0, w1, w2, w3) = block

        c0 = self._w2b(w0)
        c1 = self._w2b(w1)
        c2 = self._w2b(w2)
        c3 = self._w2b(w3)

        ws0 = self._b2w(c0[0], c3[1],  c2[2],  c1[3])
        ws1 = self._b2w(c1[0], c0[1],  c3[2],  c2[3])
        ws2 = self._b2w(c2[0], c1[1],  c0[2],  c3[3])
        ws3 = self._b2w(c3[0], c2[1],  c1[2],  c0[3])

        res_block = (ws0, ws1, ws2, ws3)

        if (self.verbose):
            print("Inverse ShiftRows block in and block out:")
            self._print_block(block)
            self._print_block(res_block)
            print("")

        return res_block

    def _inv__subbytes(self, block):
        """
        AES inverse SubBytes operation on the given block.
        """
        (w0, w1, w2, w3) = block

        res_block = (self._inv__substw(w0), self._inv__substw(w1),
                     self._inv__substw(w2), self._inv__substw(w3))

        if (self.verbose):
            print("Inverse SubBytes block in and block out:")
            self._print_block(block)
            self._print_block(res_block)
            print("")

        return res_block
