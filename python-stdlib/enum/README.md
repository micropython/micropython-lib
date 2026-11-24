# Enum for MicroPython

Use enums to give a fixed set of values meaningful names, such as modes in
a state machine or settings on a sensor.

- Use `enum.py` for `Enum`, `IntEnum`, or `StrEnum`.
- Use `enum_mini.py` for a smaller alternative when you only need `Enum`.

## Getting started

Copy the module you want to the device alongside your program or into its
library directory. Import `Enum` from `enum` for the full version, or from
`enum_mini` for the mini version.

```python
from enum import Enum

class Color(Enum):
    RED = 1
    GREEN = 2

print(Color.RED.name)   # RED
print(Color.RED.value)  # 1
print(Color(2).name)   # GREEN
```

Members are available as soon as the definition finishes in both versions.
The [full example](examples/enum_usage.py) also shows integer and string
members. The [mini example](examples/enum_mini_usage.py) shows class
declarations and creation from a dictionary. Run each example on MicroPython
with the corresponding module on its import path.

## Differences from CPython

- Both versions accept a member name or value in a call such as `Color("RED")`
  or `Color(1)`. Plain `Enum` members can compare equal to their raw values.
- The full version uses `Color()["RED"]` for subscription and `len(Color())`
  for the length on MicroPython. CPython uses `Color["RED"]` and `len(Color)`.
- The full version maps names to members in `__members__`. Mini maps members
  to raw values. Iteration order can differ from declaration order.
- Member objects and class attributes have different protections. In the full
  version, assigning to or deleting `Color.RED` on the class is possible on
  MicroPython.
- Both modules install a class creation hook when imported. The examples
  use one implementation per program.

## Running the package tests

With MicroPython and the `unittest` package available, run each test file
in a separate process from this directory and check its reported result.

```sh
micropython test_enum.py
micropython test_enum_mini.py
```
