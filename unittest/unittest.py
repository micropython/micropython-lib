class TestCase:

    def fail(self, msg=''):
        assert False, msg

    def assertEqual(self, x, y, msg=''):
        assert x == y, "%r vs (expected) %r" % (x, y)

    def assertTrue(self, x, msg=''):
        assert x, msg

    def assertIn(self, x, y, msg=''):
        assert x in y, msg

    def assertIsInstance(self, x, y, msg=''):
        assert isinstance(x, y), msg

    def assertRaises(self, exc, func, *args):
        try:
            func(*args)
            assert False, "%r not raised" % exc
        except Exception as e:
            if isinstance(e, exc):
                return
            raise


# TODO: Uncompliant
def run_class(c):
    o = c()
    for name in dir(o):
        if name.startswith("test"):
            m = getattr(o, name)
            m()
            print(name, "...ok")


def main(module="__main__"):
    m = __import__(module)
    for tn in dir(m):
        c = getattr(m, tn)
        if isinstance(c, object) and issubclass(c, TestCase):
            run_class(c)
