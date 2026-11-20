# CPy.py
# version="1.5.2"

import sys

is_micropython = sys.implementation.name == "micropython"

if is_micropython:
    from sys import print_exception

from enum import Enum, EnumMeta, StrEnum, IntEnum

class Mode(Enum):
    FAST = "fast"
    SLOW = "slow"

    def describe(self):
        return self.name + ":" + self.value

print('Mode:', Mode)
print('type(Mode):', type(Mode))
print('Mode.FAST:', Mode.FAST)
print('type(Mode.FAST):', type(Mode.FAST))

m = Mode.FAST
print('m:', m)


class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


print("--- Enum (class syntax) ---     # CPython # MicroPython output")
print(Color)                           # <enum 'Color'>
print(type(Color))                     # <class 'enum.EnumType'> # <class 'Color'>
print(Color.__members__)               # {'RED': <Color.RED: 1>, 'GREEN': <Color.GREEN: 2>, 'BLUE': <Color.BLUE: 3>} # {<Color.RED: 1>: 1, <Color.GREEN: 2>: 2, <Color.BLUE: 3>: 3}
print(list(Color))                     # [<Color.RED: 1>, <Color.GREEN: 2>, <Color.BLUE: 3>]

print(Color.RED)                       # Color.RED
print(type(Color.RED))                 # <enum 'Color'> # <class 'Color.RED'>
print(Color.RED.name)                  # RED
print(Color.RED.value)                 # 1
print(repr(Color.RED))                 # <Color.RED: 1>
print(Color.__contains__(1))           # True
print(Color.__contains__(11))          # False
print(Color.__contains__(Color.RED))   # True
print(Color.RED.value == 1)            # True
print(Color.RED.value + 10)            # 11
print(Color(1) is Color.RED)           # True
print()

print(Color)                           # <enum 'Color'>
print(repr(Color))                     # <enum 'Color'>
if is_micropython:
    print(len(Color()))                # 3
    print(Color()["RED"])              # Color.RED
    print(Color()["RED"] is Color.RED) # True
    print(Color.RED == 1)              # True
else:
    print(len(Color))                  # 3
    print(Color["RED"])                # Color.RED
    print(Color["RED"] is Color.RED)   # True
    print(Color.RED == 1)              # False

print("\n--- Immutability Tests ---")
try:
    Color.RED.value = 99
    0 / 0
except AttributeError:
    print("Protected: Cannot reassign class attribute")

try:
    Color.RED = 99
    if is_micropython:
        print("MicroPython: NOT Protected: Can reassign class attribute")
        Color.RED = Color._i()["RED"]
    else:
        0 / 0
except AttributeError:
    print("Protected: Cannot reassign class attribute")

try:
    del Color.RED
    if is_micropython:
        print("MicroPython: NOT Protected: Can delete class attribute")
        Color.RED = Color._i()["RED"]
    else:
        0 / 0
except AttributeError:
    print("Protected: Cannot delete class attribute")

try:
    Color.RED.custom = 5
    print("CPython: NOT Protected: Set attribute on enum item")  # CPython: NOT Protected: Set attribute on enum item
except AttributeError:
    print("MicroPython: Protected: Cannot set attribute on enum item")  # MicroPython: Protected: Cannot set attribute on enum item

assert Color.RED.value == 1

print("\n--- Functional API & Extensions ---")
try:
    DynCoord = Enum("DynCoord", {"X": 10, "Y": 20})
    print(DynCoord)                           # <enum 'DynCoord'>
    print(type(DynCoord))                     # <class 'enum.EnumType'> #  <class 'DynCoord'>
    print(DynCoord.__members__)               # {'X': <DynCoord.X: 10>, 'Y': <DynCoord.Y: 20>} # {<DynCoord.Y: 20>: 20, <DynCoord.X: 10>: 10}
    print(list(DynCoord))                     # [<DynCoord.X: 10>, <DynCoord.Y: 20>] # [<DynCoord.Y: 20>, <DynCoord.X: 10>]
    print(DynCoord.X.value)                   # 10
    print(type(DynCoord.X) is DynCoord)       # True
except Exception as e:
    print(f"Functional dict API error: {e}")
    print_exception(e)
    1/0

