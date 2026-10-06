import unittest
from enum_mini import Enum

# ------------------------------------------------------------------------------
# Test Sample Enum Classes
# ------------------------------------------------------------------------------
class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


class Status(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


Color()
Status()


class TestEnumMini(unittest.TestCase):

    # ==========================================================================
    # Declarative Class API & String Representation
    # ==========================================================================
    def test_class_attributes_and_repr(self):
        """Verify member values, names, str, and repr for int and str enums."""
        self.assertEqual(Color.RED.value, 1)
        self.assertEqual(Color.RED.name, "RED")
        self.assertEqual(str(Color.RED), "Color.RED")
        self.assertEqual(repr(Color.RED), "<Color.RED: 1>")

        self.assertEqual(Status.PENDING.value, "pending")
        self.assertEqual(repr(Status.PENDING), "<Status.PENDING: 'pending'>")

    # ==========================================================================
    # Member Lookup & Calling
    # ==========================================================================
    def test_lookup_by_value_and_name(self):
        """Verify member lookup by value or name via Enum call."""
        self.assertIs(Color(1), Color.RED)
        self.assertIs(Color("RED"), Color.RED)
        self.assertIs(Status("pending"), Status.PENDING)

        # Test calling member instance returns raw value
        self.assertEqual(Color.RED(), 1)

    def test_lookup_invalid_value(self):
        """Verify ValueError is raised on non-existent value/name."""
        with self.assertRaises(ValueError):
            Color(999)
        with self.assertRaises(ValueError):
            Color("YELLOW")

    # ==========================================================================
    # Functional API
    # ==========================================================================
    def test_functional_api_dict(self):
        """Create Enum via dict mapping."""
        Size = Enum("Size", {"S": 36, "M": 38, "L": 40})
        self.assertEqual(Size.S.value, 36)
        self.assertEqual(Size.L.value, 40)

    # ==========================================================================
    # Iteration, Length, and Members Mapping
    # ==========================================================================
    def test_iteration_and_len(self):
        """Verify iteration, len(), and __members__ mapping."""
        self.assertEqual(len(Color()), 3)
        self.assertEqual(list(Color()), [Color.RED, Color.GREEN, Color.BLUE])

        items_dict = Color.__members__
        self.assertIn(Color.RED, items_dict)
        self.assertEqual(items_dict[Color.RED], 1)

    # ==========================================================================
    # Equality & Cross-Enum Comparison
    # ==========================================================================
    def test_equality(self):
        """Verify equality operators for members and cross-enum items."""
        self.assertEqual(Color.RED, Color.RED)
        self.assertNotEqual(Color.RED, Color.GREEN)

        OtherColor = Enum("OtherColor", {"RED": 1})
        self.assertEqual(Color.RED, OtherColor.RED)

    # ==========================================================================
    # Protection & Mutability Limits
    # ==========================================================================
    def test_attribute_setting_protection(self):
        """Ensure attribute modification/deletion is blocked on items and class instances."""
        with self.assertRaises(AttributeError):
            Color.RED.value = 100

        with self.assertRaises(AttributeError):
            Color.RED.new_attr = "test"

        with self.assertRaises(AttributeError):
            Color().NEW_MEMBER = 4

        with self.assertRaises(AttributeError):
            del Color().RED


if __name__ == "__main__":
    unittest.main()