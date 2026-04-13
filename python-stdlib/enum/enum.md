Below is the documentation for your `enum.py` library. This file explains the core concepts of your custom `Enum` implementation and provides practical examples for embedded development and general logic.

---

# Custom Enum Library for Python & MicroPython

This library provides a flexible, memory-efficient `Enum` class designed for dynamic usage and seamless mathematical integration. Unlike the standard CPython `Enum`, this version allows for runtime expansion and direct arithmetic operations without needing to access a `.value` property.

## Core Features
* **Transparent Math**: Supports arithmetic (`+`, `-`, `*`, `/`) and bitwise (`&`, `|`, `^`, `<<`, `>>`) operations directly on enum members.
* **Dynamic Expansion**: Add new members at runtime via `.append()` or direct attribute assignment.
* **Memory Efficient**: Uses `__slots__` in the `ValueWrapper` to minimize RAM usage on platforms like the ESP32.
* **Flexible Initialization**: Can be initialized via class inheritance, dictionaries, or keyword arguments.

---

## Usage Examples

### 1. Hardware Pin Configuration (ESP32)
Define your hardware pins using class inheritance. You can skip internal or reserved pins using the `__skipped__` attribute.

```python
from enum import Enum

class Pins(Enum):
    # Members defined at class level
    LED = 2
    BUTTON = 4
    # Members to exclude from the enum mapping
    __skipped__ = ('RESERVED_PIN',)
    RESERVED_PIN = 0

# You can also add pins during instantiation
pins = Pins(SDA=21, SCL=22)

print(f"I2C SDA Pin: {pins.SDA}") # Output: 21
print(f"Is pin 21 valid? {pins.is_value(21)}") # Output: True
```

### 2. Math and Register Logic
The `ValueWrapper` allows you to perform calculations directly. This is particularly useful for bitmasks and step-based logic.

```python
# Initialize with key-value pairs
brightness = Enum(MIN=0, STEP=25, MAX=255)

# Direct arithmetic (Forward and Reflected)
next_level = brightness.MIN + brightness.STEP // 2
complex_math = 100 + brightness.STEP 

print(f"Next Level: {next_level}") # Output: 12
print(f"Complex Math: {complex_math}") # Output: 125

# Bitwise operations for register control
flags = Enum(BIT_0=0x01, BIT_1=0x02)
combined = flags.BIT_0 | flags.BIT_1
print(f"Combined Flags: {hex(combined)}") # Output: 0x03
```

### 3. Dynamic State Machines
You can expand an `Enum` as your program logic progresses, such as adding states to a connection manager.

```python
status = Enum(IDLE=0, CONNECTING=1)

# Add multiple members via append()
status.append(CONNECTED=2, ERROR=3)

# Add a single member via direct assignment
status.DISCONNECTING = 4

for name, val in status.items():
    print(f"Status {name} has code {val}")
```

### 4. Working with Different Data Types
Enums are not restricted to integers; they can wrap strings, floats, and booleans.

```python
commands = Enum(
    START="CMD_START",
    STOP="CMD_STOP",
    TIMEOUT=5.5,
    IS_ACTIVE=True
)

if commands.IS_ACTIVE:
    # Use str() to get the wrapped string value
    print(f"Executing: {commands.START}") 
```

### 5. Introspection and Utilities
The library provides helper methods to validate values or find keys based on their values.

```python
class ErrorCodes(Enum):
    NOT_FOUND = 404
    SERVER_ERROR = 500

# Check if a value exists in the Enum
exists = ErrorCodes.is_value(404) # True

# Get the formatted string name from a value
name = ErrorCodes.key_from_value(500) 
print(name) # Output: ErrorCodes.SERVER_ERROR
```

---

## API Reference

### `ValueWrapper`
The internal class that wraps values to enable mathematical transparency.
* `.value`: Access the raw value.
* `()`: Calling the object returns the raw value.

### `Enum` (Inherits from `dict`)
* `append(arg=None, **kwargs)`: Adds new members to the Enum.
* `is_value(value)`: Returns `True` if the value exists in the Enum.
* `key_from_value(value)`: Returns the string representation (e.g., `ClassName.KEY`) for a given value.
