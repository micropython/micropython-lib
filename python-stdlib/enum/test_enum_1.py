# test_enum.py
# version="1.1.0"

import unittest
from enum import Enum, ValueWrapper


class TestEnum(unittest.TestCase):
    def test_class_initialization(self):
        """Check Enum creation via class inheritance"""
        class Pins(Enum):
            TX = 1
            RX = 3

        pins = Pins()
        self.assertEqual(int(pins.TX), 1)
        self.assertEqual(int(pins.RX), 3)
        self.assertIn('TX', pins)
        self.assertIn('RX', pins)

    def test_dict_initialization(self):
        """Check Enum creation by passing a dictionary to the constructor"""
        e = Enum({'A': 10, 'B': 'test'}, C='C')
        self.assertEqual(e.A.value, 10)
        self.assertEqual(e.B(), 'test')
        self.assertEqual(e.C, 'C')

    def test_value_wrapper_behaviors(self):
        """Check ValueWrapper properties (calling, types, comparison)"""
        v = ValueWrapper(100)
        self.assertEqual(v.value, 100)  # .value
        self.assertEqual(v(), 100)  # __call__
        self.assertEqual(int(v), 100)  # __int__
        self.assertTrue(v == 100)  # __eq__
        self.assertEqual(str(v), "100")  # __str__

    def test_append_and_dynamic_attrs(self):
        """Check dynamic addition of values"""
        e = Enum()
        e.append(C=30)
        e.append({'D': 40}, E=50)
        e.F = 60

        self.assertEqual(int(e.C), 30)
        self.assertEqual(int(e.D), 40)
        self.assertEqual(int(e.E), 50)
        self.assertEqual(int(e.F), 60)
        self.assertIsInstance(e.E, ValueWrapper)
        self.assertIsInstance(e.F, ValueWrapper)

    def test_getattr_error(self):
        """Check that an error is raised when an attribute is missing"""
        e = Enum(A=1)
        with self.assertRaises(AttributeError):
            _ = e.NON_EXISTENT

    def test_is_value_and_key_lookup(self):
        """Check key lookup by value and value validation"""
        class Status(Enum):
            IDLE = 0
            BUSY = 1

        s = Status()
        self.assertTrue(s.is_value(0))
        self.assertTrue(s.is_value(1))
        self.assertFalse(s.is_value(99))
        self.assertEqual(s.key_from_value(1), "Status.X2" if "X2" in dir(s) else "Status.BUSY")
        self.assertEqual(s.key_from_value(1), "Status.BUSY")

    def test_is_loading_protection(self):
        """Check that _is_loading does not end up in dictionary keys"""
        e = Enum(A=1)
        self.assertNotIn('_is_loading', e.keys())
        # Check that the flag is False after initialization
        self.assertFalse(e._is_loading)

    def test_dir_visibility(self):
        """Check for the presence of keys and methods in dir()"""
        e = Enum(DATA=123)
        directory = dir(e)
        self.assertIn('DATA', directory)  # Dynamic data
        self.assertIn('append', directory)  # Enum class method
        self.assertIn('keys', directory)  # Base dict method

    def test_math_and_indexing(self):
        """Check usage in mathematics and as an index"""
        e = Enum(VAL=10)
        # Mathematics
        self.assertEqual(e.VAL + 5, 15)
        # Usage as an index (e.g., in a list)
        ls = [0] * 20
        ls[e.VAL] = 1
        self.assertEqual(ls[10], 1)

    def test_various_types(self):
        """Check operation with various data types"""
        e = Enum(STR="test", FLT=1.5, BL=True)
        self.assertEqual(str(e.STR), "test")
        self.assertEqual(float(e.FLT), 1.5)
        self.assertTrue(e.BL)

    def test_skipped_attributes(self):
        """Check ignoring attributes via __skipped__"""
        class MyEnum(Enum):
            __skipped__ = ('SECRET', )
            PUBLIC = 1
            SECRET = 2

        e = MyEnum()
        self.assertIn('PUBLIC', e)
        self.assertNotIn('SECRET', e)

    def test_post_loading_setattr(self):
        """Check setting attributes after initialization"""
        e = Enum(A=1)
        # Regular attribute (starts with _)
        e._internal = 100
        self.assertEqual(e._internal, 100)
        self.assertNotIn('_internal', e.keys())  # Should not be in data

        # New Enum element
        e.B = 2
        self.assertIsInstance(e.B, ValueWrapper)
        self.assertIn('B', e.keys())

    def test_key_from_value_not_found(self):
        """Check for an error when searching for a non-existent value"""
        e = Enum(A=1)
        with self.assertRaises(ValueError):
            e.key_from_value(999)

    def test_math_division(self):
        """Check floor division and true division"""
        e = Enum(STEP=25)
        # Floor division
        self.assertEqual(e.STEP // 2, 12)
        # True division
        self.assertEqual(e.STEP / 2, 12.5)

    def test_full_arithmetic(self):
        """Check all new arithmetic operations"""
        v = ValueWrapper(10)
        self.assertEqual(v + 5, 15)
        self.assertEqual(20 - v, 10)  # Check __rsub__
        self.assertEqual(v * 2, 20)
        self.assertEqual(30 // v, 3)  # Check __rfloordiv__
        self.assertEqual(v % 3, 1)
        self.assertTrue(v > 5)  # Check comparison

    def test_bitmask_operations(self):
        """Test bitwise operations (important for registers)"""
        flags = Enum(BIT_0=0x01, BIT_1=0x02)

        # Check OR and AND
        combined = flags.BIT_0 | flags.BIT_1
        self.assertEqual(combined, 0x03)
        self.assertEqual(combined & flags.BIT_1, 0x02)

        # Check shifts
        self.assertEqual(flags.BIT_0 << 2, 4)
        self.assertEqual(8 >> flags.BIT_0, 4)  # Check __rrshift__

    def test_unary_operations(self):
        """Test unary operators"""
        e = Enum(VAL=10, NEG_VAL=-5)
        self.assertEqual(-e.VAL, -10)
        self.assertEqual(abs(e.NEG_VAL), 5)
        self.assertEqual(~e.VAL, -11)  # Bitwise NOT


if __name__ == '__main__':
    unittest.main()
