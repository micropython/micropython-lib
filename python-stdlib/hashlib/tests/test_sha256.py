# Prevent importing any built-in hashes, so this test tests only the pure Python hashes.
import sys
sys.modules['uhashlib'] = sys

import unittest
from hashlib import sha256


class TestSha256(unittest.TestCase):
    a_str = b"just a test string"
    b_str = b"some other string for testing"
    c_str = b"nothing to see here"

    def test_empty(self):
        self.assertEqual(
            b"\xe3\xb0\xc4B\x98\xfc\x1c\x14\x9a\xfb\xf4\xc8\x99o\xb9$'\xaeA\xe4d\x9b\x93L\xa4\x95\x99\x1bxR\xb8U",
            sha256().digest(),
        )

    def test_empty_hex(self):
        self.assertEqual(
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            sha256().hexdigest(),
        )

    def test_str(self):
        self.assertEqual(
            b"\xd7\xb5S\xc6\xf0\x9a\xc8]\x14$\x15\xf8W\xc51\x0f;\xbb\xe7\xcd\xd7\x87\xcc\xe4\xb9\x85\xac\xed\xd5\x85&o",
            sha256(self.a_str).digest(),
        )
        self.assertEqual(
            b'|\x80Q\xb2\xa0u\xf0g\xe3\xc45\xce1p\xc6I\xb6r\x19J&\x8b\xdc\xa5"\x00?A\x90\xba\xbd,',
            sha256(self.b_str).digest(),
        )

    def test_str_hex(self):
        self.assertEqual(
            "d7b553c6f09ac85d142415f857c5310f3bbbe7cdd787cce4b985acedd585266f",
            sha256(self.a_str).hexdigest(),
        )
        self.assertEqual(
            "7c8051b2a075f067e3c435ce3170c649b672194a268bdca522003f4190babd2c",
            sha256(self.b_str).hexdigest(),
        )

    def test_long_str(self):
        self.assertEqual(
            "f1f1af5d66ba1789f8214354c0ed04856bbe43c01aa392c584ef1ec3dbf45482",
            sha256(self.a_str * 123).hexdigest(),
        )

    def test_update(self):
        s = sha256(self.a_str)
        s.update(self.b_str)
        self.assertEqual(
            "fc7f204eb969ca3f10488731fa63910486adda7c2ae2ee2142e85414454c6d42", s.hexdigest()
        )

    def test_repeat_final(self):
        s = sha256(self.a_str)
        s.update(self.b_str)
        self.assertEqual(
            "fc7f204eb969ca3f10488731fa63910486adda7c2ae2ee2142e85414454c6d42", s.hexdigest()
        )
        self.assertEqual(
            "fc7f204eb969ca3f10488731fa63910486adda7c2ae2ee2142e85414454c6d42", s.hexdigest()
        )
        s.update(self.c_str)
        self.assertEqual(
            "b707db9ae915b0f6f9a67ded8c9932999ee7e9dfb33513b084ea9384f5ffb082", s.hexdigest()
        )

    def test_copy(self):
        s = sha256(self.a_str)
        s2 = s.copy()
        s.update(self.b_str)
        s2.update(self.c_str)
        self.assertEqual(
            "fc7f204eb969ca3f10488731fa63910486adda7c2ae2ee2142e85414454c6d42", s.hexdigest()
        )
        self.assertEqual(
            "6a340b2bd2b63f4a0f9bb7566c26831354ee6ed17d1187d3a53627181fcb2907", s2.hexdigest()
        )


if __name__ == "__main__":
    unittest.main()
