# enum_mini_usage.py
# version="1.4.0"

from enum_mini import Enum

# ==============================================================================
# Usage Examples
# ==============================================================================

print("--- Color(Enum) ---")

class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


color = Color()  # Trigger initialization

# 1. Canonical output (str and repr)
print(Color.RED)              # Color.RED
print(repr(Color.RED))        # <Color.RED: 1>

# 2. Attribute access (name and value)
print(Color.RED.name)         # RED
print(Color.RED.value)        # 1

# 3. Equality and identity checks
print(Color.RED == Color.RED) # True
print(Color.RED is Color.RED) # True
print(Color.RED == 1)         # True (like CPython IntEnum; CPython Enum returns False)

# 4. Lookup by value or name (via call)
print(Color(2))               # Color.GREEN
print(Color("RED"))           # Color.RED

# 5. Length and iteration (order may vary)
print(len(Color()))           # 3
print([x for x in Color()])   # [<Color.RED: 1>, <Color.GREEN: 2>, <Color.BLUE: 3>]

# 6. Enum members mapping (order may vary)
print(Color.__members__)      # {<Color.RED: 1>: 1, <Color.GREEN: 2>: 2, <Color.BLUE: 3>: 3}

# 7. Immutability check
try:
    Color.RED.value = 100
    0 / 0
except AttributeError as e:
    print("Immutability test passed:", e)

try:
    color.RED = 100
    0 / 0
except AttributeError as e:
    print("Immutability test passed:", e)

try:
    del color.RED
    0 / 0
except AttributeError as e:
    print("Immutability test passed:", e)

# # test NOT passed
# try:
#     del Color.RED
#     0 / 0
# except AttributeError as e:
#     print("Immutability test passed:", e)

assert Color.RED == 1

# 8. Functional API: Dictionary
Load = Enum("Load", {"LOW": "low", "HIGH": "high"})
print(Load.HIGH)              # Load.HIGH
print(Load.HIGH.value)        # high
print(Load.LOW == "low")      # True (like CPython StrEnum; CPython Enum returns False)


print("\n--- Priority(Enum) - Math & Comparison ---")

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

Priority()

# Arithmetic and numeric comparison (inherits int)
print(Priority.HIGH > 2)             # True
print(Priority.LOW + 10)             # 11
print(isinstance(Priority.LOW, int)) # True


print("\n--- Status(Enum) - String Operations) ---")

class Status(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"

status = Status()

# String operations (inherits str)
print(Status.PENDING == "pending")     # True
print(Status.RUNNING.lower())          # running
print(Status.RUNNING.name.lower())     # running
print(Status.RUNNING.value.upper())    # RUNNING
