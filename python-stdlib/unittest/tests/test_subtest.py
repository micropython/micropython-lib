import unittest


class Test(unittest.TestCase):
    def test_subtest_skip(self):
        for i in range(4):
            with self.subTest(i=i):
                print("sub test", i)
                if i == 2:
                    self.skipTest("skip 2")


if __name__ == "__main__":
    unittest.main()
