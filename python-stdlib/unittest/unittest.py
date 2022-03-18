import sys
import uos

try:
    import io
    import traceback
except ImportError:
    import uio as io

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
            return True
        return False


class NullContext:
    def __enter__(self):
        pass

    def __exit__(self, a, b, c):
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
        return NullContext()

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
            run_suite(c, result, self.name)
        return result


class TestRunner:
    def run(self, suite):
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

    def wasSuccessful(self):
        return self.errorsNum == 0 and self.failuresNum == 0

    def printErrors(self):
        print()
        self.printErrorList(self.errors)
        self.printErrorList(self.failures)

    def printErrorList(self, lst):
        sep = "----------------------------------------------------------------------"
        for c, e in lst:
            print("======================================================================")
            print(c)
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
        return self


def capture_exc(e):
    buf = io.StringIO()
    if hasattr(sys, "print_exception"):
        sys.print_exception(e, buf)
    elif traceback is not None:
        traceback.print_exception(None, e, sys.exc_info()[2], file=buf)
    return buf.getvalue()


def run_suite(c, test_result, suite_name=""):
    if isinstance(c, TestSuite):
        c.run(test_result)
        return

    if isinstance(c, type):
        o = c()
    else:
        o = c
    set_up = getattr(o, "setUp", lambda: None)
    tear_down = getattr(o, "tearDown", lambda: None)
    exceptions = []
    try:
        suite_name += "." + c.__qualname__
    except AttributeError:
        pass

    def run_one(m):
        print("%s (%s) ..." % (name, suite_name), end="")
        set_up()
        try:
            test_result.testsRun += 1
            m()
            print(" ok")
        except SkipTest as e:
            print(" skipped:", e.args[0])
            test_result.skippedNum += 1
        except Exception as ex:
            ex_str = capture_exc(ex)
            if isinstance(ex, AssertionError):
                test_result.failuresNum += 1
                test_result.failures.append(((name, c), ex_str))
                print(" FAIL")
            else:
                test_result.errorsNum += 1
                test_result.errors.append(((name, c), ex_str))
                print(" ERROR")
            # Uncomment to investigate failure in detail
            # raise
        finally:
            tear_down()
            try:
                o.doCleanups()
            except AttributeError:
                pass

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

    return exceptions


def _test_cases(mod):
    for tn in dir(mod):
        c = getattr(mod, tn)
        if isinstance(c, object) and isinstance(c, type) and issubclass(c, TestCase):
            yield c
        elif tn.startswith("test_") and callable(c):
            yield c


def run_module(runner, module, path, top):
    sys_path_initial = sys.path[:]
    # Add script dir and top dir to import path
    sys.path.insert(0, str(path))
    if top:
        sys.path.insert(1, top)
    try:
        suite = TestSuite(module)
        m = __import__(module) if isinstance(module, str) else module
        for c in _test_cases(m):
            suite.addTest(c)
        result = runner.run(suite)
        return result

    finally:
        sys.path[:] = sys_path_initial


def discover(runner: TestRunner):
    from unittest_discover import discover

    return discover(runner=runner)


def main(module="__main__"):
    runner = TestRunner()

    if len(sys.argv) <= 1:
        result = discover(runner)
    elif sys.argv[0].split(".")[0] == "unittest" and sys.argv[1] == "discover":
        result = discover(runner)
    else:
        for test_spec in sys.argv[1:]:
            try:
                uos.stat(test_spec)
                # test_spec is a local file, run it directly
                if "/" in test_spec:
                    path, fname = test_spec.rsplit("/", 1)
                else:
                    path, fname = ".", test_spec
                modname = fname.rsplit(".", 1)[0]
                result = run_module(runner, modname, path, None)

            except OSError:
                # Not a file, treat as import name
                result = run_module(runner, test_spec, ".", None)

    # Terminate with non zero return code in case of failures
    sys.exit(result.failuresNum or result.errorsNum)


if __name__ == "__main__":
    main()
