import unittest
from ucmac import CmacHasher
import struct

test_sub_block_bytes = b'12345678'
test_sub_block_int = 305419896
test_block = (test_sub_block_int, test_sub_block_int, test_sub_block_int, test_sub_block_int)

class TestCmac(unittest.TestCase):
    def setUp(self):
        self.hasher = CmacHasher()


class TestCmacUpdate(TestCmac):
    def test_update_empty_message(self):
        self.hasher.update(b'12345')
        self.assertEqual(b'12345', self.hasher.current_block)
        self.assertEqual(self.hasher.message, [])

    def test_update_message_enough_space(self):
        self.hasher.current_block = b'12345'
        self.hasher.update(b'678')
        self.assertEqual(test_sub_block_bytes, self.hasher.current_block)
        self.assertEqual(self.hasher.message, [])

    def test_update_message_exact_space(self):
        self.hasher.current_block = test_sub_block_bytes + test_sub_block_bytes
        self.hasher.update(test_sub_block_bytes + test_sub_block_bytes)
        self.assertEqual(b'', self.hasher.current_block)
        self.assertEqual(self.hasher.message, [(test_sub_block_int,
                                                 test_sub_block_int,
                                                 test_sub_block_int,
                                                 test_sub_block_int
                                                )])
    
    def test_update_message_extra_bytes(self):
        self.hasher.current_block = b'12345678123456781234567812'
        self.hasher.update(b'34567812345')
        self.assertEqual(b'12345', self.hasher.current_block)
        self.assertEqual(self.hasher.message, [test_block])

    def test_update_message_extra_block(self):
        self.hasher.current_block = b'12345678123456781234567812'
        self.hasher.update(b'3456781234567812345678123456781234567812345')
        self.assertEqual(self.hasher.current_block, b'12345')
        self.assertEqual(len(self.hasher.message), 2)
        self.assertEqual(self.hasher.message, [test_block, 
                                                test_block])


class TestCmacXor(TestCmac):
    def test_xor(self):
        a = (0x00000000, 0x55555555, 0xaaaaaaaa, 0xff00ff00)
        b = (0xdeadbeef, 0xaa00aa00, 0x55555555, 0xffffffff)
        c = self.hasher.xor_words(a , b)
        self.assertEqual((0xdeadbeef, 0xff55ff55, 0xffffffff, 0x00ff00ff), c)


class TestCmacSubkeyGenerator(TestCmac):
    def test_cmac_subkey_gen(self):
        """
        Test the subkey functionality by itself. Testvectors are
        from the first examples in NISTs test case suite.
        """
        nist_key128 = (0x2b7e1516, 0x28aed2a6, 0xabf71588, 0x09cf4f3c)
        nist_exp_k1 = (0xfbeed618, 0x35713366, 0x7c85e08f, 0x7236a8de)
        nist_exp_k2 = (0xf7ddac30, 0x6ae266cc, 0xf90bc11e, 0xe46d513b)

        (K1, K2) = self.hasher.cmac_gen_subkeys(nist_key128)

        self.assertEqual(K1, nist_exp_k1)
        self.assertEqual(K2, nist_exp_k2)


