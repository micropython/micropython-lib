# Lightweight Enum

This package provides two lightweight enumeration implementations for MicroPython:

* `enum.py` provides `Enum`, `IntEnum`, and `StrEnum`, multiple forms of the
  functional API, lookup by name or value, iteration, and `.dump()`.
* `enum_mini.py` provides a smaller `Enum` implementation with class-based
  members, dictionary-based functional creation, lookup by name or value, and
  iteration.

Both implementations avoid metaclasses and share one process-wide
`__build_class__` dispatcher. `Enum` and `IntEnum`, and the mini implementation,
keep their existing initialized-container architecture. Their members inherit
raw value types rather than the declared enum class. `StrEnum` instead keeps
the real declared class and constructs genuine string instances of that class.

**Important:** The dispatcher registers both modules and retains families from
fresh imports, so old aliases continue to work. It chains an existing cooperative
class-building hook and leaves later cooperative hooks installed. Hooks that do
not delegate, or manually changing the shared builtin state, are not supported.
Ordinary classes unrelated to a registered enum family are passed through.

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

## Typed `StrEnum` on stock MicroPython

```python
class Mode(StrEnum):
    FAST = "fast"
    SLOW = "slow"

    def describe(self):
        return self.name + ":" + self.value

print(type(Mode.FAST) is Mode)           # True
print(isinstance(Mode.FAST, Mode))       # True
print(isinstance(Mode.FAST, StrEnum))    # True
print(isinstance(Mode.FAST, Enum))       # True
print(isinstance(Mode.FAST, str))        # True
print(Mode("fast") is Mode.FAST)        # True
print(Mode("FAST") is Mode.FAST)        # True
print(Mode(Mode.FAST) is Mode.FAST)      # True
print(Mode.FAST.describe())             # FAST:fast
print(Mode.FAST[0], Mode.FAST[:2])       # f fa
print([member.name for member in Mode]) # order is not guaranteed

Dynamic = StrEnum("Dynamic", "FAST SLOW")
print(Dynamic.FAST.value)               # fast
```

Members are finalized immediately after the class body. Construction through
the declared string subclass is adapted from [Dungeon Drifters' StrEnum by
MrCodeGameAndAnime](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/blob/2fa5f9d0ca806e5e7dbd41f3ac9073465d26762b/root/portability/micropython/enum.py),
building on this package's existing class-finalization hook.

The direct functional API is retained: dictionaries, strings, lists/tuples of
names or pairs, and other name iterables supported by 1.5.0. A string of names
generates lowercase values; lists and other name iterables retain name spelling.
`dump()` still emits `StrEnum(...)`. There is no separate factory API.

String operations, equality and hashing use native string behavior. String-valued
inputs remain members even if callable, and their content is normalized to a
plain string before duplicate detection. Inputs overriding string slicing are
rejected, because stock MicroPython cannot safely bypass that override; members
produced by this package retain safe string slicing and can be reused as values.
Private names are ignored and public declared methods are preserved. Duplicate values,
non-string declarations, custom constructors, mixins and extension of finalized
StrEnum classes are rejected. Member metadata is read-only through normal
attribute assignment/deletion.

### Stock-runtime limits

This is a supported subset, not full CPython enum parity:

- `list(Mode)` and `for member in Mode` use stock MicroPython's class sequence
  fallback. Member indexing and slicing still operate on their string content.
  This class-iteration fallback is not a CPython feature.
- `len(Mode)` and `Mode["FAST"]` are unavailable for the real-class typed profile.
  Use `len(Mode._i())` and `Mode("FAST")` when those operations are needed.
- Class member replacement/deletion is not intercepted. The exposed member-to-value
  metadata dictionary is mutable. Do not modify class members or this metadata.
- Classes keep ordinary class representation. Members keep native string `str`
  and `repr`, rather than enum-style representation, for scalar/list JSON encoding.
- Stock MicroPython has limitations with Python string-subclass dictionary keys,
  including JSON dictionary keys. Use plain `.value` strings when creating keys.
  This package does not change dictionary or JSON runtime behavior.
- `Mode()` returning the class, name lookup by call and callable members returning
  values remain 1.5.0 extensions. Member order follows the runtime's declaration
  dictionary traversal and is not guaranteed.

Generic `Enum`/`IntEnum` and mini containers keep their existing operations and
representations. They are not changed to match the typed StrEnum restrictions.

## Comparing the implementations

| Feature | CPython | `Enum` / `IntEnum` | Typed `StrEnum` (stock MicroPython) | `enum_mini.py` |
| --- | --- | --- | --- | --- |
| Declared-class member identity | Yes | No | Yes | No |
| Name lookup | `Color["RED"]` | `Color("RED")` or `Color["RED"]` | `Mode("FAST")` | `Color("RED")` |
| Value lookup | `Color(1)` | `Color(1)` | `Mode("fast")` | `Color(1)` |
| Iteration | `for item in Color` | `for item in Color` | `for item in Mode` | `for item in Color` |
| Length | `len(Color)` | `len(Color)` | `len(Mode._i())` | `len(Color)` |
| `__members__` mapping | Name to member | Member to raw value | Member to raw value | Member to raw value |
| Functional creation | `Enum(...)` | `Enum(...)` / `IntEnum(...)` | `StrEnum(...)` | `Enum(name, dictionary)` |
| `.dump()` | No | Yes | Yes | No |
| Member repr | Enum-style | Enum-style | Native string | Enum-style |
| Plain Enum equals raw value | No | Yes | String equality | Yes |
| Calling a member | Not supported | Returns value | Returns value | Returns value |

## Code

The runnable example in [`CPy/CPy.py`](CPy/CPy.py) compares basic member
access, lookup, iteration, equality, and immutability on CPython and
MicroPython.
Run it with `python CPy.py`.

## Limitations

The package intentionally provides a smaller API than standard-library `enum`.
Equal raw values can compare equal across different enum classes. Generic Enum,
IntEnum and mini members retain their value-type/container architecture; only
the typed StrEnum profile provides declared-class member identity. The stock
limitations above are intentional boundaries, not prerequisites for a modified
interpreter.

## Tests

With a stock MicroPython 1.29.0 executable and the `unittest` package available,
run both existing files from this directory in separate processes:

```sh
micropython test_enum.py
micropython test_enum_mini.py
```

The files cover full-first and mini-first imports, fresh full imports preserving
old aliases, cooperative hooks, and the typed-member profile. Check each runner's
reported result: some MicroPython unittest versions exit zero even on failure.
