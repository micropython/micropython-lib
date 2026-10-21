# test_enum.py
# version="1.5.1"

import unittest
from enum import Enum, IntEnum, StrEnum


class TestEnum(unittest.TestCase):
    def setUp(self):
        class Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3

        class Status(Enum):
            IDLE = 0
            RUNNING = 1
            ERROR = 2

        self.ColorClass = Color
        self.color = Color()
        self.StatusClass = Status
        self.status = Status()

    def test_class_attributes(self):
        """Test basic access to Enum members, names, and values."""
        self.assertEqual(self.color.RED.value, 1)
        self.assertEqual(self.color.RED.name, 'RED')
        self.assertEqual(str(type(self.color.RED)), "<class 'Color.RED'>")
        self.assertEqual(type(self.color.RED).__name__, 'Color.RED')

        self.assertIsInstance(self.color.RED, type(self.color.RED))
        self.assertEqual(self.status.IDLE.value, 0)

    def test_getitem_access(self):
        """Test item access via square brackets."""
        self.assertEqual(self.ColorClass()["RED"], self.color.RED)
        self.assertEqual(self.ColorClass()["BLUE"], self.color.BLUE)

        with self.assertRaises(KeyError):
            _ = self.ColorClass()["YELLOW"]

    def test_comparison(self):
        """Test equality between Enum members and raw values."""
        self.assertTrue(self.color.RED == 1)
        self.assertFalse(self.color.RED == 2)
        self.assertEqual(self.color.RED, self.color.RED)
        self.assertFalse(self.color.RED == "1")

    def test_reverse_lookup(self):
        """Test reverse lookup by value, name, and member instance."""
        # Lookup by value
        self.assertEqual(self.color(1), self.color.RED)
        self.assertEqual(self.StatusClass(1), self.StatusClass.RUNNING)

        # Lookup by name
        self.assertEqual(self.color('RED'), self.color.RED)

        # Lookup by instance
        self.assertEqual(self.color(self.ColorClass.RED), self.ColorClass.RED)

        # Invalid lookup
        with self.assertRaises(ValueError):
            self.color(999)
        with self.assertRaises(ValueError):
            self.StatusClass(999)

    def test_iteration(self):
        """Test iteration over Enum instance."""
        members = list(self.color)
        names = [m.name for m in members]
        self.assertEqual(len(members), 3)
        self.assertEqual(names, ['RED', 'GREEN', 'BLUE'])

    def test_immutability(self):
        """Verify Enum member and Enum instance are immutable after init."""
        with self.assertRaises(AttributeError):
            self.color.RED.value = 10

        with self.assertRaises(AttributeError):
            self.color.NEW_MEMBER = 4

    def test_deletion_prevention(self):
        """Verify that members cannot be deleted from instance or class."""
        with self.assertRaises(AttributeError):
            del self.color.RED

#         with self.assertRaises(AttributeError):
#             delattr(self.ColorClass, "RED")

    def test_len_and_items(self):
        """Test __len__ and __members__ dictionary."""
        self.assertEqual(len(self.color), 3)
        self.assertEqual(
            self.color.__members__,
            {self.color.RED: 1, self.color.GREEN: 2, self.color.BLUE: 3}
        )

    def test_call_method(self):
        """Test calling EnumValue as a function to get its value."""
        self.assertEqual(self.color.RED(), 1)
        self.assertEqual(self.color.GREEN(), 2)

    def test_functional_api(self):
        """Test dynamic Enum creation using the Functional API."""
        State = Enum(value='State', names={'ON': 1, 'OFF': 0})
        self.assertTrue(hasattr(State, 'ON'))
        self.assertEqual(State.ON.value, 1)
        self.assertEqual(State.OFF.name, 'OFF')

        StrParsed = Enum('StrParsed', 'A B C', start=10)
        self.assertEqual(StrParsed.A.value, 10)
        self.assertEqual(StrParsed.C.value, 12)

        ListParsed = Enum('ListParsed', ['X', 'Y'])
        self.assertEqual(ListParsed.X.value, 1)
        self.assertEqual(ListParsed.Y.value, 2)

    def test_int_enum_and_str_enum(self):
        """Verify IntEnum and StrEnum type restrictions."""
        class Number(IntEnum):
            ONE = 1
            TWO = 2

        Number()
        self.assertEqual(Number.ONE.value, 1)

        with self.assertRaises(TypeError):
            class InvalidInt(IntEnum):
                ONE = 1
                BAD = "not_an_int"
            InvalidInt()

        class Greeting(StrEnum):
            HI = "hello"

        Greeting()
        self.assertEqual(Greeting.HI.value, "hello")

        with self.assertRaises(TypeError):
            class InvalidStr(StrEnum):
                HI = "hello"
                BAD = 123
            InvalidStr()

    def test_str_and_repr(self):
        """Test string representations for Enum members."""
        self.assertEqual(str(self.color.RED), "Color.RED")
        self.assertEqual(repr(self.color.RED), "<Color.RED: 1>")

    def test_serialization_repr_eval(self):
        """Verify eval(cls.dump()) restores the Enum correctly."""
        c_dump = self.color.dump()
        c_restored = eval(c_dump)
        self.assertEqual(self.color.__members__, c_restored.__members__)
        self.assertEqual(type(self.color).__name__, c_restored.__name__)

        s_dynamic = Enum(value='StatusFunc', names={'START': 1, 'STOP': 0})
        s_dump = s_dynamic.dump()
        s_restored = eval(s_dump)
        self.assertEqual(s_dynamic.__members__, s_restored.__members__)


