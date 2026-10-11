import io
import sys


class SkipTest(Exception):
    pass


class AssertRaisesContext:
    def __init__(self, exc):
        self.expected = exc

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if self.expected is None:
            # Used by assertWarns, do nothing.
            return
        self.exception = exc_value
        if exc_type is None:
            raise AssertionError("%r not raised" % self.expected)
        if issubclass(exc_type, self.expected):
            # store exception for later retrieval
            self.exception = exc_value
            return True
        return False


# These are used to provide required context to things like subTest
__current_test__ = None
__test_result__ = None


class SubtestContext:
    def __init__(self, msg=None, params=None):
        self.msg = msg
        self.params = params

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None:
            # Exception raised
            global __test_result__, __current_test__
            test_details = __current_test__
            if self.msg:
                test_details += (" [%s]" % self.msg,)
            if self.params:
                detail = ", ".join("%s=%s" % k_v for k_v in self.params.items())
                test_details += (" (%s)" % detail,)

            _handle_test_exception(test_details, __test_result__, exc_value, False)
        # Suppress the exception as we've captured it above
        return True


class TestCase:
    def __init__(self):
        pass

    def addCleanup(self, func, *args, **kwargs):
        if not hasattr(self, "_cleanups"):
            self._cleanups = []
        self._cleanups.append((func, args, kwargs))

    def doCleanups(self):
        if hasattr(self, "_cleanups"):
            while self._cleanups:
                func, args, kwargs = self._cleanups.pop()
                func(*args, **kwargs)

    def subTest(self, msg=None, **params):
        return SubtestContext(msg=msg, params=params)

    def skipTest(self, reason):
        raise SkipTest(reason)

    def fail(self, msg=""):
        raise AssertionError(msg)

    def assertEqual(self, x, y, msg=None):
        if not x == y:
            raise AssertionError(msg or "%r vs (expected) %r" % (x, y))

    def assertNotEqual(self, x, y, msg=None):
        if not x != y:
            raise AssertionError(msg or "%r not expected to be equal %r" % (x, y))

    def assertLessEqual(self, x, y, msg=None):
        if not x <= y:
            raise AssertionError(msg or "%r is expected to be <= %r" % (x, y))

    def assertGreaterEqual(self, x, y, msg=None):
        if not x >= y:
            raise AssertionError(msg or "%r is expected to be >= %r" % (x, y))

    def assertAlmostEqual(self, x, y, places=None, msg=None, delta=None):
        if x == y:
            return
        if delta is not None and places is not None:
            raise TypeError("specify delta or places not both")

        if delta is not None:
            if abs(x - y) <= delta:
                return
            raise AssertionError(msg or "%r != %r within %r delta" % (x, y, delta))
        else:
            if places is None:
                places = 7
            if round(abs(y - x), places) == 0:
                return
            raise AssertionError(msg or "%r != %r within %r places" % (x, y, places))

    def assertNotAlmostEqual(self, x, y, places=None, msg=None, delta=None):
        if delta is not None and places is not None:
            raise TypeError("specify delta or places not both")

        if delta is not None:
            if not (x == y) and abs(x - y) > delta:
                return
            raise AssertionError(msg or "%r == %r within %r delta" % (x, y, delta))
        else:
            if places is None:
                places = 7
            if not (x == y) and round(abs(y - x), places) != 0:
                return
            raise AssertionError(msg or "%r == %r within %r places" % (x, y, places))

    def assertIs(self, x, y, msg=None):
        if not x is y:
            raise AssertionError(msg or "%r is not %r" % (x, y))

    def assertIsNot(self, x, y, msg=None):
        if not x is not y:
            raise AssertionError(msg or "%r is %r" % (x, y))

    def assertIsNone(self, x, msg=None):
        if not x is None:
            raise AssertionError(msg or "%r is not None" % x)

    def assertIsNotNone(self, x, msg=None):
        if not x is not None:
            raise AssertionError(msg or "%r is None" % x)

    def assertTrue(self, x, msg=None):
        if not x:
            raise AssertionError(msg or "Expected %r to be True" % x)

    def assertFalse(self, x, msg=None):
        if x:
            raise AssertionError(msg or "Expected %r to be False" % x)

    def assertIn(self, x, y, msg=None):
        if not x in y:
            raise AssertionError(msg or "Expected %r to be in %r" % (x, y))

    def assertIsInstance(self, x, y, msg=""):
        if not isinstance(x, y):
            raise AssertionError(msg)

    def assertRaises(self, exc, func=None, *args, **kwargs):
        if func is None:
            return AssertRaisesContext(exc)

        try:
            func(*args, **kwargs)
        except Exception as e:
            if isinstance(e, exc):
                return
            raise e

        raise AssertionError("%r not raised" % exc)

    def assertWarns(self, warn):
        return AssertRaisesContext(None)


