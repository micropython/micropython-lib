import unittest


global_context = None


class TestUnittestIsolated(unittest.TestCase):
    def test_NotChangedByOtherTest(self):
        global global_context
        assert global_context is None
        global_context = True


if __name__ == "__main__":
    unittest.main()
