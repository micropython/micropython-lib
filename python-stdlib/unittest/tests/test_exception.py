import unittest


def broken_func():
    raise ValueError("uh oh!")


def test_func():
    broken_func()


if __name__ == "__main__":
    unittest.main()