class TestTypedStrEnum(unittest.TestCase):
    def test_identity_lookup_and_methods(self):
        class Mode(StrEnum):
            FAST = "fast"
            SLOW = "slow"
            _private_helper = 123

            def describe(self):
                return self.name + ":" + self.value

        self.assertIs(type(Mode.FAST), Mode)
        for base in (Mode, StrEnum, Enum, str):
            self.assertTrue(isinstance(Mode.FAST, base))
        self.assertFalse(isinstance("fast", Mode))
        for value in ("fast", "FAST", Mode.FAST):
            self.assertIs(Mode(value), Mode.FAST)
        self.assertIs(Mode(), Mode)
        self.assertEqual(Mode.FAST.name, "FAST")
        self.assertEqual(Mode.FAST.value, "fast")
        self.assertEqual(Mode.FAST.describe(), "FAST:fast")
        self.assertEqual(Mode.FAST(), "fast")
        with self.assertRaises(ValueError):
            Mode("missing")

    def test_string_operations_and_iteration(self):
        class Mode(StrEnum):
            FAST = "fast"
            SLOW = "slow"

        self.assertTrue(Mode.FAST == "fast")
        self.assertTrue("fast" == Mode.FAST)
        self.assertEqual(Mode.FAST.upper(), "FAST")
        self.assertEqual(Mode.FAST + "!", "fast!")
        self.assertEqual(hash(Mode.FAST), hash("fast"))
        self.assertEqual(Mode.FAST[0], "f")
        self.assertEqual(Mode.FAST[:2], "fa")
        self.assertEqual(Mode.FAST[-1], "t")
        with self.assertRaises(TypeError):
            Mode.FAST[None]
        members = list(Mode)
        self.assertEqual(len(members), 2)
        self.assertTrue(any(item is Mode.FAST for item in members))
        self.assertTrue(any(item is Mode.SLOW for item in members))
        self.assertEqual(list(Mode.FAST), list("fast"))
        self.assertEqual(str(Mode.FAST), "fast")
        self.assertEqual(repr(Mode.FAST), repr("fast"))

    def test_direct_functional_api_and_dump(self):
        for names in ("FAST SLOW", {"FAST": "fast", "SLOW": "slow"},
                      (("FAST", "fast"), ("SLOW", "slow"))):
            Mode = StrEnum("Mode", names)
            self.assertIs(type(Mode.FAST), Mode)
            self.assertEqual(Mode.FAST.value, "fast")
            self.assertIs(Mode("FAST"), Mode.FAST)
            self.assertEqual(len(list(Mode)), 2)
            restored = eval(Mode.dump())
            self.assertIs(type(restored.FAST), restored)
            self.assertEqual(restored.FAST.value, "fast")
        self.assertEqual(StrEnum("Words", ["UP", "DOWN"]).UP.value, "UP")
        self.assertEqual(StrEnum("Words", (x for x in ["UP", "DOWN"])).UP.value, "UP")

    def test_reject_invalid_declarations(self):
        with self.assertRaises(TypeError):
            class Invalid(StrEnum):
                BAD = 1
        with self.assertRaises(ValueError):
            class Duplicate(StrEnum):
                A = "same"
                B = "same"
        with self.assertRaises(TypeError):
            class Constructor(StrEnum):
                A = "a"
                def __init__(self, value):
                    pass
        with self.assertRaises(TypeError):
            class Allocator(StrEnum):
                A = "a"
                def __new__(cls, value):
                    return value
        class Base(StrEnum):
            A = "a"
        with self.assertRaises(TypeError):
            class Child(Base):
                B = "b"
        class Mixin:
            pass
        with self.assertRaises(TypeError):
            class Mixed(Mixin, StrEnum):
                A = "a"
        with self.assertRaises(TypeError):
            Base("Child", {"B": "b"})
        with self.assertRaises(TypeError):
            class Reserved(StrEnum):
                __members__ = {}
        Empty = StrEnum("Empty", {})
        self.assertEqual(list(Empty), [])

    def test_callable_string_values_and_normalization(self):
        class Text(str):
            def __call__(self):
                return "callable"
            def __str__(self):
                return "misleading"
        class Mode(StrEnum):
            FAST = Text("fast")
        self.assertIs(type(Mode.FAST), Mode)
        self.assertEqual(Mode.FAST, "fast")
        self.assertIs(type(Mode.FAST.value), str)
        class Copy(StrEnum):
            FAST = Mode.FAST
        self.assertIs(type(Copy.FAST), Copy)
        self.assertEqual(Copy.FAST.value, "fast")
        class SlicedText(Text):
            def __getitem__(self, key):
                return "wrong"
        with self.assertRaises(TypeError):
            class UnsupportedValue(StrEnum):
                FAST = SlicedText("fast")
        with self.assertRaises(ValueError):
            class Duplicate(StrEnum):
                A = Text("same")
                B = "same"

    def test_member_metadata_and_stock_limits(self):
        class Mode(StrEnum):
            FAST = "fast"
        with self.assertRaises(AttributeError):
            Mode.FAST.name = "changed"
        with self.assertRaises(AttributeError):
            del Mode.FAST.value
        with self.assertRaises(TypeError):
            len(Mode)
        with self.assertRaises(TypeError):
            Mode["FAST"]
        import json
        self.assertEqual(json.loads(json.dumps(Mode.FAST)), "fast")
        self.assertEqual(json.loads(json.dumps([Mode.FAST])), ["fast"])

    def test_full_then_mini_and_fresh_full(self):
        import enum_mini
        class Mini(enum_mini.Enum):
            A = 1
        self.assertEqual(Mini.A.name, "A")
        class Mode(StrEnum):
            FAST = "fast"
        self.assertIs(type(Mode.FAST), Mode)
        state = __ENUM_STATE__
        wrapper = state["wrapper"]
        import enum as module
        count = len(state["families"])
        self.assertIs(__import__("enum"), module)
        self.assertEqual(len(state["families"]), count)
        import sys
        del sys.modules["enum"]
        try:
            fresh = __import__("enum")
        finally:
            sys.modules["enum"] = module
        namespace = {"StrEnum": fresh.StrEnum, "Enum": fresh.Enum, "IntEnum": fresh.IntEnum}
        self.assertIs(state["wrapper"], wrapper)
        class OldMode(StrEnum):
            A = "a"
        class FreshMode(namespace["StrEnum"]):
            A = "a"
        self.assertIs(type(OldMode.A), OldMode)
        self.assertIs(type(FreshMode.A), FreshMode)
        class OldGeneric(Enum):
            A = 1
        class FreshGeneric(namespace["Enum"]):
            A = 1
        class FreshNumber(namespace["IntEnum"]):
            A = 1
        self.assertEqual(OldGeneric.A.name, "A")
        self.assertEqual(FreshGeneric.A.name, "A")
        self.assertTrue(isinstance(FreshNumber.A, int))

    def test_cooperative_hooks_and_unrelated_classes(self):
        import builtins
        import enum as module
        previous = __build_class__
        calls = []
        def cooperative(body, name, *bases, **keywords):
            calls.append(name)
            return previous(body, name, *bases, **keywords)
        builtins.__build_class__ = cooperative
        try:
            namespace = {"__name__": "cooperative_enum"}
            exec(open(module.__file__).read(), namespace)
            self.assertIs(__build_class__, cooperative)
            class Ordinary:
                A = "a"
            class Mode(namespace["StrEnum"]):
                FAST = "fast"
            self.assertIs(type(Mode.FAST), Mode)
            self.assertEqual(Ordinary.A, "a")
            self.assertTrue("Ordinary" in calls)
            self.assertTrue("Mode" in calls)
        finally:
            builtins.__build_class__ = previous


if __name__ == '__main__':
    unittest.main()
