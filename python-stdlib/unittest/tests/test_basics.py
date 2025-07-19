import unittest


class TestWithRunTest(unittest.TestCase):
    run = False

    def runTest(self):
        TestWithRunTest.run = True

    def testRunTest(self):
        self.fail()

    @staticmethod
    def tearDownClass():
        if not TestWithRunTest.run:
            raise ValueError()


def test_func():
    pass


@unittest.expectedFailure
def test_foo():
    raise ValueError()


if __name__ == "__main__":
    unittest.main()
