from unittest import TestCase, run_class
from contextlib import contextmanager, closing, suppress


class ContextManagerTestCase(TestCase):

    def setUp(self):
        self._history = []

        @contextmanager
        def manager(x):
            self._history.append('start')
            try:
                yield x
            finally:
                self._history.append('finish')

        self._manager = manager

    def test_context_manager(self):
        with self._manager(123) as x:
            self.assertEqual(x, 123)
        self.assertEqual(self._history, ['start', 'finish'])

    def test_context_manager_on_error(self):
        exc = Exception()
        try:
            with self._manager(123) as x:
                raise exc
        except Exception as e:
            self.assertEqual(exc, e)
        self.assertEqual(self._history, ['start', 'finish'])


class ClosingTestCase(TestCase):

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


class SuppressTestCase(TestCase):

    def test_suppress(self):
        with suppress(ValueError, TypeError):
            raise ValueError()
            raise TypeError()
        self.assertTrue(True)


if __name__ == '__main__':
    run_class(ContextManagerTestCase)
    run_class(ClosingTestCase)
    run_class(SuppressTestCase)
