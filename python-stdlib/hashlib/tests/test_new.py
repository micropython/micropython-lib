import unittest
import hashlib


class TestNew(unittest.TestCase):
    def test_sha224(self):
        self.assertEqual(
            hashlib.new("sha224", b"1234").digest(),
            b"\x99\xfb/H\xc6\xafGa\xf9\x04\xfc\x85\xf9^\xb5a\x90\xe5\xd4\x0b\x1fD\xec:\x9c\x1f\xa3\x19",
        )

    def test_sha256(self):
        self.assertEqual(
            hashlib.new("sha256", b"1234").digest(),
            b"\x03\xacgB\x16\xf3\xe1\\v\x1e\xe1\xa5\xe2U\xf0g\x956#\xc8\xb3\x88\xb4E\x9e\x13\xf9x\xd7\xc8F\xf4",
        )

    def test_sha384(self):
        self.assertEqual(
            hashlib.new("sha384", b"1234").digest(),
            b"PO\x00\x8c\x8f\xcf\x8b.\xd5\xdf\xcd\xe7R\xfcTd\xab\x8b\xa0d!]\x9c[_\xc4\x86\xaf=\x9a\xb8\xc8\x1b\x14xQ\x80\xd2\xad|\xee\x1a\xb7\x92\xadDy\x8c",
        )

    def test_sha512(self):
        self.assertEqual(
            hashlib.new("sha512", b"1234").digest(),
            b"\xd4\x04U\x9f`.\xabo\xd6\x02\xacv\x80\xda\xcb\xfa\xad\xd1603^\x95\x1f\tz\xf3\x90\x0e\x9d\xe1v\xb6\xdb(Q/.\x00\x0b\x9d\x04\xfb\xa5\x13>\x8b\x1cn\x8d\xf5\x9d\xb3\xa8\xab\x9d`\xbeK\x97\xcc\x9e\x81\xdb",
        )


if __name__ == "__main__":
    unittest.main()
