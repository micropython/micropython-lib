import unittest
import helpers


class Test(helpers.BaseTestCase):
    def test_subtest_skip(self):
        for i in range(4):
            with self.subTest(i=i):
                print("sub test", i)
                if i == 2:
                    self.skipTest("skip 2")

    def test_subtest_catches_failures(self):
        class _Test(unittest.TestCase):
            def test(self):
                with self.subTest(inner=1):
                    self.fail("Failure1")
                with self.subTest(inner=2):
                    self.fail("Failure2")

        result, output = helpers.run_tests_in_testcase(self, _Test)
        self.assertTestResult(result, testsRun=1, numFailures=2, numErrors=0, numSkipped=0)
        self.assertEqual(
            output, "test (test_subtest.Test.test_subtest_catches_failures._Test) ... FAIL\n"
        )

    def test_subtest_catches_exceptions(self):
        class _Test(unittest.TestCase):
            def test(self):
                with self.subTest(inner=1):
                    raise ValueError("Failure1")
                with self.subTest(inner=2):
                    raise ValueError("Failure2")

        result, output = helpers.run_tests_in_testcase(self, _Test)
        self.assertTestResult(result, testsRun=1, numFailures=0, numErrors=2, numSkipped=0)
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(len(result.failures), 0)
        self.assertEqual(len(result.errors), 2)
        # FIXME: unittest framework incorrectly prints the test `FAIL`ed, rather
        # than `ERROR`ed.
        self.assertEqual(
            output, "test (test_subtest.Test.test_subtest_catches_exceptions._Test) ... FAIL\n"
        )


if __name__ == "__main__":
    unittest.main()
