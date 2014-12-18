from unittest import TestCase, run_class
import sys
sys.path.insert(0, '../uasyncio')
import queues


class QueueTestCase(TestCase):

    def _val(self, gen):
        """Returns val from generator."""
        while True:
            try:
                gen.send(None)
            except StopIteration as e:
                return e.value

    def test_get_put(self):
        q = queues.Queue(maxsize=1)
        self._val(q.put(42))
        self.assertEqual(self._val(q.get()), 42)

    def test_get_put_nowait(self):
        q = queues.Queue(maxsize=1)
        q.put_nowait(12)
        try:
            q.put_nowait(42)
            self.assertTrue(False)
        except Exception as e:
            self.assertEqual(type(e), queues.QueueFull)
        self.assertEqual(q.get_nowait(), 12)
        try:
            q.get_nowait()
            self.assertTrue(False)
        except Exception as e:
            self.assertEqual(type(e), queues.QueueEmpty)

    def test_qsize(self):
        q = queues.Queue()
        for n in range(10):
            q.put_nowait(10)
        self.assertEqual(q.qsize(), 10)

    def test_empty(self):
        q = queues.Queue()
        self.assertTrue(q.empty())
        q.put_nowait(10)
        self.assertFalse(q.empty())

    def test_full(self):
        q = queues.Queue(maxsize=1)
        self.assertFalse(q.full())
        q.put_nowait(10)
        self.assertTrue(q.full())


if __name__ == '__main__':
    run_class(QueueTestCase)
