"""
Don't use ``tempfile`` in these tests, as ``tempfile`` relies on ``shutil``.
"""

import os
import shutil
import unittest


class TestRmtree(unittest.TestCase):
    def test_dir_dne(self):
        with self.assertRaises(OSError):
            os.stat("foo")

        with self.assertRaises(OSError):
            shutil.rmtree("foo")

    def test_file(self):
        fn = "foo"
        with open(fn, "w"):
            pass

        with self.assertRaises(OSError):
            shutil.rmtree(fn)

        os.remove(fn)

    def test_empty_dir(self):
        with self.assertRaises(OSError):
            # If this triggers, a previous test didn't clean up.
            # bit of a chicken/egg situation with ``tempfile``
            os.stat("foo")

        os.mkdir("foo")
        shutil.rmtree("foo")

        with self.assertRaises(OSError):
            os.stat("foo")

    def test_dir(self):
        with self.assertRaises(OSError):
            # If this triggers, a previous test didn't clean up.
            # bit of a chicken/egg situation with ``tempfile``
            os.stat("foo")

        os.mkdir("foo")
        os.mkdir("foo/bar")
        with open("foo/bar/baz1.txt", "w"):
            pass
        with open("foo/bar/baz2.txt", "w"):
            pass

        shutil.rmtree("foo")

        with self.assertRaises(OSError):
            os.stat("foo")
