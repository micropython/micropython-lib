# Enum Library

This library provides a lightweight, memory-efficient `Enum` implementation designed for MicroPython environments. It focuses on immutability, reverse lookup capabilities, and serialization support without the complexity of metaclasses.

---

## Core Features
* **Immutability**: Enum members (`EnumValue`) are protected against modification. Any attempt to change their name or value raises an `AttributeError`.
* **Static Design**: Once an Enum instance is initialized, it is "frozen." You cannot add new attributes or delete existing members.
* **Dual Reverse Lookup**:
    * **Class Constructor**: Retrieve a member by value using the class name (e.g., `Status(1)`).
    * **Instance Call**: Retrieve a member by value by calling the instance (e.g., `s(1)`).
* **Serialization Support**: Implements `__repr__` such that `obj == eval(repr(obj))`, allowing easy restoration of Enum states.
* **Functional API**: Supports dynamic creation of Enums at runtime.

---

## Usage Examples

### 1. Standard Class Definition
Define your enumeration by inheriting from the `Enum` class. Class-level constants are automatically converted into `EnumValue` objects upon initialization.

```python
from enum import Enum

class Color(Enum):
    RED = 'red'
    GREEN = 'green'

# Initialize the enum to process attributes
c = Color()

print(c.RED)        # Output: RED: red
print(c.RED.name)   # Output: RED
print(c.RED.value)  # Output: red
print(c.RED())      # Output: red
```


### 2. Reverse Lookup
The library provides two ways to find a member based on its raw value.

```python
class Status(Enum):
    IDLE = 0
    RUNNING = 1

# Method A: Via Class (Simulates interpreting hardware/network bytes)
# Uses __new__ logic to return the correct EnumValue
current_status = Status(1)
print(current_status.name)  # Output: RUNNING
print(current_status)       # Output: RUNNING: 1
print(current_status())     # Output: 1

# Method B: Via Instance Call
s = Status()
print(s(0).name)            # Output: IDLE
print(s(0))                 # Output: IDLE: 0
print(s(0)())               # Output: 0
```


### 3. Functional API (Dynamic Creation)
If you need to create an Enum from external data (like a JSON config), use the functional constructor.

```python
# Create a dynamic Enum instance
State = Enum(name='State', names={'ON': 1, 'OFF': 2})

print(State.ON)      # Output: ON: 1
assert State.ON == 1 # Comparison with raw value
```


### 4. Serialization (Repr / Eval)
The library ensures that the string representation can be used to perfectly reconstruct the object.

```python
colors = Color()
# Get serialized string
serialized = repr(colors)
# Reconstruct object
restored_colors = eval(serialized)

print(f"Original: {colors}")           # Output: Original: Color(names={'ON': 1, 'OFF': 2, 'GREEN': 'green', 'RED': 'red'})
print(f"Restored: {restored_colors}")  # Output: Restored: Color(names={'ON': 1, 'OFF': 2, 'GREEN': 'green', 'RED': 'red'})
print(colors == restored_colors)       # Output: True

```


---

## API Reference

### `EnumValue`
The object representing a specific member of an Enum.
* `.name`: The string name of the member.
* `.value`: The raw value associated with the member.
* `()`: Calling the member object returns its raw value (e.g., `c.RED() -> 'red'`).

### `Enum`
The base class for all enumerations.
* `list()`: Returns a list of all defined members.
* `is_value(value)`: Returns `True` if the provided raw value exists within the Enum.
* `__len__`: Returns the total number of members.
* `__iter__`: Allows looping through members (e.g., `[m.name for m in color_inst]`).

---

## Error Handling
* **`AttributeError`**:
    * Raised when attempting to modify an `EnumValue`.
    * Raised when attempting to add new members to an initialized Enum.
    * Raised when a class-level lookup (`Status(999)`) fails.
    * Raised when an instance-level lookup (`s(999)`) fails.

## Compare with CPython

```python
# Run on MicroPython v1.28.0 on 2026-04-06; Generic ESP32 module with ESP32
# Run on Python 3.12.10
from enum import Enum

# class syntax
class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3

# OR
# functional syntax
# Color = Enum('Color', {'RED': 1, 'GREEN': 2, 'BLUE': 3})

# List enum members
try:
    print(list(Color))
# [<Color.RED: 1>, <Color.GREEN: 2>, <Color.BLUE: 3>]
except:
    print(Color.list())
# [RED: 1, GREEN: 2, BLUE: 3]

# Accessing enum member by name
print(Color.GREEN, type(Color.GREEN))
# Color.GREEN  <enum 'Color'>
# GREEN: 2 <class 'EnumValue'>

# Accessing enum member by name
try:
    print(Color['GREEN'])
# Color.GREEN
except:
    print(Color('GREEN'))
# GREEN: 2

# Accessing enum member by value
print(Color(2))
# Color.GREEN

# Accessing enum member name
print(Color.GREEN.name, type(Color.GREEN.name))
#  GREEN <class 'str'>

# Accessing enum member value
print(Color.GREEN.value, type(Color.GREEN.value))
# 2 <class 'int'>
```

### Output is:

| MicroPython v1.28.0  |  Python 3.12.10  |
|   :---   |   :---  |
| [RED: 1, GREEN: 2, BLUE: 3] | [<Color.RED: 1>, <Color.GREEN: 2>, <Color.BLUE: 3>] |
| GREEN: 2 <class 'EnumValue'> | Color.GREEN <enum 'Color'> |
| GREEN: 2 | Color.GREEN |
| GREEN: 2 | Color.GREEN |
| GREEN <class 'str'> | GREEN <class 'str'> |
| 2 <class 'int'> | 2 <class 'int'> |

