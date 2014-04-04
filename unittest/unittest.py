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


# Warning: this is not compliant, but at least an example of test
# runner until we have globals()
def main(test_classes):
    for c in test_classes:
        o = c()
        for name in dir(o):
            if name.startswith("test"):
                m = getattr(o, name)
                m()
                print(name, "...ok")
