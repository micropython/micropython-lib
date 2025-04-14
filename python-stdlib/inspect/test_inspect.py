import inspect
import unittest


def fun():
    return 1


def gen():
    yield 1


class Class:
    def meth(self):
        pass


entities = (
    fun,
    gen,
    gen(),
    Class,
    Class.meth,
    Class().meth,
    inspect,
)


class TestInspect(unittest.TestCase):
    def _test_is_helper(self, f, *entities_true):
        for entity in entities:
            result = f(entity)
            if entity in entities_true:
                self.assertTrue(result)
            else:
                self.assertFalse(result)

    def test_isfunction(self):
        self._test_is_helper(inspect.isfunction, entities[0], entities[4])

    def test_isgeneratorfunction(self):
        self._test_is_helper(inspect.isgeneratorfunction, entities[1])

    def test_isgenerator(self):
        self._test_is_helper(inspect.isgenerator, entities[2])

    def test_iscoroutinefunction(self):
        self._test_is_helper(inspect.iscoroutinefunction, entities[1])

    def test_iscoroutine(self):
        self._test_is_helper(inspect.iscoroutine, entities[2])

    def test_ismethod(self):
        self._test_is_helper(inspect.ismethod, entities[5])

    def test_isclass(self):
        self._test_is_helper(inspect.isclass, entities[3])

    def test_ismodule(self):
        self._test_is_helper(inspect.ismodule, entities[6])
