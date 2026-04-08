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
    result = unittest.TestResult(stream=stdout)
    suite.run(result)
    return result, stdout.getvalue()


def run_tests_in_module(parent_test: unittest.TestCase, module) -> tuple[unittest.TestResult, str]:
    """Runs all tests in the given module-like object.

    Args:
        module: An object that can have its attributes listed with the `dir` function.
    """
    _, parent_suite_name = parent_test._test_name
    suite = unittest.TestSuite(name=f"{parent_suite_name[1:-1]}.{parent_test._test_method_name}")
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
        return f"{self.__module__}.{self.__class__.__name__}.{self._test_method_name}"

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
