class SkipTest(Exception):
    pass


class AssertRaisesContext:

    def __init__(self, exc):
        self.expected = exc

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is None:
            assert False, "%r not raised" % self.expected
        if issubclass(exc_type, self.expected):
            return True
        return False


class TestCase:

    def fail(self, msg=''):
        assert False, msg

    def assertEqual(self, x, y, msg=''):
        if not msg:
            msg = "%r vs (expected) %r" % (x, y)
        assert x == y, msg

    def assertNotEqual(self, x, y, msg=''):
        if not msg:
            msg = "%r not expected to be equal %r" % (x, y)
        assert x != y, msg

    def assertAlmostEqual(self, x, y, places=None, msg='', delta=None):
        if x == y:
            return
        if delta is not None and places is not None:
            raise TypeError("specify delta or places not both")

        if delta is not None:
            if abs(x - y) <= delta:
                return
            if not msg:
                msg = '%r != %r within %r delta' % (x, y, delta)
        else:
            if places is None:
                places = 7
            if round(abs(y-x), places) == 0:
                return
            if not msg:
                msg = '%r != %r within %r places' % (x, y, places)

        assert False, msg

    def assertNotAlmostEqual(self, x, y, places=None, msg='', delta=None):
        if delta is not None and places is not None:
            raise TypeError("specify delta or places not both")

        if delta is not None:
            if not (x == y) and abs(x - y) > delta:
                return
            if not msg:
                msg = '%r == %r within %r delta' % (x, y, delta)
        else:
            if places is None:
                places = 7
            if not (x == y) and round(abs(y-x), places) != 0:
                return
            if not msg:
                msg = '%r == %r within %r places' % (x, y, places)

        assert False, msg

    def assertIs(self, x, y, msg=''):
        if not msg:
            msg = "%r is not %r" % (x, y)
        assert x is y, msg

    def assertIsNot(self, x, y, msg=''):
        if not msg:
            msg = "%r is %r" % (x, y)
        assert x is not y, msg

    def assertIsNone(self, x, msg=''):
        if not msg:
            msg = "%r is not None" % x
        assert x is None, msg

    def assertIsNotNone(self, x, msg=''):
        if not msg:
            msg = "%r is None" % x
        assert x is not None, msg

    def assertTrue(self, x, msg=''):
        if not msg:
            msg = "Expected %r to be True" % x
        assert x, msg

    def assertFalse(self, x, msg=''):
        if not msg:
            msg = "Expected %r to be False" % x
        assert not x, msg

    def assertIn(self, x, y, msg=''):
        if not msg:
            msg = "Expected %r to be in %r" % (x, y)
        assert x in y, msg

    def assertIsInstance(self, x, y, msg=''):
        assert isinstance(x, y), msg

    def assertRaises(self, exc, func=None, *args, **kwargs):
        if func is None:
            return AssertRaisesContext(exc)

        try:
            func(*args, **kwargs)
            assert False, "%r not raised" % exc
        except Exception as e:
            if isinstance(e, exc):
                return
            raise



def skip(msg):
    def _decor(fun):
        # We just replace original fun with _inner
        def _inner(self):
            raise SkipTest(msg)
        return _inner
    return _decor


def skipUnless(cond, msg):
    if cond:
        return lambda x: x
    return skip(msg)


class TestSuite:
    def __init__(self):
        self.tests = []
    def addTest(self, cls):
        self.tests.append(cls)

class TestRunner:
    def run(self, suite):
        res = TestResult()
        for c in suite.tests:
            run_class(c, res)
        return res

class TestResult:
    def __init__(self):
        self.errorsNum = 0
        self.failuresNum = 0
        self.skippedNum = 0
        self.testsRun = 0

    def wasSuccessful(self):
        return self.errorsNum == 0 and self.failuresNum == 0

# TODO: Uncompliant
def run_class(c, test_result):
    o = c()
    set_up = getattr(o, "setUp", lambda: None)
    tear_down = getattr(o, "tearDown", lambda: None)
    for name in dir(o):
        if name.startswith("test"):
            print(name, end=' ...')
            m = getattr(o, name)
            try:
                set_up()
                test_result.testsRun += 1
                m()
                tear_down()
                print(" ok")
            except SkipTest as e:
                print(" skipped:", e.args[0])
                test_result.skippedNum += 1


def main(module="__main__"):
    def test_cases(m):
        for tn in dir(m):
            c = getattr(m, tn)
            if isinstance(c, object) and isinstance(c, type) and issubclass(c, TestCase):
                yield c

    m = __import__(module)
    suite = TestSuite()
    for c in test_cases(m):
        suite.addTest(c)
    runner = TestRunner()
    result = runner.run(suite)
    msg = "Ran %d tests" % result.testsRun
    if result.skippedNum > 0:
        msg += " (%d skipped)" % result.skippedNum
    print(msg)
