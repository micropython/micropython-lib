import io
import os
import sys

try:
    import traceback
except ImportError:
    traceback = None


class SkipTest(Exception):
    pass


class AssertRaisesContext:
    def __init__(self, exc):
        self.expected = exc

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.exception = exc_value
        if exc_type is None:
            assert False, "%r not raised" % self.expected
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

    def __exit__(self, *exc_info):
        if exc_info[0] is not None:
            # Exception raised
            global __test_result__, __current_test__
            test_details = __current_test__
            if self.msg:
                test_details += (f" [{self.msg}]",)
            if self.params:
                detail = ", ".join(f"{k}={v}" for k, v in self.params.items())
                test_details += (f" ({detail})",)

            _handle_test_exception(test_details, __test_result__, exc_info, False)
        # Suppress the exception as we've captured it above
        return True


class NullContext:
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        pass


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
        assert False, msg

    def assertEqual(self, x, y, msg=""):
        if not msg:
            msg = "%r vs (expected) %r" % (x, y)
        assert x == y, msg

    def assertNotEqual(self, x, y, msg=""):
        if not msg:
            msg = "%r not expected to be equal %r" % (x, y)
        assert x != y, msg

    def assertLessEqual(self, x, y, msg=None):
        if msg is None:
            msg = "%r is expected to be <= %r" % (x, y)
        assert x <= y, msg

    def assertGreaterEqual(self, x, y, msg=None):
        if msg is None:
            msg = "%r is expected to be >= %r" % (x, y)
        assert x >= y, msg

    def assertAlmostEqual(self, x, y, places=None, msg="", delta=None):
        if x == y:
            return
        if delta is not None and places is not None:
            raise TypeError("specify delta or places not both")

        if delta is not None:
            if abs(x - y) <= delta:
                return
            if not msg:
                msg = "%r != %r within %r delta" % (x, y, delta)
        else:
            if places is None:
                places = 7
            if round(abs(y - x), places) == 0:
                return
            if not msg:
                msg = "%r != %r within %r places" % (x, y, places)

        assert False, msg

    def assertNotAlmostEqual(self, x, y, places=None, msg="", delta=None):
        if delta is not None and places is not None:
            raise TypeError("specify delta or places not both")

        if delta is not None:
            if not (x == y) and abs(x - y) > delta:
                return
            if not msg:
                msg = "%r == %r within %r delta" % (x, y, delta)
        else:
            if places is None:
                places = 7
            if not (x == y) and round(abs(y - x), places) != 0:
                return
            if not msg:
                msg = "%r == %r within %r places" % (x, y, places)

        assert False, msg

    def assertIs(self, x, y, msg=""):
        if not msg:
            msg = "%r is not %r" % (x, y)
        assert x is y, msg

    def assertIsNot(self, x, y, msg=""):
        if not msg:
            msg = "%r is %r" % (x, y)
        assert x is not y, msg

    def assertIsNone(self, x, msg=""):
        if not msg:
            msg = "%r is not None" % x
        assert x is None, msg

    def assertIsNotNone(self, x, msg=""):
        if not msg:
            msg = "%r is None" % x
        assert x is not None, msg

    def assertTrue(self, x, msg=""):
        if not msg:
            msg = "Expected %r to be True" % x
        assert x, msg

    def assertFalse(self, x, msg=""):
        if not msg:
            msg = "Expected %r to be False" % x
        assert not x, msg

    def assertIn(self, x, y, msg=""):
        if not msg:
            msg = "Expected %r to be in %r" % (x, y)
        assert x in y, msg

    def assertIsInstance(self, x, y, msg=""):
        assert isinstance(x, y), msg

    def assertRaises(self, exc, func=None, *args, **kwargs):
        if func is None:
            return AssertRaisesContext(exc)

        try:
            func(*args, **kwargs)
        except Exception as e:
            if isinstance(e, exc):
                return
            raise

        assert False, "%r not raised" % exc

    def assertWarns(self, warn):
        return NullContext()


def skip(msg):
    def _decor(fun):
        # We just replace original fun with _inner
        def _inner(self):
            raise SkipTest(msg)

        return _inner

    return _decor


def skipIf(cond, msg):
    if not cond:
        return lambda x: x
    return skip(msg)


def skipUnless(cond, msg):
    if cond:
        return lambda x: x
    return skip(msg)


def expectedFailure(test):
    def test_exp_fail(*args, **kwargs):
        try:
            test(*args, **kwargs)
        except:
            pass
        else:
            assert False, "unexpected success"

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
        if res.failuresNum > 0 or res.errorsNum > 0:
            print("FAILED (failures=%d, errors=%d)" % (res.failuresNum, res.errorsNum))
        else:
            msg = "OK"
            if res.skippedNum > 0:
                msg += " (skipped=%d)" % res.skippedNum
            print(msg)

        return res


TextTestRunner = TestRunner


class TestResult:
    def __init__(self):
        self.errorsNum = 0
        self.failuresNum = 0
        self.skippedNum = 0
        self.testsRun = 0
        self.errors = []
        self.failures = []
        self.skipped = []
        self._newFailures = 0

    def wasSuccessful(self):
        return self.errorsNum == 0 and self.failuresNum == 0

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
            print(f"FAIL: {detail}")
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
        self.testsRun += other.testsRun
        self.errors.extend(other.errors)
        self.failures.extend(other.failures)
        self.skipped.extend(other.skipped)
        return self


def _capture_exc(exc, exc_traceback):
    buf = io.StringIO()
    if hasattr(sys, "print_exception"):
        sys.print_exception(exc, buf)
    elif traceback is not None:
        traceback.print_exception(None, exc, exc_traceback, file=buf)
    return buf.getvalue()


def _handle_test_exception(
    current_test: tuple, test_result: TestResult, exc_info: tuple, verbose=True
):
    exc = exc_info[1]
    traceback = exc_info[2]
    ex_str = _capture_exc(exc, traceback)
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
    set_up_class = getattr(o, "setUpClass", lambda: None)
    tear_down_class = getattr(o, "tearDownClass", lambda: None)
    set_up = getattr(o, "setUp", lambda: None)
    tear_down = getattr(o, "tearDown", lambda: None)
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
        test_container = f"({suite_name})"
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
        except SkipTest as e:
            reason = e.args[0]
            print(" skipped:", reason)
            test_result.skippedNum += 1
            test_result.skipped.append((name, c, reason))
        except Exception as ex:
            _handle_test_exception(
                current_test=(name, c), test_result=test_result, exc_info=(type(ex), ex, None)
            )
            # Uncomment to investigate failure in detail
            # raise
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
