# This makes unittest return an error code, so is not named "test_xxx.py".

import unittest


def broken_func():
    raise ValueError("uh oh!")


def test_func():
    broken_func()


if __name__ == "__main__":
    unittest.main()
