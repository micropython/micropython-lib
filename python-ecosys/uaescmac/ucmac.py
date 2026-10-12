#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#=======================================================================
# Author: Joachim Strömbergson
# Copyright (c) 2016, Secworks Sweden AB
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

from uaes import AesCypher

R128 = (0, 0, 0, 0x00000087)
MAX128 = ((2**128) - 1)
AES_BLOCK_LENGTH = 128
AES_BLOCK_BYTES_LENGTH = int(AES_BLOCK_LENGTH / 4)
SUB_BLOCK_BYTES_LENGTH = 8


class CmacHasher():
    def __init__(self, key=(0x00000000, 0x00000000, 0x00000000, 0x00000000), verbose = False):
        self.verbose = verbose
        self.cypher = AesCypher(verbose=verbose, dump_vars=verbose)
        self.current_block = b''
        self.message = []
        self.key = key

    def pad_block(self, block_in_bytes):
        """
        Pads a given block with the "1000...." padding.

        Parameters
        ----------
        block_in_bytes : bytes array
            bytes array to complete with the appropriate padding

        Returns
        -------
        tuple(int, int, int, int)
            Block with padding split in the cmac block format
        """
        if len(block_in_bytes) < AES_BLOCK_BYTES_LENGTH:
            block_in_bytes += b'8'
            block_in_bytes += b'0' * (AES_BLOCK_BYTES_LENGTH - len(block_in_bytes))

        return self._bytes_to_block(block_in_bytes)

    def update(self, bytes_value):
        """
        Adds the given bytes value to the current block.
        If the current block reaches the CMAC block size, the bytes array
        is converted into a block of 4 integers and added to the message.

        Parameters
        ----------
        bytes_value : bytes array
            Hexadecimal value to concatenate in the message
        """
        free_space = AES_BLOCK_BYTES_LENGTH - len(self.current_block)
        n_extra_bytes = len(bytes_value) - free_space

        if n_extra_bytes > 0:
            while(n_extra_bytes > 0):
                self.current_block += bytes_value[:free_space]
                self._update_message()

                self.current_block = b''
                bytes_value = bytes_value[free_space:]
                free_space = AES_BLOCK_BYTES_LENGTH - len(self.current_block)
                n_extra_bytes = len(bytes_value) - free_space

            self.current_block = bytes_value
        else:
            self.current_block += bytes_value
            if n_extra_bytes == 0:
                self._update_message()
                self.current_block = b''

    def xor_words(self, a, b):
        """
        Apply an XOR operator element to element between a and b.

        Parameters
        ----------
        a : tuple(int, int, int, int)
            Tuple of four integers to be 'xor-ed' with b
        b : tuple(int, int, int, int)
            Tuple of four integers to be 'xor-ed' with a

        Returns
        -------
        tuple(int, int, int, int)
            Result of the element to element xor operation.
        """
        c = (a[0] ^ b[0], a[1] ^ b[1], a[2] ^ b[2], a[3] ^ b[3])
        if (self.verbose):
            print("XORing words in the following two 128 bit block gives the result:")
            self.cypher.print_block(a)
            self.cypher.print_block(b)
            self.cypher.print_block(c)
        return c

    def cmac_gen_subkeys(self, key):
        """
        Generate subkeys K1 and K2.
        K1 is used to generate complete message, i.e. where all blocks contain
        128 bits of information.
        K2 is used to generate incomplete messages, i.e with a final block length
        lower than 128 bits.

        Parameters
        ----------
        key : tuple
            128 or 256 bits key to compute the aes cmac key

        Returns
        -------
        tuple
            K1 and K2
        """
        L = self.cypher.aes_encipher_block(key, (0, 0, 0, 0))
        Pre_K1 = self._shift_words(L)
        MSBL = (L[0] >> 31) & 0x01
        if MSBL:
            K1 = self.xor_words(Pre_K1, R128)
        else:
            K1 = Pre_K1

        Pre_K2 = self._shift_words(K1)
        MSBK1 = (K1[0] >> 31) & 0x01
        if MSBK1:
            K2 = self.xor_words(Pre_K2, R128)
        else:
            K2 = Pre_K2

        if (self.verbose):
            print("Internal data during sub key generation")
            print("---------------------------------------")
            print("L:")
            self.cypher.print_block(L)

            print("MSBL = 0x%01x" % MSBL)
            print("Pre_K1:")
            self.cypher.print_block(Pre_K1)
            print("K1:")
            self.cypher.print_block(K1)
            print("MSBK1 = 0x%01x" % MSBK1)
            print("Pre_K2:")
            self.cypher.print_block(Pre_K2)
            print("K2:")
            self.cypher.print_block(K2)
            print()

        return (K1, K2)

    def digest(self):
        """
        Hash the message given to the hasher.
        The message is a list of 4-integers blocks, if the last block
        does not contain 128 bits of information, it will be padded.

        Returns
        -------
        bytes array
            Hash value for the given message
        """
        import struct
        key = self.key
        final_length = len(self.current_block) * 4 if len(self.current_block) != 0 else AES_BLOCK_LENGTH

        message = self.message

        # Start by generating the subkeys
        (K1, K2) = self.cmac_gen_subkeys(key)
        print("CMAC Subkeys generated.")
        state = (0x00000000, 0x00000000, 0x00000000, 0x00000000)
        blocks = len(message) if final_length == AES_BLOCK_LENGTH else len(message) + 1

        if blocks == 0:
            # Empty message.
            paddded_block = self.pad_block(self.current_block)
            tweak = self.xor_words(paddded_block, K2)
            if (self.verbose):
                print("tweak empty block")
                self.cypher.print_block(tweak)
            cmac_hash = self.cypher.aes_encipher_block(key, tweak)

        else:
            for i in range(blocks - 1):
                state = self.xor_words(state, message[i])
                if (self.verbose):
                    print("state before aes block %d:" % (i + 1))
                    self.cypher.print_block(state)
                state = self.cypher.aes_encipher_block(key, state)
                if (self.verbose):
                    print("state after aes block %d:" % (i + 1))
                    self.cypher.print_block(state)

            if (final_length == AES_BLOCK_LENGTH):
                tweak = self.xor_words(K1, message[-1])
                if (self.verbose):
                    print("tweak complete final block")
                    self.cypher.print_block(tweak)

            else:
                padded_block = self.pad_block(self.current_block)
                tweak = self.xor_words(K2, padded_block)
                if (self.verbose):
                    print("tweak incomplete final block")
                    self.cypher.print_block(tweak)

        state = self.xor_words(state, tweak)
        if (self.verbose):
            print("state before aes final block:")
            self.cypher.print_block(state)
        cmac_hash = self.cypher.aes_encipher_block(key, state)
        if (self.verbose):
            print("state after aes final block:")
            self.cypher.print_block(cmac_hash)

        print("CMAC hash generated: ", cmac_hash)
        cmac_hash = struct.pack('<IIII', *cmac_hash)
        print("CMAC hash (bytes): ", cmac_hash)
        return cmac_hash

    def _bytes_to_block(self, block_in_bytes):
        sub_blocks = []
        for sb_start in range(0, AES_BLOCK_BYTES_LENGTH, SUB_BLOCK_BYTES_LENGTH):
            sub_blocks.append(int("0x" + block_in_bytes[sb_start:sb_start + SUB_BLOCK_BYTES_LENGTH].decode()) )

        return tuple(sub_blocks)

    def _update_message(self):
        block = self._bytes_to_block(self.current_block)
        self.message.append(block)

    def _shift_words(self, wl):
        w = ((wl[0] << 96) + (wl[1] << 64) + (wl[2] << 32) + wl[3]) & MAX128
        ws = w << 1 & MAX128
        return ((ws >> 96) & 0xffffffff, (ws >> 64) & 0xffffffff,
                (ws >> 32) & 0xffffffff, ws & 0xffffffff)
