import unittest
import isolated


class TestUnittestIsolated1(unittest.TestCase):
    def test_NotChangedByOtherTest(self):
        self.assertIsNone(isolated.state)
        isolated.state = True
