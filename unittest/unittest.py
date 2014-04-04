class TestCase:

    def fail(self, msg):
        assert False, msg

    def assertEqual(self, x, y):
        assert x == y, "%r vs %r" % (x, y)

    def assertTrue(self, x):
        assert x

    def assertIn(self, x, y):
        assert x in y

    def assertIsInstance(self, x, y):
        assert isinstance(x, y)

    def assertRaises(self, exc, func, *args):
        try:
            func(*args)
            assert False, "%r not raised" % exc
        except Exception as e:
            if isinstance(e, exc):
                return
            raise


def main(module="__main__"):
    m = __import__(module)
    for tn in dir(m):
        c = getattr(m, tn)
        # workaround for isinstance(c, object) not working
        if type(c) is type(object) and issubclass(c, TestCase):
            o = c()
            for name in dir(o):
                if name.startswith("test"):
                    m = getattr(o, name)
                    m()
                    print(name, "...ok")
