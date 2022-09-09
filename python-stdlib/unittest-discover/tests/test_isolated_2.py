import unittest
import isolated


class TestUnittestIsolated2(unittest.TestCase):
    def test_NotChangedByOtherTest(self):
        self.assertIsNone(isolated.state)
        isolated.state = True
