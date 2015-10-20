import unittest
from contextlib import closing, suppress


class ClosingTestCase(unittest.TestCase):

    class Closable:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    def test_closing(self):
        closable = self.Closable()
        with closing(closable) as c:
            self.assertFalse(c.closed)
        self.assertTrue(closable.closed)

    def test_closing_after_error(self):
        closable = self.Closable()
        exc = Exception()
        try:
            with closing(closable) as c:
                raise exc
        except Exception as e:
            self.assertEqual(exc, e)
        self.assertTrue(closable.closed)


class SuppressTestCase(unittest.TestCase):

    def test_suppress(self):
        with suppress(ValueError, TypeError):
            raise ValueError()
            raise TypeError()
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
