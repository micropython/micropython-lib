import unittest
from uaes import AesCypher

nist_aes128_key = (0x2b7e1516, 0x28aed2a6, 0xabf71588, 0x09cf4f3c)
nist_aes256_key = (0x603deb10, 0x15ca71be, 0x2b73aef0, 0x857d7781,
                   0x1f352c07, 0x3b6108d7, 0x2d9810a3, 0x0914dff4)

class TestAes(unittest.TestCase):
    def setUp(self):
        self.cypher = AesCypher(verbose=False, dump_vars=False)

class TestAesMixColumns():
    def test_mixcolumns(self):

        print("Test of _mixcolumns and inverse _mixcolumns:")
        mixresult = self._mixcolumns(nist_aes128_key)
        inv_mixresult = self._inv__mixcolumns(mixresult)

        print("Test of _mixw ochi _inv__mixw:")
        testw = 0xdb135345
        expw  = 0x8e4da1bc
        mixresult = self._mixw(testw)
        inv_mixresult = self._inv__mixw(mixresult)
        print("Testword:   0x%08x" % testw)
        print("expexted:   0x%08x" % expw)
        print("_mixword:    0x%08x" % mixresult)
        print("inv_mixword: 0x%08x" % inv_mixresult)


class TestAesCypher128Bits(TestAes):
    """
    Plain text and expected values come from: https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Standards-and-Guidelines/documents/examples/AES_Core128.pdf
    """
    def _test_aes_cypher_128_bits(self, plain_text, expected):
        result = self.cypher.aes_encipher_block(nist_aes128_key, plain_text)
        self.assertEqual(result, expected)

    def test_aes_1(self):
        plain_text = (0x6bc1bee2, 0x2e409f96, 0xe93d7e11, 0x7393172a)
        expected = (0x3ad77bb4, 0x0d7a3660, 0xa89ecaf3, 0x2466ef97)

        self._test_aes_cypher_128_bits(plain_text, expected)

    def test_aes_2(self):
        plain_text = (0xae2d8a57, 0x1e03ac9c, 0x9eb76fac, 0x45af8e51)
        expected = (0xf5d3d585, 0x03b9699d, 0xe785895a, 0x96fdbaaf)

        self._test_aes_cypher_128_bits(plain_text, expected)

    def test_aes_3(self):
        plain_text = (0x30c81c46, 0xa35ce411, 0xe5fbc119, 0x1a0a52ef)
        expected = (0x43b1cd7f, 0x598ece23, 0x881b00e3, 0xed030688)

        self._test_aes_cypher_128_bits(plain_text, expected)

    def test_aes_4(self):
        plain_text = (0xf69f2445, 0xdf4f9b17, 0xad2b417b, 0xe66c3710)
        expected = (0x7b0c785e, 0x27e8ad3f, 0x82232071, 0x04725dd4)

        self._test_aes_cypher_128_bits(plain_text, expected)

class TestAesCypher256Bits(TestAes):
    """
    Plain text and expected values come from: https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Standards-and-Guidelines/documents/examples/AES_Core256.pdf
    """
    def _test_aes_cypher_256_bits(self, plain_text, expected):
        result = self.cypher.aes_encipher_block(nist_aes256_key, plain_text)
        self.assertEqual(result, expected)

    def test_aes_1(self):
        plain_text = (0x6bc1bee2, 0x2e409f96, 0xe93d7e11, 0x7393172a)
        expected = (0xf3eed1bd, 0xb5d2a03c, 0x064b5a7e, 0x3db181f8)

        self._test_aes_cypher_256_bits(plain_text, expected)

    def test_aes_2(self):
        plain_text = (0xae2d8a57, 0x1e03ac9c, 0x9eb76fac, 0x45af8e51)
        expected = (0x591ccb10, 0xd410ed26, 0xdc5ba74a, 0x31362870)

        self._test_aes_cypher_256_bits(plain_text, expected)

    def test_aes_3(self):
        plain_text = (0x30c81c46, 0xa35ce411, 0xe5fbc119, 0x1a0a52ef)
        expected = (0xb6ed21b9, 0x9ca6f4f9, 0xf153e7b1, 0xbeafed1d)

        self._test_aes_cypher_256_bits(plain_text, expected)

    def test_aes_4(self):
        plain_text = (0xf69f2445, 0xdf4f9b17, 0xad2b417b, 0xe66c3710)
        expected = (0x23304b7a, 0x39f9f3ff, 0x067d8d8f, 0x9e24ecc7)

        self._test_aes_cypher_256_bits(plain_text, expected)

