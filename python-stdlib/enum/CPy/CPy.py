from enum import Enum, StrEnum, IntEnum


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

print("\n--- Functional API & Extensions ---")
try:
    DynCoord = Enum("DynCoord", {"X": 10, "Y": 20})
    print(DynCoord)                           # <enum 'DynCoord'>
    print(type(DynCoord))                     # <class 'enum.EnumType'> #  <class 'DynCoord'>
    print(DynCoord.__members__)               # {'X': <DynCoord.X: 10>, 'Y': <DynCoord.Y: 20>} # {<DynCoord.Y: 20>: 20, <DynCoord.X: 10>: 10}
    print(list(DynCoord))                     # [<DynCoord.X: 10>, <DynCoord.Y: 20>] # [<DynCoord.Y: 20>, <DynCoord.X: 10>]
    print(DynCoord.X.value)                   # 10

except Exception as e:
    print_exception(e)
    print(f"Functional dict API error: {e}")

print()
try:
    DynStr = StrEnum("DynStr", "A B C")
    print(DynStr)                             # <enum 'DynStr'>
    print(type(DynStr))                       # <class 'enum.EnumType'> # <class 'DynStr'>
    print(DynStr.__members__)                 # {'A': <DynStr.A: 'a'>, 'B': <DynStr.B: 'b'>, 'C': <DynStr.C: 'c'>} # {<DynStr.A: 'a'>: 'a', <DynStr.C: 'c'>: 'c', <DynStr.B: 'b'>: 'b'}
    print(list(DynStr))                       # [<DynStr.A: 'a'>, <DynStr.B: 'b'>, <DynStr.C: 'c'>] # [<DynStr.A: 'a'>, <DynStr.C: 'c'>, <DynStr.B: 'b'>]
    print(DynStr.A.value)                     # a
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
    print(list(Restored))                     # [<Color.RED: 1>, <Color.GREEN: 2>, <Color.BLUE: 3>]
    print("Restored equality:", Restored == Color)                      # True
    print("Restored equality:", Restored.RED.value == Color.RED.value)  # True
