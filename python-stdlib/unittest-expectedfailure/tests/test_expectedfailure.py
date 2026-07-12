# Tests for the optional "unittest-expectedfailure" add-on.
#
# The add-on is activated purely by importing it: it monkey-patches the base
# "unittest" package to add CPython-compatible expected-failure / unexpected-
# success tracking.
#
# Each test runs an inner TestCase through its own TestResult and inspects the
# counters, so the outer test run is never made to fail by the cases under test.
import sys
import unittest
import unittest.expectedfailure  # noqa: F401  (imported for its side effect)


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
        # CPython semantics: an unexpected success is NOT a failure or error ...
        self.assertEqual(r.failuresNum, 0)
        self.assertEqual(r.errorsNum, 0)
        # ... but it does make the overall run unsuccessful.
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
        # unittest-discover combines per-module results with "+"; the new
        # counters must be carried across.
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

    def test_reimport_does_not_repatch(self):
        # unittest-discover re-imports test modules with a restored sys.modules,
        # so the add-on may be imported more than once. Re-importing must not
        # patch the machinery a second time.
        before = unittest._handle_test_exception
        sys.modules.pop("unittest.expectedfailure", None)
        __import__("unittest.expectedfailure")

        self.assertIs(unittest._handle_test_exception, before)


if __name__ == "__main__":
    unittest.main()
