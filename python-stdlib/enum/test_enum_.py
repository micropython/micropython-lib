# test_enum.py
# version="1.2.3"

import unittest
from enum import Enum, EnumValue


class TestEnum(unittest.TestCase):
    def setUp(self):
        # Define standard Enum classes for testing
        class Color(Enum):
            RED = 'red'
            GREEN = 'green'
            BLUE = 'blue'

        class Status(Enum):
            IDLE = 0
            RUNNING = 1
            ERROR = 2

        self.Color = Color
        self.Status = Status
        self.color_inst = Color()
        self.status_inst = Status()

    def test_member_access(self):
        """Test basic access to Enum members, names, and values."""
        self.assertEqual(self.color_inst.RED.name, 'RED')
        self.assertEqual(self.color_inst.RED.value, 'red')
        self.assertEqual(self.status_inst.IDLE.value, 0)

    def test_member_equality(self):
        """Test equality between EnumValues and raw values."""
        self.assertTrue(self.color_inst.RED == 'red')
        self.assertTrue(self.status_inst.RUNNING == 1)
        self.assertFalse(self.status_inst.ERROR == 0)
        # Test equality between two EnumValue objects
        self.assertEqual(self.color_inst.RED, self.color_inst.RED)

    def test_immutability(self):
        """Verify that EnumValue attributes and Enum instances are static."""
        # Test EnumValue immutability
        with self.assertRaises(AttributeError):
            self.color_inst.RED.value = 'blue'

        # Test Enum instance immutability (once initialized)
        with self.assertRaises(AttributeError):
            self.color_inst.NEW_COLOR = 'yellow'

    def test_reverse_lookup_via_constructor(self):
        """Test reverse lookup by passing a value to the class constructor."""
        # Using __new__ logic for reverse lookup
        member = self.Status(1)
        self.assertEqual(member.name, "RUNNING")
        self.assertEqual(member, self.Status.RUNNING)

        with self.assertRaises(AttributeError):
            self.Status(999)

    def test_reverse_lookup_via_instance_call(self):
        """Test reverse lookup by calling the instance with a value."""
        # Using __call__ logic for reverse lookup
        member = self.color_inst('green')
        self.assertEqual(member.name, 'GREEN')

        with self.assertRaises(AttributeError):
            self.color_inst('yellow')

    def test_iteration(self):
        """Test that the Enum instance is iterable and returns all members."""
        members = list(self.status_inst)
        names = [m.name for m in members]
        values = [m.value for m in members]

        self.assertEqual(len(members), 3)
        self.assertIn('IDLE', names)
        self.assertIn(2, values)


#     def test_functional_api(self):
#         """Test dynamic Enum creation using the Functional API."""
#         # Dynamic creation via Enum(name, names_dict)
#         State = Enum(name='State', names={'ON': 1, 'OFF': 0})
#
#         self.assertTrue(hasattr(State, 'ON'))
#         self.assertEqual(State.ON.value, 1)
#         self.assertEqual(State.OFF.name, 'OFF')

#     def test_serialization_repr_eval(self):
#         """Verify that eval(repr(obj)) restores the Enum instance correctly."""
#         # Test standard class instance
#         c_repr = repr(self.color_inst)
#         print('c_repr', c_repr)
#         c_restored = eval(c_repr)
#         self.assertEqual(self.color_inst, c_restored)
#
#         # Test dynamically created instance
#         s_dynamic = Enum(name='State', names={'ON': 1, 'OFF': 0})
#         s_repr = repr(s_dynamic)
#         s_restored = eval(s_repr)
#         self.assertEqual(s_dynamic, s_restored)

    def test_len_and_list(self):
        """Test utility functions like __len__ and list."""
        self.assertEqual(len(self.color_inst), 3)
        members_list = self.color_inst.list()
        self.assertEqual(members_list, [self.color_inst.RED, self.color_inst.GREEN, self.color_inst.BLUE])

    def test_deletion_prevention(self):
        """Verify that members cannot be deleted."""
        with self.assertRaises(AttributeError):
            del self.color_inst.RED

if __name__ == '__main__':
    unittest.main()
