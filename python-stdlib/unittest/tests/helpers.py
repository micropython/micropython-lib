import io
import unittest
import collections


def _run_tests(suite: unittest.TestSuite) -> tuple[unittest.TestResult, str]:
    """Runs a TestSuite, capturing its output.

    Args:
        suite: The TestSuite to run

    Returns:
        A tuple of (test_result, text_output)
    """
    stdout = io.StringIO()
    tmp_stdout = unittest._stdout
    tmp_current_test = unittest.__current_test__
    tmp_test_result = unittest.__test_result__
    try:
        unittest._stdout = stdout
        result = unittest.TestResult()
        suite.run(result)
        return result, stdout.getvalue()
    finally:
        unittest._stdout = tmp_stdout
        unittest.__current_test__ = tmp_current_test
        unittest.__test_result__ = tmp_test_result


def run_tests_in_module(parent_test: unittest.TestCase, module) -> tuple[unittest.TestResult, str]:
    test_name, parent_suite_name = unittest.__current_test__
    parent_suite_name = f"{parent_suite_name[1:-1]}.{test_name}"
    suite = unittest.TestSuite(name=parent_suite_name)
    suite._load_module(module)
    return _run_tests(suite)


def run_tests_in_testcase(
    parent_test: unittest.TestCase, *testcase_classes: type[unittest.TestCase]
) -> tuple[unittest.TestResult, str]:
    """Runs tests in the given TestCase classes."""

    class _FakeModule: ...

    for tc in testcase_classes:
        setattr(_FakeModule, tc.__name__, tc)
    return run_tests_in_module(parent_test, _FakeModule)


class _TestResultSummary(
    collections.namedtuple(
        "TestResultSummary", ("testsRun", "numFailures", "numErrors", "numSkipped")
    )
):
    @classmethod
    def convert(cls, test_result: unittest.TestResult):
        return cls(
            test_result.testsRun,
            len(test_result.failures),
            len(test_result.errors),
            len(test_result.skipped),
        )


class BaseTestCase(unittest.TestCase):
    def full_test_name(self):
        my_name, cls_name = unittest.__current_test__
        return f"{cls_name[1:-1]}.{my_name}"

    def assertTestResult(
        self,
        result: unittest.TestResult,
        *,
        testsRun: int,
        numFailures: int,
        numErrors: int,
        numSkipped: int,
    ):
        expected = _TestResultSummary(testsRun, numFailures, numErrors, numSkipped)
        actual = _TestResultSummary.convert(result)
        if expected == actual:
            return
        err_parts = [f"{actual} != (expected) {expected}"]
        if actual.numFailures != expected.numFailures:
            err_parts.append(f"failures={result.failures!r}")
        if actual.numErrors != expected.numErrors:
            err_parts.append(f"errors={result.errors!r}")
        if actual.numSkipped != expected.numSkipped:
            err_parts.append(f"skipped={result.skipped!r}")
        raise AssertionError("\n".join(err_parts))
