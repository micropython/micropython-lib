# enum

Python enum module for MicroPython implementing PEP 435 (basic enums) and PEP 663 (Flag additions).

Provides standard enumeration types with lazy loading for optimal memory usage.

## Features

- **Enum** - Base enumeration with member management, iteration, and lookup
- **IntEnum** - Integer-valued enum with arithmetic operations (duck-typed)
- **Flag** - Bitwise flag enum with `|`, `&`, `^`, `~` operators
- **IntFlag** - Integer-compatible flags combining Flag and IntEnum behavior
- **StrEnum** - String-valued enum (Python 3.11+)
- **auto()** - Automatic sequential value assignment
- **@unique** - Decorator to prevent duplicate values

## Architecture

The module uses lazy loading to minimize memory footprint:

- **Core** (`core.py`): Enum, IntEnum, EnumMeta (~1.5KB frozen, always loaded)
- **Flags** (`flags.py`): Flag, IntFlag (~500 bytes frozen, loaded on first use)
- **Extras** (`extras.py`): StrEnum, auto, unique (~450 bytes frozen, loaded on first use)

Total memory: ~2KB for basic usage, ~8KB when all features loaded.

## Required MicroPython Features

This module requires metaclass support. Enable the following compile-time flags:

| Feature | Config Flag | Bytes | ROM Level | Required For |
|---------|-------------|-------|-----------|--------------|
| Metaclass `__init__` | `MICROPY_PY_METACLASS_INIT` | +136 | CORE | Enum class initialization |
| Metaclass operators | `MICROPY_PY_METACLASS_OPS` | +240 | EXTRA | `len(EnumClass)`, `member in EnumClass` |
| Metaclass properties | `MICROPY_PY_METACLASS_PROPERTIES` | +88 | EXTRA | Class-level property access |
| Metaclass `__prepare__` | `MICROPY_PY_METACLASS_PREPARE` | +84 | FULL | `auto()` value generation |

**Total C overhead**: 540 bytes when all features enabled (FULL ROM level).

**Minimum requirements**: CORE level for basic Enum/IntEnum. FULL level for auto() support.

## Installation

```bash
mpremote mip install enum
```

Or include in your project's `manifest.py`:

```python
require("enum")
```

## Usage

### Basic Enum

```python
from enum import Enum

class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3

# Access
print(Color.RED)           # <Color.RED: 1>
print(Color(1))            # <Color.RED: 1>
print(Color['RED'])        # <Color.RED: 1>

# Attributes
print(Color.RED.name)      # 'RED'
print(Color.RED.value)     # 1

# Iteration
for color in Color:
    print(color)
```

### IntEnum with Arithmetic

```python
from enum import IntEnum

class HttpStatus(IntEnum):
    OK = 200
    NOT_FOUND = 404

# Integer operations work
print(HttpStatus.OK + 1)       # 201
print(HttpStatus.OK < 300)     # True
print(int(HttpStatus.OK))      # 200
```

### Flag with Bitwise Operations

```python
from enum import Flag

class Permission(Flag):
    READ = 1
    WRITE = 2
    EXECUTE = 4

# Combine flags
read_write = Permission.READ | Permission.WRITE
print(read_write)                   # <Permission.READ|WRITE: 3>

# Check flags
if Permission.READ in read_write:
    print("Can read")

# Remove flags
perms = read_write ^ Permission.WRITE  # Remove WRITE
```

### StrEnum

```python
from enum import StrEnum

class Mode(StrEnum):
    READ = 'r'
    WRITE = 'w'

# String operations work
print(Mode.READ + 'b')         # 'rb'
print(Mode.READ.upper())       # 'R'
```

### Auto Values

```python
from enum import Enum, auto

class Status(Enum):
    PENDING = auto()    # 1
    ACTIVE = auto()     # 2
    DONE = auto()       # 3
```

**Note**: `auto()` requires `MICROPY_PY_METACLASS_PREPARE=1` (FULL ROM level).

### Unique Values

```python
from enum import Enum, unique

@unique
class Status(Enum):
    PENDING = 1
    ACTIVE = 2
    DONE = 1  # ValueError: duplicate values found: DONE -> PENDING
```

## CPython Compatibility

**99.3% compatible** with CPython 3.13 enum module (445/448 official tests pass).

### What Works

- All class-based enum definitions
- auto() value generation
- Explicit and mixed value assignment
- Iteration, lookup, comparison, repr
- Flag bitwise operations
- @unique decorator
- Type mixins (int, str, float, date)
- Pickling/unpickling
- `__members__`, `dir()`, introspection
- Thread-safe enum creation

### Known Limitations

**1. IntEnum isinstance check**

`isinstance(IntEnum.member, int)` returns `False` due to MicroPython's int subclassing limitations. However, all integer operations work correctly.

Workaround: Use arithmetic directly or `int(member)`.

```python
# Works:
HttpStatus.OK + 1        # 201
int(HttpStatus.OK)       # 200

# Doesn't work:
isinstance(HttpStatus.OK, int)  # False (but operations still work)
```

**2. Functional API not supported**

Use class syntax instead:

```python
# Not supported:
Status = Enum('Status', 'PENDING ACTIVE DONE')

# Use instead:
class Status(Enum):
    PENDING = 1
    ACTIVE = 2
    DONE = 3
```

**3. Advanced hooks not implemented**

The following CPython features are not available:
- `_missing_()` - Custom value lookup
- `_ignore_` - Exclude class attributes
- `_generate_next_value_()` - Custom auto() logic
- Boundary modes (STRICT, CONFORM, EJECT, KEEP)

## Testing

The package includes CPython's official enum test suite (`test_enum.py`). To run:

```python
# Using the included test runner
python tools/run_enum_tests.py

# Or run directly
python -m unittest lib.micropython-lib.python-stdlib.enum.test_enum
```

## Documentation

Full CPython enum documentation: https://docs.python.org/3/library/enum.html

## License

MIT License. Based on CPython's enum module implementation.