class TestAesDecypher128Bits(TestAes):
    """
    Plain text and expected values come from: https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Standards-and-Guidelines/documents/examples/AES_Core128.pdf
    """
    def _test_aes_decypher_128_bits(self, cipher_text, expected):
        result = self.cypher.aes_decipher_block(nist_aes128_key, cipher_text)
        self.assertEqual(result, expected)

    def test_aes_1(self):
        plain_text = (0x6bc1bee2, 0x2e409f96, 0xe93d7e11, 0x7393172a)
        cipher_text = (0x3ad77bb4, 0x0d7a3660, 0xa89ecaf3, 0x2466ef97)

        self._test_aes_decypher_128_bits(cipher_text, plain_text)

    def test_aes_2(self):
        plain_text = (0xae2d8a57, 0x1e03ac9c, 0x9eb76fac, 0x45af8e51)
        cipher_text = (0xf5d3d585, 0x03b9699d, 0xe785895a, 0x96fdbaaf)

        self._test_aes_decypher_128_bits(cipher_text, plain_text)

    def test_aes_3(self):
        plain_text = (0x30c81c46, 0xa35ce411, 0xe5fbc119, 0x1a0a52ef)
        cipher_text = (0x43b1cd7f, 0x598ece23, 0x881b00e3, 0xed030688)

        self._test_aes_decypher_128_bits(cipher_text, plain_text)

    def test_aes_4(self):
        plain_text = (0xf69f2445, 0xdf4f9b17, 0xad2b417b, 0xe66c3710)
        cipher_text = (0x7b0c785e, 0x27e8ad3f, 0x82232071, 0x04725dd4)

        self._test_aes_decypher_128_bits(cipher_text, plain_text)

class TestAesDecypher256Bits(TestAes):
    """
    Plain text and expected values come from: https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Standards-and-Guidelines/documents/examples/AES_Core256.pdf
    """
    def _test_aes_decypher_256_bits(self, cipher_text, expected):
        result = self.cypher.aes_decipher_block(nist_aes256_key, cipher_text)
        self.assertEqual(result, expected)

    def test_aes_1(self):
        plain_text = (0x6bc1bee2, 0x2e409f96, 0xe93d7e11, 0x7393172a)
        cipher_text = (0xf3eed1bd, 0xb5d2a03c, 0x064b5a7e, 0x3db181f8)

        self._test_aes_decypher_256_bits(cipher_text, plain_text)

    def test_aes_2(self):
        plain_text = (0xae2d8a57, 0x1e03ac9c, 0x9eb76fac, 0x45af8e51)
        cipher_text = (0x591ccb10, 0xd410ed26, 0xdc5ba74a, 0x31362870)

        self._test_aes_decypher_256_bits(cipher_text, plain_text)

    def test_aes_3(self):
        plain_text = (0x30c81c46, 0xa35ce411, 0xe5fbc119, 0x1a0a52ef)
        cipher_text = (0xb6ed21b9, 0x9ca6f4f9, 0xf153e7b1, 0xbeafed1d)

        self._test_aes_decypher_256_bits(cipher_text, plain_text)

    def test_aes_4(self):
        plain_text = (0xf69f2445, 0xdf4f9b17, 0xad2b417b, 0xe66c3710)
        cipher_text = (0x23304b7a, 0x39f9f3ff, 0x067d8d8f, 0x9e24ecc7)

        self._test_aes_decypher_256_bits(cipher_text, plain_text)


if __name__ == "__main__":
    unittest.main()