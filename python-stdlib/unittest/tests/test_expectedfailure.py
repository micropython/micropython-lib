# Tests for @unittest.expectedFailure: a decorated test that fails is an expected
# failure (run stays OK); one that passes is an unexpected success (run fails).
# Each case runs through its own TestResult so it can't fail the outer run.
import unittest


def _run(test_cls):
    result = unittest.TestResult()
    suite = unittest.TestSuite()
    suite.addTest(test_cls)
    suite.run(result)
    return result


class TestExpectedFailure(unittest.TestCase):
    def test_expected_failure_is_not_a_failure(self):
        class Inner(unittest.TestCase):
            @unittest.expectedFailure
            def test_x(self):
                self.assertEqual(1, 0)  # fails as expected

        r = _run(Inner)
        self.assertEqual(r.testsRun, 1)
        self.assertEqual(r.expectedFailuresNum, 1)
        self.assertEqual(r.failuresNum, 0)
        self.assertEqual(r.errorsNum, 0)
        self.assertTrue(r.wasSuccessful())

    def test_unexpected_success_is_tracked_separately(self):
        class Inner(unittest.TestCase):
            @unittest.expectedFailure
            def test_x(self):
                self.assertEqual(1, 1)  # passes -> unexpected success

        r = _run(Inner)
        self.assertEqual(r.testsRun, 1)
        self.assertEqual(r.unexpectedSuccessesNum, 1)
        # Not a failure or error, but still makes the run unsuccessful.
        self.assertEqual(r.failuresNum, 0)
        self.assertEqual(r.errorsNum, 0)
        self.assertFalse(r.wasSuccessful())

    def test_regular_failure_still_counts_as_failure(self):
        class Inner(unittest.TestCase):
            def test_x(self):
                self.assertEqual(1, 0)

        r = _run(Inner)
        self.assertEqual(r.failuresNum, 1)
        self.assertEqual(r.expectedFailuresNum, 0)
        self.assertEqual(r.unexpectedSuccessesNum, 0)
        self.assertFalse(r.wasSuccessful())

    def test_error_is_unaffected(self):
        class Inner(unittest.TestCase):
            def test_x(self):
                raise ValueError("boom")

        r = _run(Inner)
        self.assertEqual(r.errorsNum, 1)
        self.assertEqual(r.expectedFailuresNum, 0)
        self.assertEqual(r.unexpectedSuccessesNum, 0)
        self.assertFalse(r.wasSuccessful())

    def test_results_aggregate_across_modules(self):
        # Results combined with "+" must carry the new counters across.
        class ExpFail(unittest.TestCase):
            @unittest.expectedFailure
            def test_x(self):
                self.assertEqual(1, 0)

        class UnexpSucc(unittest.TestCase):
            @unittest.expectedFailure
            def test_x(self):
                self.assertEqual(1, 1)

        combined = _run(ExpFail) + _run(UnexpSucc)
        self.assertEqual(combined.expectedFailuresNum, 1)
        self.assertEqual(combined.unexpectedSuccessesNum, 1)
        self.assertFalse(combined.wasSuccessful())


if __name__ == "__main__":
    unittest.main()
