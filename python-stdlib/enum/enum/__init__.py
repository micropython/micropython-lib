"""
Minimal Enum implementation for MicroPython.
Compatible with CPython's enum module (basic features only).

Uses lazy loading pattern similar to asyncio to reduce initial memory footprint.
Core classes (Enum, IntEnum, EnumMeta) are always loaded.
Optional classes (Flag, IntFlag, StrEnum, auto, unique) are loaded on demand.
"""

from .core import *

__version__ = (1, 0, 0)


# Internal helpers for CPython compatibility
def _simple_enum(enum_class):
    """
    Decorator for creating simple enums from member names (CPython compat).
    This is a minimal stub for stdlib compatibility - returns a passthrough decorator.
    """

    def decorator(member_names):
        """Passthrough decorator - functional API not fully implemented"""
        # For stdlib compatibility, just return the enum class unchanged
        # The stdlib uses this but doesn't require full functional API
        return enum_class

    return decorator


_test_simple_enum = _simple_enum

_attrs = {
    "Flag": "flags",
    "IntFlag": "flags",
    "auto": "extras",
    "StrEnum": "extras",
    "unique": "extras",
}


def __getattr__(attr):
    """
    Lazy loader for optional enum features.
    Loads Flag, IntFlag, StrEnum, auto, and unique only when first accessed.
    """
    mod = _attrs.get(attr, None)
    if mod is None:
        raise AttributeError(f"module 'enum' has no attribute '{attr}'")
    # Import the module relative to this package
    # Use positional arguments for MicroPython compatibility
    imported_mod = __import__(f"enum.{mod}", None, None, [attr])
    value = getattr(imported_mod, attr)
    globals()[attr] = value
    return value