print()
try:
    DynStr = StrEnum("DynStr", "A B C")
    print(DynStr)                             # <enum 'DynStr'>
    print(type(DynStr))                       # <class 'enum.EnumType'> # <class 'DynStr'>
    print(DynStr.__members__)                 # {'A': <DynStr.A: 'a'>, 'B': <DynStr.B: 'b'>, 'C': <DynStr.C: 'c'>} # {<DynStr.A: 'a'>: 'a', <DynStr.C: 'c'>: 'c', <DynStr.B: 'b'>: 'b'}
    print(list(DynStr))                       # [<DynStr.A: 'a'>, <DynStr.B: 'b'>, <DynStr.C: 'c'>] # [<DynStr.A: 'a'>, <DynStr.C: 'c'>, <DynStr.B: 'b'>]
    print(DynStr.A.value)                     # a
    print(type(DynStr.A) is DynStr)           # True

    print(isinstance(DynStr.A, StrEnum))      # True
    print(repr(DynStr.A))                     # <DynStr.A: 'a'> # 'a' on MicroPython
except Exception as e:
    print(f"Functional string API not supported or error: {e}")
    print_exception(e)

try:
    class Colors(Color):
        YELLOW = 'yellow'
except TypeError as e:
    print(f"TypeError: {e}")  # TypeError: <enum 'Colors'> cannot extend <enum 'Color'> # TypeError: Colors cannot extend Color
    if is_micropython:
        print_exception(e)

if is_micropython:
    print("\n--- Dump & Restore (if available) ---")
    d_str = Color.dump()
    print("Dump:", d_str)                     # Dump: Enum('Color', {'BLUE': 3, 'RED': 1, 'GREEN': 2})
    Restored = eval(d_str)
    print(Restored)                           # <enum 'Color'>
    print(type(Restored))                     # <class 'Color'>
    print(list(Restored()))                   # [<Color.RED: 1>, <Color.GREEN: 2>, <Color.BLUE: 3>]
    print(Color.__members__)                  # {<Color.RED: 1>: 1, <Color.GREEN: 2>: 2, <Color.BLUE: 3>: 3}
    print(Restored.__members__)               # {<Color.RED: 1>: 1, <Color.GREEN: 2>: 2, <Color.BLUE: 3>: 3}
    print("Restored equality:", Restored == Color)                      # True
    print("Color.RED.value:", Color.RED.value)  # True
    print("Restored.RED.value:", Restored.RED.value)  # True
    print("Restored equality:", Restored.RED.value == Color.RED.value)  # True

class Mode(StrEnum):
    FAST = "fast"
    SLOW = "slow"

print("\n--- Class ---")
print(list(Mode))
print("Mode:", Mode)
print("type(Mode):", type(Mode))
print("Mode.FAST:", Mode.FAST)
print("type(Mode.FAST):", type(Mode.FAST))
print('Mode("fast"):', Mode("fast"))
print('type(Mode("fast")):', type(Mode("fast")))
print("Members:", getattr(Mode, "__members__", None))

assert isinstance(Mode.FAST, str)

assert Mode.FAST.name == "FAST"
assert Mode.FAST.value == "fast"
#assert Mode(Mode.FAST) is Mode.FAST
#assert Mode("fast") is Mode.FAST

if is_micropython:
    assert issubclass(Mode, str)
    assert issubclass(Mode, EnumMeta)
    assert issubclass(Mode, Enum)
    assert issubclass(Mode, StrEnum)

    assert isinstance(Mode, type)
    assert isinstance(Mode(), str)
    assert isinstance(Mode(), Enum)
    assert isinstance(Mode(), StrEnum)
else:
    pass

if is_micropython:
    assert issubclass(Mode, Enum)
    assert issubclass(Mode, StrEnum)
    pass
else:
    assert issubclass(Mode, Enum)
    assert issubclass(Mode, StrEnum)

if is_micropython:
    assert isinstance(Mode.FAST, Mode)
    pass
else:
    assert isinstance(Mode.FAST, Mode)

if is_micropython:
    print("\n--- Instance(MicroPython) ---")
    mode = Mode()
    print("Mode:", Mode)
    print("mode:", mode)
    print("type(mode):", type(mode))
    print("mode.FAST:", mode.FAST)
    print("type(mode.FAST):", type(mode.FAST))
    print("Members:", getattr(mode, "__members__", None))

    assert mode.FAST.name == "FAST"
    assert mode.FAST.value == "fast"
    assert mode("fast") is mode.FAST
    assert mode(mode.FAST) is mode.FAST

    assert issubclass(type(mode), Enum)
    assert issubclass(type(mode), StrEnum)

    assert isinstance(mode, Enum)
    assert isinstance(mode, StrEnum)

    assert isinstance(mode.FAST, str)
    assert isinstance(mode.FAST, type(mode))

    assert type(mode) is Mode
    print("Mode Members:", Mode.__members__)
    print("mode Members:", mode.__members__)
    Mode1 = Mode
    assert Mode1 == Mode
    #assert Mode == mode
    #assert mode == Mode