def skip(msg):
    def _decor(fun):
        # We just replace original fun with _inner
        def _inner(self):
            raise SkipTest(msg)

        return _inner

    return _decor


def skipIf(cond, msg):
    return skip(msg) if cond else lambda x: x


def skipUnless(cond, msg):
    return skipIf(not cond, msg)


# Sentinels for the two @expectedFailure outcomes: a test that raised
# (expected failure) vs one that passed (unexpected success).
class _ExpFail(Exception):
    pass


class _UnexpSucc(Exception):
    pass


def expectedFailure(test):
    def test_exp_fail(*args, **kwargs):
        try:
            test(*args, **kwargs)
        except Exception:
            raise _ExpFail
        raise _UnexpSucc

    return test_exp_fail


class TestSuite:
    def __init__(self, name=""):
        self._tests = []
        self.name = name

    def addTest(self, cls):
        self._tests.append(cls)

    def run(self, result):
        for c in self._tests:
            _run_suite(c, result, self.name)
        return result

    def _load_module(self, mod):
        for tn in dir(mod):
            c = getattr(mod, tn)
            if isinstance(c, object) and isinstance(c, type) and issubclass(c, TestCase):
                self.addTest(c)
            elif tn.startswith("test") and callable(c):
                self.addTest(c)


class TestRunner:
    def run(self, suite: TestSuite):
        res = TestResult()
        suite.run(res)

        res.printErrors()
        print("----------------------------------------------------------------------")
        print("Ran %d tests\n" % res.testsRun)
        info = []
        for num, label in (
            (res.failuresNum, "failures"),
            (res.errorsNum, "errors"),
            (res.skippedNum, "skipped"),
            (res.expectedFailuresNum, "expected failures"),
            (res.unexpectedSuccessesNum, "unexpected successes"),
        ):
            if num:
                info.append("%s=%d" % (label, num))
        status = "OK" if res.wasSuccessful() else "FAILED"
        print("%s (%s)" % (status, ", ".join(info)) if info else status)

        return res


TextTestRunner = TestRunner


class TestResult:
    def __init__(self):
        self.errorsNum = 0
        self.failuresNum = 0
        self.skippedNum = 0
        self.expectedFailuresNum = 0
        self.unexpectedSuccessesNum = 0
        self.testsRun = 0
        self.errors = []
        self.failures = []
        self.skipped = []
        self._newFailures = 0

    def wasSuccessful(self):
        # An unexpected success isn't a failure/error but still fails the run.
        return self.errorsNum == 0 and self.failuresNum == 0 and self.unexpectedSuccessesNum == 0

    def printErrors(self):
        if self.errors or self.failures:
            print()
            self.printErrorList(self.errors)
            self.printErrorList(self.failures)

    def printErrorList(self, lst):
        sep = "----------------------------------------------------------------------"
        for c, e in lst:
            detail = " ".join((str(i) for i in c))
            print("======================================================================")
            print("FAIL:", detail)
            print(sep)
            print(e)

    def __repr__(self):
        # Format is compatible with CPython.
        return "<unittest.result.TestResult run=%d errors=%d failures=%d>" % (
            self.testsRun,
            self.errorsNum,
            self.failuresNum,
        )

    def __add__(self, other):
        self.errorsNum += other.errorsNum
        self.failuresNum += other.failuresNum
        self.skippedNum += other.skippedNum
        self.expectedFailuresNum += other.expectedFailuresNum
        self.unexpectedSuccessesNum += other.unexpectedSuccessesNum
        self.testsRun += other.testsRun
        self.errors.extend(other.errors)
        self.failures.extend(other.failures)
        self.skipped.extend(other.skipped)
        return self


