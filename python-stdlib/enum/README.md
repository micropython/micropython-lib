# Lightweight Enum

This package provides two lightweight enumeration implementations for MicroPython:

* `enum.py` provides `Enum`, `IntEnum`, and `StrEnum`, multiple forms of the
  functional API, lookup by name or value, iteration, and `.dump()`.
* `enum_mini.py` provides a smaller `Enum` implementation with class-based
  members, dictionary-based functional creation, lookup by name or value, and
  iteration.

Both implementations avoid metaclasses. They use a `builtins.__build_class__`
hook to turn classes derived from their `Enum` base into initialized enum
containers. Members are created lazily by `_i()` when needed; functional-API
enums are initialized during creation. Each member is a dynamically created
subclass of its raw value's type (for example, `int` or `str`), rather than an
instance of the enum container class. As a result, members can compare equal to
their raw values, and members from different enum containers can compare equal
when their values match.

**Important:** Both modules install a process-wide class-building hook when
imported. This affects class creation for classes derived from the relevant
`Enum` base, so use these modules with care in applications that define many
classes or mix implementations.

## Quick start: `enum.py`

```python
from enum import Enum, IntEnum, StrEnum

class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3

print(Color.RED)        # Color.RED
print(Color.RED.name)   # RED
print(Color.RED.value)  # 1

print(Color(2))         # Color.GREEN: lookup by value
print(Color("RED"))     # Color.RED: lookup by name
print(Color["RED"])     # Color.RED: lookup by name
print(list(Color))      # Enum members
print(len(Color))       # 3
print(Color.dump())     # Reconstructable expression
```

`enum.py` also provides constrained value types:

```python
class Priority(IntEnum):
    LOW = 1
    HIGH = 2

class Status(StrEnum):
    PENDING = "pending"
    DONE = "done"

print(Priority.HIGH > 1)              # True
print(isinstance(Priority.LOW, int))  # True
print(Status.PENDING.name.upper())    # PENDING
print(isinstance(Status.DONE, str))   # True
```

`IntEnum` values must be integers and `StrEnum` values must be strings.
Invalid member values raise `TypeError`.

### Standard Behavior (Compatible)
- ✅ Member access: `Color.RED`, `.name`, `.value`
- ✅ Member iteration: `for item in Color`
- ✅ `IntEnum` and `StrEnum` types with strict value checking
- ✅ Immutability: members cannot be modified after creation
- ✅ Functional API: `Enum('Name', {'KEY': value, ...})`

### Non-Standard Behavior
Key differences from CPython:
- **Name-based lookup via call**: `Color("RED")` works for both name and value lookup (CPython standard call only supports value lookup).
- **Value equality**: `Color.RED == 1` is `True` (only true for `IntEnum` in CPython).
- **Custom methods**: `.dump()` does not exist in stdlib `Enum`.
- **Callable members**: `Color.RED()` returns the value (not supported in CPython).
- **Instance `__len__`**: `len(Color)` works; CPython enums are not containers.
- **Serialization**: `dump()` for eval-based reconstruction is MicroPython-specific.

## Comparing the implementations

| Feature | CPython | `enum.py` | `enum_mini.py` |
| --- | --- | --- | --- |
| Enum types | `Enum`, `IntEnum`, `StrEnum` | `Enum`, `IntEnum`, `StrEnum` | `Enum` |
| Lookup by name | `Color["RED"]` | `Color("RED")` or `Color["RED"]` | `Color("RED")` |
| Lookup by value | `Color(1)` | `Color(1)` | `Color(1)` |
| Iteration | `for item in Color` | `for item in Color` | `for item in Color` |
| Iteration in `__members__` | Yes | Yes | Yes |
| `__members__` mapping | Name to member | Member to raw value | Member to raw value |
| Functional API | Dict, names string, list/tuple, or iterable | Dict, names string, list/tuple, or iterable | Dictionary only |
| `start` for generated integer values | Yes | Yes | No |
| Strict integer/string member types | `IntEnum` / `StrEnum` | `IntEnum` / `StrEnum` | Not provided |
| Length | Not provided | `len(Color)` | `len(Color)` |
| `.dump()` | No | Yes | No |
| Plain `Enum` member equals its raw value | No | Yes | Yes |
| Member is an instance of its enum class | Yes | No | No |
| Calling a member, e.g. `Color.RED()` | Not supported | Returns its raw value | Returns its raw value |

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
