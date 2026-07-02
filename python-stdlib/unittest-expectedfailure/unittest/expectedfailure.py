# Optional add-on for the "unittest" package that adds CPython-compatible
# tracking of expected failures and unexpected successes.
#
# Activate it by importing this module once, before running your tests:
#
#     import unittest
#     import unittest.expectedfailure  # imported for its side effect
#
# then decorate tests as usual with @unittest.expectedFailure.
#
# Behaviour (matching CPython):
#   - a decorated test that fails    -> counted in expectedFailuresNum,
#                                        the run stays successful
#   - a decorated test that passes   -> counted in unexpectedSuccessesNum,
#                                        NOT counted as a failure/error, but
#                                        wasSuccessful() becomes False
import unittest

# unittest-discover re-imports test modules with a restored sys.modules, so this
# module can execute more than once per session.
if not getattr(unittest, "_expectedfailure_patched", False):

    class _ExpectedFailure(Exception):
        pass

    class _UnexpectedSuccess(Exception):
        pass

    _orig_handle = unittest._handle_test_exception
    _orig_result_add = unittest.TestResult.__add__

    # Decorator: run the wrapped test and raise a sentinel exception so the
    # result machinery can tell an expected failure (the test raised) from an
    # unexpected success (the test passed).
    def expectedFailure(test):
        def wrapper(*args, **kwargs):
            try:
                test(*args, **kwargs)
            except Exception:
                raise _ExpectedFailure
            raise _UnexpectedSuccess

        return wrapper

    # Replaces unittest._handle_test_exception: record the two sentinel outcomes
    # in their own result categories, and delegate any other exception to the
    # original handler (failures, errors, skips).
    def _handle_test_exception(current_test, test_result, exc, verbose=True):
        if isinstance(exc, _ExpectedFailure):
            test_result.expectedFailuresNum += 1
            if verbose:
                print(" expected failure")
            return
        if isinstance(exc, _UnexpectedSuccess):
            test_result.unexpectedSuccessesNum += 1
            if verbose:
                print(" unexpected success")
            return
        return _orig_handle(current_test, test_result, exc, verbose)

    # Extend TestResult.__add__ so the new counters are aggregated when
    # per-module results are combined (unittest-discover sums results with "+").
    def _result_add(self, other):
        _orig_result_add(self, other)
        self.expectedFailuresNum += other.expectedFailuresNum
        self.unexpectedSuccessesNum += other.unexpectedSuccessesNum
        return self

    def _was_successful(self):
        # An unexpected success is not a failure or error, but (like CPython) it
        # does make the overall run unsuccessful.
        return self.errorsNum == 0 and self.failuresNum == 0 and self.unexpectedSuccessesNum == 0

    # Replaces TestRunner.run: like the base runner, but reports expected
    # failures / unexpected successes in the CPython-style summary and decides
    # OK/FAILED via wasSuccessful().
    def _runner_run(self, suite):
        result = unittest.TestResult()
        suite.run(result)

        result.printErrors()
        print("----------------------------------------------------------------------")
        print("Ran %d tests\n" % result.testsRun)
        infos = []
        if result.wasSuccessful():
            status = "OK"
        else:
            status = "FAILED"
            if result.failuresNum:
                infos.append("failures=%d" % result.failuresNum)
            if result.errorsNum:
                infos.append("errors=%d" % result.errorsNum)
        if result.skippedNum:
            infos.append("skipped=%d" % result.skippedNum)
        if result.expectedFailuresNum:
            infos.append("expected failures=%d" % result.expectedFailuresNum)
        if result.unexpectedSuccessesNum:
            infos.append("unexpected successes=%d" % result.unexpectedSuccessesNum)
        if infos:
            print("%s (%s)" % (status, ", ".join(infos)))
        else:
            print(status)
        return result

    unittest.expectedFailure = expectedFailure
    unittest._handle_test_exception = _handle_test_exception
    # Class-level defaults keep the counters free per-result: no instance
    # attribute is allocated until a test is actually recorded (an instance
    # attribute is created on first increment). They also let results created
    # before this add-on loaded (e.g. discover's accumulator) be read and
    # combined with "+".
    unittest.TestResult.expectedFailuresNum = 0
    unittest.TestResult.unexpectedSuccessesNum = 0
    unittest.TestResult.__add__ = _result_add
    unittest.TestResult.wasSuccessful = _was_successful
    unittest.TestRunner.run = _runner_run
    unittest._expectedfailure_patched = True
