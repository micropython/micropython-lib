import os
import tempfile
import unittest


class Base(unittest.TestCase):
    def assertExists(self, fn):
        os.stat(fn)

    def assertNotExists(self, fn):
        with self.assertRaises(OSError):
            os.stat(fn)


class TestMkdtemp(Base):
    def test_no_args(self):
        fn = tempfile.mkdtemp()
        self.assertTrue(fn.startswith("/tmp"))
        self.assertExists(fn)
        os.rmdir(fn)

    def test_prefix(self):
        fn = tempfile.mkdtemp(prefix="foo")
        self.assertTrue(fn.startswith("/tmp"))
        self.assertTrue("foo" in fn)
        self.assertFalse(fn.endswith("foo"))
        self.assertExists(fn)
        os.rmdir(fn)

    def test_suffix(self):
        fn = tempfile.mkdtemp(suffix="foo")
        self.assertTrue(fn.startswith("/tmp"))
        self.assertTrue(fn.endswith("foo"))
        self.assertExists(fn)
        os.rmdir(fn)

    def test_dir(self):
        fn = tempfile.mkdtemp(dir="tmp_micropython")
        self.assertTrue(fn.startswith("tmp_micropython"))
        self.assertExists(fn)
        os.rmdir(fn)


class TestTemporaryDirectory(Base):
    def test_context_manager_no_args(self):
        with tempfile.TemporaryDirectory() as fn:
            self.assertTrue(isinstance(fn, str))
            self.assertTrue(fn.startswith("/tmp"))
            self.assertExists(fn)
        self.assertNotExists(fn)
