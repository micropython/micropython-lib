# test_enum.py
# version="1.2.5"

import unittest
from enum import Enum, EnumValue


class TestEnum(unittest.TestCase):
    def setUp(self):
        # Standard Class Definitions for testing
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
        self.assertIsInstance(self.color.RED, EnumValue)
        self.assertEqual(self.status.IDLE.value, 0)

    def test_comparison(self):
        """Test equality between EnumValues and raw values."""
        self.assertTrue(self.color.RED == 1)
        self.assertFalse(self.color.RED == 2)
        self.assertEqual(self.color.RED, self.color.RED)
        # Verify object does not equal value of different type
        self.assertFalse(self.color.RED == "1")

    def test_call_reverse_lookup(self):
        """Test reverse lookup via instance call Color(1) -> RED."""
        result = self.color(1)
        self.assertEqual(result.name, 'RED')
        self.assertEqual(result.value, 1)

        # Test lookup by name string
        result = self.color('RED')
        self.assertEqual(result.name, 'RED')

        result = self.color(self.ColorClass.RED)
        self.assertEqual(result, self.ColorClass.RED)

        with self.assertRaises(AttributeError):
            self.color(999)

    def test_constructor_reverse_lookup(self):
        """Test reverse lookup via class constructor Status(1) -> RUNNING."""
        member = self.StatusClass(1)
        self.assertEqual(member.name, "RUNNING")
        self.assertEqual(member, self.StatusClass.RUNNING)

        with self.assertRaises(AttributeError):
            self.StatusClass(999)

    def test_is_value(self):
        """Test utility method is_value()."""
        self.assertTrue(self.color.is_value(1))
        self.assertTrue(self.color.is_value(3))
        self.assertFalse(self.color.is_value(5))

    def test_iteration(self):
        """Test iteration over Enum instance."""
        members = list(self.color)
        names = [m.name for m in members]
        self.assertEqual(len(members), 3)
        self.assertIn('RED', names)
        self.assertIn('GREEN', names)
        self.assertIn('BLUE', names)

    def test_immutability(self):
        """Verify EnumValue and Enum instance are immutable after init."""
        # EnumValue attribute protection
        with self.assertRaises(AttributeError):
            self.color.RED.value = 10

        # Enum instance attribute protection (static)
        with self.assertRaises(AttributeError):
            self.color.NEW_MEMBER = 4

    def test_deletion_prevention(self):
        """Verify that members cannot be deleted."""
        with self.assertRaises(AttributeError):
            del self.color.RED

    def test_len_and_list(self):
        """Test __len__ and list() utility methods."""
        self.assertEqual(len(self.color), 3)
        members_list = self.color.list()
        self.assertEqual(members_list, [self.color.RED, self.color.GREEN, self.color.BLUE])

    def test_call_method(self):
        """Test calling EnumValue as a function to get its value."""
        self.assertEqual(self.color.RED(), 1)
        self.assertEqual(self.color.GREEN(), 2)

    def test_functional_api(self):
        """Test dynamic Enum creation using the Functional API."""
        # Logic restored from commented out sections
        State = Enum(name='State', names={'ON': 1, 'OFF': 0})
        self.assertTrue(hasattr(State, 'ON'))
        self.assertEqual(State.ON.value, 1)
        self.assertEqual(State.OFF.name, 'OFF')

    def test_serialization_repr_eval(self):
        """Verify eval(repr(obj)) restores the Enum correctly."""
        # Test standard instance
        c_repr = repr(self.color)
        c_restored = eval(c_repr)
        # Check equality of members
        self.assertEqual(self.color.list(), c_restored.list())
        self.assertEqual(type(self.color).__name__, type(c_restored).__name__)

        # Test functional instance
        s_dynamic = Enum(name='StatusFunc', names={'START': 1, 'STOP': 0})
        s_repr = repr(s_dynamic)
        s_restored = eval(s_repr)
        self.assertEqual(s_dynamic.list(), s_restored.list())

        # Test functional instance
        s_dynamic = Enum(name='State', names={'ON': 1, 'OFF': 0})
        s_repr = repr(s_dynamic)
        s_restored = eval(s_repr)
        self.assertEqual(s_dynamic.list(), s_restored.list())


if __name__ == '__main__':
    unittest.main()
