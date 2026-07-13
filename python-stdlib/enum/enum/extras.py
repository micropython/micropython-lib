"""
Extra enum features for MicroPython.
Contains: auto, StrEnum, unique
"""

from .core import Enum, EnumMeta
from . import core as _core_module


class auto:
    """
    Instances are replaced with an appropriate value for Enum members.
    By default, the initial value starts at 1 and increments by 1.

    Note: In MicroPython, when mixing auto() with explicit values, all auto()
    values are assigned after considering ALL explicit values in the enum.
    This differs from CPython which processes members in definition order.
    """

    def __init__(self):
        # Track creation order via a global counter in core module
        self._order = _core_module._auto_counter
        _core_module._auto_counter += 1
        self._value = None
        self._generation = _core_module._current_enum_generation

    def __repr__(self):
        return "auto()"


class StrEnum(str, Enum, metaclass=EnumMeta):
    """Enum where members are also strings"""

    def __new__(cls, value):
        if not isinstance(value, str):
            raise TypeError(f"StrEnum values must be strings, not {type(value).__name__}")
        # MicroPython doesn't expose str.__new__, use object.__new__
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __str__(self):
        return self._value_

    def __eq__(self, other):
        """StrEnum members compare equal to their string values"""
        if isinstance(other, str):
            return self._value_ == other
        return super().__eq__(other)

    def __add__(self, other):
        """String concatenation"""
        return self._value_ + other

    def __radd__(self, other):
        """Reverse string concatenation"""
        return other + self._value_

    def upper(self):
        """Return uppercase version"""
        return self._value_.upper()

    def lower(self):
        """Return lowercase version"""
        return self._value_.lower()

    def capitalize(self):
        """Return capitalized version"""
        return self._value_.capitalize()

    def replace(self, old, new):
        """Return string with replacements"""
        return self._value_.replace(old, new)


def unique(enumeration):
    """
    Decorator that ensures only one name is bound to each value.
    Raises ValueError if an alias is found.

    Note: This is a simplified version. In minimal implementation,
    consider this optional/deprecated.
    """
    duplicates = []
    for name, member in enumeration._member_map_.items():
        for other_name, other_member in enumeration._member_map_.items():
            if name != other_name and member._value_ == other_member._value_:
                duplicates.append((name, other_name, member._value_))
                break

    if duplicates:
        duplicate_names = ", ".join([f"{n1}/{n2}" for n1, n2, _ in duplicates])
        raise ValueError(f"duplicate values found in {enumeration.__name__}: {duplicate_names}")

    return enumeration


__all__ = ["auto", "StrEnum", "unique"]
