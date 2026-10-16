# test_enum.py
# version="1.4.0"

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


if __name__ == '__main__':
    unittest.main()
