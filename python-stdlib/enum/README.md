# Lightweight Enum

This package provides two lightweight enumeration implementations for
MicroPython:

* `enum.py` provides `Enum`, `IntEnum`, and `StrEnum`, class declarations,
  several forms of the functional API, name/value lookup, iteration, and
  `.dump()`.
* `enum_mini.py` provides a smaller `Enum` implementation for applications
  that only need basic members, dictionary-based functional creation, lookup,
  and iteration.

Both implementations avoid metaclasses. Members declared in a class are
initialized lazily when the enum is first instantiated or looked up; members
created through the functional API are initialized immediately. Members inherit
from the type of their value, so integer-valued members behave like integers
and string-valued members behave like strings. Consequently, equality with a
raw value (and between members from different enum classes with the same value)
is possible. This differs from Python's standard-library `Enum`.

### Standard Behavior (Compatible)
- ✅ Member access: `Color.RED`, `.name`, `.value`
- ✅ Member iteration: `for item in Color()`
- ✅ `IntEnum` and `StrEnum` types with strict value checking
- ✅ Immutability: members cannot be modified after creation
- ✅ Functional API: `Enum('Name', {'KEY': value, ...})`

### Non-Standard Behavior
Key differences from CPython:
- **Explicit Lazy Initialization**: MicroPython implementations rely on class/instance evaluation (e.g., `Color()`) to trigger lazy member initialization when standard class bodies aren't fully traversed upfront.
- **Name-based lookup via call**: `Color("RED")` works for both name and value lookup (CPython standard call only supports value lookup).
- **Value equality**: `Color.RED == 1` is `True` (only true for `IntEnum` in CPython).
- **Custom methods**: `.dump()` does not exist in stdlib `Enum`.
- **Callable members**: `Color.RED()` returns the value (not supported in CPython).
- **Instance `__len__`**: `len(Color())` works; CPython enums are not containers.
- **Serialization**: `dump()` for eval-based reconstruction is MicroPython-specific.

### Migration Notes
If you're porting code from CPython `enum`:
- Use `Color()` MicroPython requires explicit initialization.
- Replace `Color['RED']` with `Color('RED')`.

## Comparing the implementations

| Feature | CPython | `enum.py` | `enum_mini.py` |
| --- | --- | --- | --- |
| Enum types | `Enum`, `IntEnum`, `StrEnum` | `Enum`, `IntEnum`, `StrEnum` | `Enum` |
| Lookup by name | `Color["RED"]` | `Color("RED")` or `Color()["RED"]` | `Color("RED")` |
| Lookup by value | `Color(1)` | `Color(1)` | `Color(1)` |
| Iteration | `for item in Color` | `for item in Color()` | `for item in Color()` |
| Iteration in `__members__` | Yes | Yes | Yes |
| `__members__` keys and values | Names and members | Members and values | Members and values |
| Functional API | Dict, names string, list/tuple, or iterable | Dict, names string, list/tuple, or iterable | Dictionary only |
| `start` for generated integer values | Yes | Yes | No |
| `.dump()` | No | Yes | No |
| Plain `Enum` member equals its raw value | No | Yes | Yes |
| Member is an instance of its enum class | Yes | No | No |
| Calling the enum without arguments returns a container | No | Yes | Yes |

## Code

The runnable example in [`CPy/CPy.py`](CPy/CPy.py) compares basic member
access, lookup, iteration, equality, and immutability on CPython and
MicroPython.
Run it with `python CPy.py`.

## Limitations

These implementations intentionally provide a smaller API than Python's
standard-library `enum`. In particular, members are value-type instances, not
instances of their enum class; equal values can compare equal across different
enum classes; and enum classes do not provide the full standard-library Enum
semantics. Choose the full implementation when you need `IntEnum`, `StrEnum`,
the expanded functional API, or `.dump()`.
