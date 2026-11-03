"""
Flag and IntFlag enum classes for MicroPython.
Contains: Flag, IntFlag
"""

from .core import Enum, EnumMeta


class FlagMeta(EnumMeta):
    """Metaclass for Flag enums with combination membership testing"""

    def __contains__(cls, value):
        """Check if value is a valid flag or flag combination"""
        # First check if it's an explicitly named member
        if isinstance(value, cls) and value._name_ in cls._member_map_:
            return True

        # For integer values, check if it's a valid combination of member bits
        if isinstance(value, int):
            # Calculate all valid bits from all members
            all_bits = 0
            for member in cls:
                all_bits |= member._value_

            # Value is valid if all its bits exist in at least one member
            # and value is non-negative
            return value >= 0 and (value & all_bits) == value

        return False


class Flag(Enum, metaclass=FlagMeta):
    """Support for flags with bitwise operations"""

    def _create_pseudo_member_(self, value):
        """Create a pseudo-member for composite flag values"""
        # Try to find existing member first
        if value in self.__class__._value2member_map_:
            return self.__class__._value2member_map_[value]

        # Create a new pseudo-member for composite values
        pseudo_member = object.__new__(self.__class__)
        pseudo_member._value_ = value
        pseudo_member._name_ = None  # Composite members don't have simple names
        return pseudo_member

    def __or__(self, other):
        if isinstance(other, self.__class__):
            return self._create_pseudo_member_(self._value_ | other._value_)
        elif isinstance(other, int):
            return self._create_pseudo_member_(self._value_ | other)
        return NotImplemented

    def __and__(self, other):
        if isinstance(other, self.__class__):
            return self._create_pseudo_member_(self._value_ & other._value_)
        elif isinstance(other, int):
            return self._create_pseudo_member_(self._value_ & other)
        return NotImplemented

    def __xor__(self, other):
        if isinstance(other, self.__class__):
            return self._create_pseudo_member_(self._value_ ^ other._value_)
        elif isinstance(other, int):
            return self._create_pseudo_member_(self._value_ ^ other)
        return NotImplemented

    def __invert__(self):
        # Calculate the complement based on all defined flag values
        all_bits = 0
        for member in self.__class__:
            all_bits |= member._value_
        return self._create_pseudo_member_(all_bits & ~self._value_)

    # Reverse operations for when Flag is on the right side
    __ror__ = __or__
    __rand__ = __and__
    __rxor__ = __xor__


class IntFlag(int, Flag, metaclass=FlagMeta):
    """Flag enum that is also compatible with integers"""

    def _create_pseudo_member_(self, value):
        """Create a pseudo-member for composite flag values"""
        # Try to find existing member first
        if value in self.__class__._value2member_map_:
            return self.__class__._value2member_map_[value]

        # Create a new pseudo-member for composite values
        pseudo_member = object.__new__(self.__class__)
        pseudo_member._value_ = value
        pseudo_member._name_ = None  # Composite members don't have simple names
        return pseudo_member

    def __or__(self, other):
        if isinstance(other, self.__class__):
            return self._create_pseudo_member_(self._value_ | other._value_)
        elif isinstance(other, int):
            return self._create_pseudo_member_(self._value_ | other)
        return NotImplemented

    def __and__(self, other):
        if isinstance(other, self.__class__):
            return self._create_pseudo_member_(self._value_ & other._value_)
        elif isinstance(other, int):
            return self._create_pseudo_member_(self._value_ & other)
        return NotImplemented

    def __xor__(self, other):
        if isinstance(other, self.__class__):
            return self._create_pseudo_member_(self._value_ ^ other._value_)
        elif isinstance(other, int):
            return self._create_pseudo_member_(self._value_ ^ other)
        return NotImplemented

    __ror__ = __or__
    __rand__ = __and__
    __rxor__ = __xor__


__all__ = ["Flag", "IntFlag"]
