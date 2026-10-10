from enum import Enum

is_micropython = False
try:
    from machine import reset
    is_micropython = True
except Exception:
    pass


class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3

if is_micropython:
    Color()  # Trigger initialization

print("\n--- Basic Lookups ---")
print(Color.RED)                       # Color.RED
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

if is_micropython:
    print(Color())                         # <enum 'Color'>
    print(repr(Color()))                   # <enum 'Color'>
    print(len(Color()))                    # 3
    print(Color("RED"))                    # Color.RED
    print(Color("RED") is Color.RED)       # True
    print(Color.RED == 1)                  # True (like IntEnum)
    print(list(Color()))                   # ['RED', 'GREEN', 'BLUE']
    print(list(Color.__members__))         # ['RED', 'GREEN', 'BLUE']
else:
    print(Color)                           # <enum 'Color'>
    print(repr(Color))                     # <enum 'Color'>
    print(len(Color))                      # 3
    print(Color["RED"])                    # Color.RED
    print(Color["RED"] is Color.RED)       # True
    print(Color.RED == 1)                  # False
    print(list(Color))                     # [<Color.RED: 1>, <Color.GREEN: 2>, <Color.BLUE: 3>]
    print(list(Color.__members__))         # ['RED', 'GREEN', 'BLUE']

print("\n--- Immutability Tests ---")
try:
    Color.RED.value = 99
    0 / 0
except AttributeError:
    print("Protected: Cannot reassign class attribute")

try:
    if is_micropython:
        Color().RED = 99
    else:
        Color.RED = 99
    0 / 0
except AttributeError:
    print("Protected: Cannot reassign class attribute")

try:
    if is_micropython:
        del Color().RED
    else:
        del Color.RED
    0 / 0
except AttributeError:
    print("Protected: Cannot delete class attribute")

assert Color.RED.value == 1
