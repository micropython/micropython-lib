import unittest


class TestUnittestSetup(unittest.TestCase):
    class_setup_var = 0

    @classmethod
    def setUpClass(cls):
        assert cls is TestUnittestSetup
        TestUnittestSetup.class_setup_var += 1

    @classmethod
    def tearDownClass(cls):
        assert cls is TestUnittestSetup
        # Not sure how to actually test this, but we can check (in the test case below)
        # that it hasn't been run already at least.
        TestUnittestSetup.class_setup_var = -1

    def testSetUpTearDownClass_1(self):
        assert TestUnittestSetup.class_setup_var == 1, TestUnittestSetup.class_setup_var

    def testSetUpTearDownClass_2(self):
        # Test this twice, as if setUpClass() gets run like setUp() it would be run twice
        assert TestUnittestSetup.class_setup_var == 1, TestUnittestSetup.class_setup_var


if __name__ == "__main__":
    unittest.main()
