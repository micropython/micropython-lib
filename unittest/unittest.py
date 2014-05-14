class SkipTest(Exception):
    pass


class TestCase:

    def fail(self, msg=''):
        assert False, msg

    def assertEqual(self, x, y, msg=''):
        if not msg:
            msg = "%r vs (expected) %r" % (x, y)
        assert x == y, msg

    def assertIs(self, x, y, msg=''):
        if not msg:
            msg = "%r is not %r" % (x, y)
        assert x is y, msg

    def assertTrue(self, x, msg=''):
        assert x, msg

    def assertIn(self, x, y, msg=''):
        assert x in y, msg

    def assertIsInstance(self, x, y, msg=''):
        assert isinstance(x, y), msg

    def assertRaises(self, exc, func, *args, **kwargs):
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


# TODO: Uncompliant
def run_class(c):
    o = c()
    set_up = getattr(o, "setUp", lambda: None)
    tear_down = getattr(o, "tearDown", lambda: None)
    for name in dir(o):
        if name.startswith("test"):
            m = getattr(o, name)
            try:
                set_up()
                m()
                tear_down()
                print(name, "...ok")
            except SkipTest as e:
                print(name, "...skipped:", e.args[0])


def main(module="__main__"):
    m = __import__(module)
    for tn in dir(m):
        c = getattr(m, tn)
        if isinstance(c, object) and issubclass(c, TestCase):
            run_class(c)
