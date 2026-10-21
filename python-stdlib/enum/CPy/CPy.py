import sys
# CPy.py
# version="1.5.1"

is_micropython = False
try:
    from machine import reset
    is_micropython = True
except ImportError:
    pass

from enum import Enum, StrEnum, IntEnum


def section(s):
    print(s)
    
    
# ---------------------------------------------------------------------------
# 1. Basic class-based Enum
# ---------------------------------------------------------------------------
section("Basic Enum (class syntax)")

class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


print("\n--- Basic Lookups ---         # CPython # MicroPython output")
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
print(len(Color))                      # 3
print(Color["RED"])                    # Color.RED
print(Color["RED"] is Color.RED)       # True
print(Color.RED == 1)                  # False # True
# ---------------------------------------------------------------------------
# 2. Immutability
# ---------------------------------------------------------------------------

print("\n--- Immutability Tests ---")
try:
    Color.RED.value = 99
    0 / 0
except AttributeError:
    print("Protected: Cannot reassign class attribute")

try:
    Color.RED = 99
    0 / 0
except AttributeError:
    print("Protected: Cannot reassign class attribute")

try:
    del Color.RED
    0 / 0
except AttributeError:
    print("Protected: Cannot delete class attribute")

try:
    Color.RED.custom = 5
    print("NOT Protected: Set attribute on enum item")  # NOT Protected: Set attribute on enum item
except AttributeError:
    print("Protected: Cannot set attribute on enum item")  # Protected: Cannot set attribute on enum item

assert Color.RED.value == 1
# ---------------------------------------------------------------------------
# 3. Functional API
# ---------------------------------------------------------------------------

print("\n--- Functional API & Extensions ---")
try:
    DynCoord = Enum("DynCoord", {"X": 10, "Y": 20})
    print(DynCoord)                           # <enum 'DynCoord'>
    print(type(DynCoord))                     # <class 'enum.EnumType'> #  <class 'DynCoord'>
    print(DynCoord.__members__)               # {'X': <DynCoord.X: 10>, 'Y': <DynCoord.Y: 20>} # {<DynCoord.Y: 20>: 20, <DynCoord.X: 10>: 10}
    # Functional generic enums retain their container API on MicroPython.
    coord_members = DynCoord() if sys.implementation.name == "micropython" else DynCoord
    print(list(coord_members))                # Order may vary on MicroPython.
    print(DynCoord.X.value)                   # 10

except Exception as e:
    print(f"Functional dict API error: {e}")

print()
try:
    DynStr = StrEnum("DynStr", "A B C")
    print(DynStr)                             # <enum 'DynStr'>
    print(type(DynStr))                       # <class 'enum.EnumType'> # <class 'DynStr'>
    print(DynStr.__members__)                 # {'A': <DynStr.A: 'a'>, 'B': <DynStr.B: 'b'>, 'C': <DynStr.C: 'c'>} # {'a': 'a', 'c': 'c', 'b': 'b'}
    print(list(DynStr))                       # [<DynStr.A: 'a'>, <DynStr.B: 'b'>, <DynStr.C: 'c'>] # ['a', 'c', 'b']
    print(DynStr.A.value)                     # a
    print(type(DynStr.A) is DynStr)           # True
    print(isinstance(DynStr.A, StrEnum))      # True
    print(repr(DynStr.A))                     # <DynStr.A: 'a'> # 'a' on MicroPython
except Exception as e:
    print(f"Functional string API not supported or error: {e}")

try:
    class Colors(Color):
        YELLOW = 'yellow'
except TypeError as e:
    print(f"TypeError: {e}")

if hasattr(Color, "dump"):
    print("\n--- Dump & Restore (if available) ---")
    d_str = Color.dump()
    print("Dump:", d_str)
    Restored = eval(d_str)                    # Dump: Enum('Color', {'BLUE': 3, 'RED': 1, 'GREEN': 2})
    print(Restored)                           # <enum 'Color'>
    print(type(Restored))                     # <class 'Color'>
    print(Restored.__members__)               # {<Color.RED: 1>: 1, <Color.GREEN: 2>: 2, <Color.BLUE: 3>: 3}
    print(list(Restored()))                   # [<Color.RED: 1>, <Color.GREEN: 2>, <Color.BLUE: 3>]
    print("Restored equality:", Restored == Color)                      # True
    print("Restored equality:", Restored.RED.value == Color.RED.value)  # True

# ---------------------------------------------------------------------------
# 4. StrEnum class vs instance
# ---------------------------------------------------------------------------
print()

class Mode(StrEnum):
    FAST = "fast"
    SLOW = "slow"

class Mode2(StrEnum):
    FAST2 = "fast2"
    SLOW2 = "slow2"

print("--- Class ---")
print("Mode:", Mode)
print("type(Mode):", type(Mode))
print("Mode.FAST:", Mode.FAST)
print("type(Mode.FAST):", type(Mode.FAST))
print("Members:", getattr(Mode, "__members__", None))

assert Mode.FAST.name == "FAST"
assert Mode.FAST.value == "fast"
assert Mode("fast") is Mode.FAST
assert Mode(Mode.FAST) is Mode.FAST

assert isinstance(Mode.FAST, str)

if is_micropython:
    assert isinstance(Mode, Enum)
    assert isinstance(Mode, (StrEnum, type(StrEnum)))
else:
    pass

# ---------------------------------------------------------------------------
# 5. Instance pattern (MicroPython-friendly)
# ---------------------------------------------------------------------------

if is_micropython:
    assert issubclass(type(Mode), Enum)
    assert issubclass(type(Mode), (StrEnum, type(StrEnum)))
else:
    assert issubclass(Mode, Enum)
    assert issubclass(Mode, StrEnum)

assert isinstance(Mode.FAST, str)
if is_micropython:
    assert isinstance(Mode.FAST, type(Mode))
else:
    assert isinstance(Mode.FAST, Mode)

if is_micropython:
    print()
    print("--- Instance ---")
    mode = Mode()
    print("mode:", mode)
    print("type(mode):", type(mode))
    print("mode.FAST:", mode.FAST)
    print("type(mode.FAST):", type(mode.FAST))
    print("Members:", getattr(mode, "__members__", None))

    assert mode.FAST.name == "FAST"
    assert mode.FAST.value == "fast"
    assert mode("fast") is mode.FAST
    assert mode(mode.FAST) is mode.FAST

    assert isinstance(mode.FAST, str)

    assert issubclass(type(mode), Enum)
    assert issubclass(type(mode), (StrEnum, type(StrEnum)))

    assert isinstance(mode, Enum)
    assert isinstance(mode, (StrEnum, type(StrEnum)))

    assert isinstance(mode.FAST, str)
    assert isinstance(mode.FAST, type(mode))

    assert type(mode) is type(Mode)
    assert mode == Mode
