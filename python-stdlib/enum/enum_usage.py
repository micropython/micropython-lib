# enum_usage.py
# version="1.5.1"

from enum import Enum, IntEnum, StrEnum

# ==============================================================================
# Usage Examples
# ==============================================================================

# ==============================================================================
# Class Definition Syntax
# ==============================================================================

class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


# 1. Canonical output (str and repr)
print(Color.RED)              # Color.RED
print(repr(Color.RED))        # <Color.RED: 1>

# 2. Attribute access (name and value)
print(Color.RED.name)         # RED
print(Color.RED.value)        # 1

# 3. Equality and identity checks
print(Color.RED == Color.RED) # True
print(Color.RED is Color.RED) # True
print(Color.RED == 1)         # True (like CPython's IntEnum; standard CPython Enum returns False)

# 4. Lookup by value or name (via call)
print(Color(2))               # Color.GREEN
print(Color("RED"))           # Color.RED

# 5. Container access (via instance)
print(Color["RED"])           # Color.RED

# 6. Length and iteration (order may vary)
print(len(Color))             # 3
print([x for x in Color])     # [<Color.RED: 1>, <Color.GREEN: 2>, <Color.BLUE: 3>]

# 7. Serialization and dictionary mapping
print(Color.__members__)      # {<Color.RED: 1>: 1, <Color.GREEN: 2>: 2, <Color.BLUE: 3>: 3}
print(Color.dump())           # Enum('Color', {'BLUE': 3, 'RED': 1, 'GREEN': 2})

# 8. Immutability check
try:
    Color.RED.value = 100
    raise AssertionError("Expected AttributeError on setting attribute")
except AttributeError as e:
    print("Immutability test passed:", e)

try:
    Color.RED = 100
    raise AssertionError("Expected AttributeError on setting attribute")
except AttributeError as e:
    print("Immutability test passed:", e)

try:
    del Color.RED
    raise AssertionError("Expected AttributeError on deleting attribute")
except AttributeError as e:
    print("Immutability test passed:", e)

try:
    del Color.RED
    0 / 0
except AttributeError as e:
    print("Immutability test passed:", e)
print(Color.RED)

assert Color.RED == 1

# 9. Functional API: Comma / space separated string with custom start
State = Enum("State", "OFF, ON", start=10)
print(State.OFF)              # State.OFF
print(State.ON)               # State.ON
print(State.ON.value)         # 11
print(repr(State.ON))         # <State.ON: 11>

# 10. Functional API: Dictionary
Load = Enum("Load", {"LOW": "low", "HIGH": "high"})
print(Load.HIGH)              # Load.HIGH
print(Load.HIGH.value)        # high
print(Load.LOW == "low")      # True (like CPython StrEnum; CPython Enum returns False)

# 11. Functional API: Tuple of pairs
Do = Enum("Do", (("START", 200), ("STOP", 201)))
print(Do.START)               # Do.START
print(Do.STOP)                # Do.STOP
print(Do.STOP.value)          # 201


# ==============================================================================
# IntEnum Example
# ==============================================================================
class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

print("\n--- IntEnum ---")
print(Priority.LOW)                  # 1
print(repr(Priority.LOW))            # <Priority.LOW: 1>

# Arithmetic and numeric comparison (inherits int)
print(Priority.LOW == 1)             # True
print(Priority.HIGH > 2)             # True
print(Priority.LOW + 10)             # 11

# Preserving int type inheritance
print(isinstance(Priority.LOW, int)) # True
print(Priority.dump())               # IntEnum('Priority', {'MEDIUM': 2, 'LOW': 1, 'HIGH': 3})


# ==============================================================================
# StrEnum Example
# ==============================================================================
class Status(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"

print("\n--- StrEnum ---")
print(Status.__members__)
print(Status.PENDING)                  # pending
print(repr(Status.PENDING))            # <Status.PENDING: 'pending'>

# String operations (inherits str)
print(Status.PENDING == "pending")     # True
print(Status.RUNNING.upper())          # RUNNING
print(Status.RUNNING.name)             # RUNNING
print(Status.RUNNING.value.upper())    # RUNNING

# Preserving str type inheritance
print(isinstance(Status.PENDING, str)) # True
print(Status.dump())                   # StrEnum('Status', {'DONE': 'done', 'RUNNING': 'running', 'PENDING': 'pending'})


# ==============================================================================
# StrEnum Functional API
# ==============================================================================
HttpCode = StrEnum("HttpCode", "OK NOT_FOUND INTERNAL_ERROR")

print("\n--- StrEnum Functional API ---")
print(HttpCode.OK.value)                  # ok
print(HttpCode.NOT_FOUND == "not_found")  # True
print(HttpCode.dump())                    # StrEnum('HttpCode', {'NOT_FOUND': 'not_found', 'OK': 'ok', 'INTERNAL_ERROR': 'internal_error'})
