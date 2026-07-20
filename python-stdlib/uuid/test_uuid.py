import unittest
import uuid


class TestUUID(unittest.TestCase):
    def test_unique(self):
        n = 10
        us = set(uuid.uuid4().bytes for _ in range(n))
        self.assertEqual(len(us), n)

    def test_len(self):
        u = uuid.uuid4()
        self.assertEqual(len(u.bytes), 16)
        self.assertEqual(len(u.hex), 32)
        self.assertEqual(len(str(u)), 36)

    def test_repr(self):
        u = str(repr(uuid.uuid4()))
        self.assertTrue(u.startswith("<UUID"))
        self.assertTrue(u.endswith(">"))

    def test_constructor(self):
        u1 = uuid.uuid4()
        u2 = uuid.UUID(bytes.fromhex(u1.hex))
        self.assertEqual(u1.hex, u2.hex)


if __name__ == "__main__":
    unittest.main()