def _handle_test_exception(
    current_test: tuple, test_result: TestResult, exc: Exception, verbose=True
):
    if isinstance(exc, SkipTest):
        reason = exc.args[0]
        test_result.skippedNum += 1
        test_result.skipped.append((current_test, reason))
        print(" skipped:", reason)
        return
    if isinstance(exc, _ExpFail):
        test_result.expectedFailuresNum += 1
        if verbose:
            print(" expected failure")
        return
    if isinstance(exc, _UnexpSucc):
        test_result.unexpectedSuccessesNum += 1
        if verbose:
            print(" unexpected success")
        return
    buf = io.StringIO()
    sys.print_exception(exc, buf)
    ex_str = buf.getvalue()
    if isinstance(exc, AssertionError):
        test_result.failuresNum += 1
        test_result.failures.append((current_test, ex_str))
        if verbose:
            print(" FAIL")
    else:
        test_result.errorsNum += 1
        test_result.errors.append((current_test, ex_str))
        if verbose:
            print(" ERROR")
    test_result._newFailures += 1


def _run_suite(c, test_result: TestResult, suite_name=""):
    if isinstance(c, TestSuite):
        c.run(test_result)
        return

    if isinstance(c, type):
        o = c()
    else:
        o = c
    nop = lambda: None
    set_up_class = getattr(o, "setUpClass", nop)
    tear_down_class = getattr(o, "tearDownClass", nop)
    set_up = getattr(o, "setUp", nop)
    tear_down = getattr(o, "tearDown", nop)
    exceptions = []
    try:
        suite_name += "." + c.__qualname__
    except AttributeError:
        pass

    def run_one(test_function):
        global __test_result__, __current_test__
        print("%s (%s) ..." % (name, suite_name), end="")
        set_up()
        __test_result__ = test_result
        test_container = "(%s)" % suite_name
        __current_test__ = (name, test_container)
        try:
            test_result._newFailures = 0
            test_result.testsRun += 1
            test_function()
            # No exception occurred, test passed
            if test_result._newFailures:
                print(" FAIL")
            else:
                print(" ok")
        except Exception as ex:
            _handle_test_exception((name, c), test_result, ex)
            # Uncomment to investigate failure in detail
            # raise ex
        finally:
            __test_result__ = None
            __current_test__ = None
            tear_down()
            try:
                o.doCleanups()
            except AttributeError:
                pass

    set_up_class()
    try:
        if hasattr(o, "runTest"):
            name = str(o)
            run_one(o.runTest)
            return

        for name in dir(o):
            if name.startswith("test"):
                m = getattr(o, name)
                if not callable(m):
                    continue
                run_one(m)

        if callable(o):
            name = o.__name__
            run_one(o)
    finally:
        tear_down_class()

    return exceptions


# This supports either:
#
# >>> import mytest
# >>> unitttest.main(mytest)
#
# >>> unittest.main("mytest")
#
# Or, a script that ends with:
# if __name__ == "__main__":
#     unittest.main()
# e.g. run via `mpremote run mytest.py`
def main(module="__main__", testRunner=None):
    if testRunner is None:
        testRunner = TestRunner()
    elif isinstance(testRunner, type):
        testRunner = testRunner()

    if isinstance(module, str):
        module = __import__(module)
    suite = TestSuite(module.__name__)
    suite._load_module(module)
    return testRunner.run(suite)