class TestCmacDigest(unittest.TestCase):
    def setUp(self):
        key = (0x2b7e1516, 0x28aed2a6, 0xabf71588, 0x09cf4f3c)
        self.hasher = CmacHasher(key)

    def test_zero_length_message(self):
        expected = (0xbb1d6929, 0xe9593728, 0x7fa37d12, 0x9b756746)
        digest = struct.unpack('<IIII', self.hasher.digest())
        self.assertEqual(digest, expected)

    def test_message_1_block(self):
        expected = (0x070a16b4, 0x6b4d4144, 0xf79bdd9d, 0xd04a287c)
        self.hasher.message = [(0x6bc1bee2, 0x2e409f96, 0xe93d7e11, 0x7393172a)]
        digest = struct.unpack('<IIII', self.hasher.digest())
        self.assertEqual(digest, expected)

    def test_message_one_and_quart_blocks(self):
        expected = (0x7d85449e, 0xa6ea19c8, 0x23a7bf78, 0x837dfade)
        self.hasher.message = [(0x6bc1bee2, 0x2e409f96, 0xe93d7e11, 0x7393172a)]
        self.hasher.current_block = b"ae2d8a57"
        digest = struct.unpack('<IIII', self.hasher.digest())
        self.assertEqual(digest, expected)

    def test_message_incomplete_last_block(self):
        expected = (0x72675e5d, 0x1289f7f3, 0x96166b1d, 0xd5e38149)
        self.hasher.message = [(0x6bc1bee2, 0x2e409f96, 0xe93d7e11, 0x7393172a)]
        self.hasher.current_block = b"ae2d8a"
        digest = struct.unpack('<IIII', self.hasher.digest())
        self.assertEqual(digest, expected)

    def test_message_four_blocks(self):
        print("128 bit key, four block message.")
        expected = (0x51f0bebf, 0x7e3b9d92, 0xfc497417, 0x79363cfe)
        self.hasher.message = [(0x6bc1bee2, 0x2e409f96, 0xe93d7e11, 0x7393172a),
                   (0xae2d8a57, 0x1e03ac9c, 0x9eb76fac, 0x45af8e51),
                   (0x30c81c46, 0xa35ce411, 0xe5fbc119, 0x1a0a52ef),
                   (0xf69f2445, 0xdf4f9b17, 0xad2b417b, 0xe66c3710)]
        digest = struct.unpack('<IIII', self.hasher.digest())
        self.assertEqual(digest, expected)


class TestCmacDigestKey256Bits(unittest.TestCase):
    def setUp(self):
        nist_key256 = (0x603deb10, 0x15ca71be, 0x2b73aef0, 0x857d7781,
                       0x1f352c07, 0x3b6108d7, 0x2d9810a3, 0x0914dff4)
        self.hasher = CmacHasher(key=nist_key256)

    def test_digest_zero_length_message(self):
        expected = (0x028962f6, 0x1b7bf89e, 0xfc6b551f, 0x4667d983)
        self.hasher.message = []
        digest = struct.unpack('<IIII', self.hasher.digest())
        self.assertEqual(digest, expected)

    def test_digest_four_blocks_message(self):
        expected = (0xe1992190, 0x549f6ed5, 0x696a2c05, 0x6c315410)
        self.hasher.message = [(0x6bc1bee2, 0x2e409f96, 0xe93d7e11, 0x7393172a),
                                (0xae2d8a57, 0x1e03ac9c, 0x9eb76fac, 0x45af8e51),
                                (0x30c81c46, 0xa35ce411, 0xe5fbc119, 0x1a0a52ef),
                                (0xf69f2445, 0xdf4f9b17, 0xad2b417b, 0xe66c3710)]
        digest = struct.unpack('<IIII', self.hasher.digest())
        self.assertEqual(digest, expected)

class TestCmacPadding(TestCmac):
    def test_padding_empty_block(self):
        padded_block = self.hasher.pad_block(b'')
        self.assertEqual(padded_block, (0x80000000, 0x00000000, 0x00000000, 0x00000000))

    def test_padding_first_block_complete(self):
        padded_block = self.hasher.pad_block(b'12345678')
        self.assertEqual(padded_block, (0x12345678, 0x80000000, 0x00000000, 0x00000000))

    def test_padding_first_block_incomplete(self):
        padded_block = self.hasher.pad_block(b'1234567')
        self.assertEqual(padded_block, (0x12345678, 0x00000000, 0x00000000, 0x00000000))

    def test_padding_all_blocks_complete(self):
        padded_block = self.hasher.pad_block(b'12345678123456781234567812345678')
        self.assertEqual(padded_block, (0x12345678, 0x12345678, 0x12345678, 0x12345678))

if __name__ == "__main__":
    unittest.main()
