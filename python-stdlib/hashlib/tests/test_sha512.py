import unittest
from hashlib import sha512


class Testsha512(unittest.TestCase):
    a_str = b"just a test string"
    b_str = b"some other string for testing"
    c_str = b"nothing to see here"

    def test_empty(self):
        self.assertEqual(
            b"\xcf\x83\xe15~\xef\xb8\xbd\xf1T(P\xd6m\x80\x07\xd6 \xe4\x05\x0bW\x15\xdc\x83\xf4\xa9!\xd3l\xe9\xceG\xd0\xd1<]\x85\xf2\xb0\xff\x83\x18\xd2\x87~\xec/c\xb91\xbdGAz\x81\xa582z\xf9'\xda>",
            sha512().digest(),
        )

    def test_empty_hex(self):
        self.assertEqual(
            "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e",
            sha512().hexdigest(),
        )

    def test_str(self):
        self.assertEqual(
            b"h\xbeLfd\xaf\x86}\xd1\xd0\x1c\x8dw\xe9c\xd8}w\xb7\x02@\x0c\x8f\xab\xae5ZA\xb8\x92zZU3\xa7\xf1\xc2\x85\t\xbb\xd6\\_:\xc7\x16\xf3;\xe2q\xfb\xda\x0c\xa0\x18\xb7\x1a\x84p\x8c\x9f\xae\x8aS",
            sha512(self.a_str).digest(),
        )
        self.assertEqual(
            b"Tt\xd1\xf8\x1fh\x14\xba\x85\x1a\x84\x15\x9b(\x812\x8er\x8d\xdeN\xc0\xe2\xff\xbb\xcc$i\x18gh\x18\xc4\xcb?\xc0\xa0\nTl\x0f\x01J\x07eP\x19\x98\xd9\xebZ\xd2?\x1cj\xa8Q)!\x18\xab!!~",
            sha512(self.b_str).digest(),
        )

    def test_str_hex(self):
        self.assertEqual(
            "68be4c6664af867dd1d01c8d77e963d87d77b702400c8fabae355a41b8927a5a5533a7f1c28509bbd65c5f3ac716f33be271fbda0ca018b71a84708c9fae8a53",
            sha512(self.a_str).hexdigest(),
        )
        self.assertEqual(
            "5474d1f81f6814ba851a84159b2881328e728dde4ec0e2ffbbcc246918676818c4cb3fc0a00a546c0f014a0765501998d9eb5ad23f1c6aa851292118ab21217e",
            sha512(self.b_str).hexdigest(),
        )

    def test_long_str(self):
        self.assertEqual(
            "8ee045cd8faf900bb23d13754d65723404a224030af827897cde92a40f7a1202405bc3efe5466c7e4833e7a9a5b9f9278ebe4c968e7fa662d8addc17ba95cc73",
            sha512(self.a_str * 123).hexdigest(),
        )

    def test_update(self):
        s = sha512(self.a_str)
        s.update(self.b_str)
        self.assertEqual(
            "3fa253e7b093d5bc7b31f613f03833a4d39341cf73642349a46f26b39b5d95c97bb4e16fc588bda81d5c7a2db62cfca5c4c71a142cf02fd78409bffe5e4f408c",
            s.hexdigest(),
        )

    def test_repeat_final(self):
        s = sha512(self.a_str)
        s.update(self.b_str)
        self.assertEqual(
            "3fa253e7b093d5bc7b31f613f03833a4d39341cf73642349a46f26b39b5d95c97bb4e16fc588bda81d5c7a2db62cfca5c4c71a142cf02fd78409bffe5e4f408c",
            s.hexdigest(),
        )
        self.assertEqual(
            "3fa253e7b093d5bc7b31f613f03833a4d39341cf73642349a46f26b39b5d95c97bb4e16fc588bda81d5c7a2db62cfca5c4c71a142cf02fd78409bffe5e4f408c",
            s.hexdigest(),
        )
        s.update(self.c_str)
        self.assertEqual(
            "4b0827d5a28eeb2ebbeec270d7c775e78d5a76251753b8242327ffa2b1e5662a655be44bc09e41fcc0805bccd79cee13f4c41c40acff6fc1cf69b311d9b08f55",
            s.hexdigest(),
        )

    def test_copy(self):
        s = sha512(self.a_str)
        s2 = s.copy()
        s.update(self.b_str)
        s2.update(self.c_str)
        self.assertEqual(
            "3fa253e7b093d5bc7b31f613f03833a4d39341cf73642349a46f26b39b5d95c97bb4e16fc588bda81d5c7a2db62cfca5c4c71a142cf02fd78409bffe5e4f408c",
            s.hexdigest(),
        )
        self.assertEqual(
            "2e4d68ec2d2836f24718b24442db027141fd2f7e06fb11c1460b013017feb0e74dea9d9415abe51b729ad86792bd5cd2cec9567d58a47a03785028376e7a5cc1",
            s2.hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
