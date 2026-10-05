# enum_check.py
# version="1.4.0"

from enum import Enum, IntEnum, StrEnum

# --- Usage Example 1: Standard Class Definition & Access ---
class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3

# Basic class-level property and method calls
print(f"RED: repr={repr(Color.RED)}, type={type(Color.RED)}, name={Color(1).name}")
print(f"RED: name={Color.RED.name}, value={Color.RED.value}, str={str(Color.RED)}, call={Color.RED()}")
assert Color(1).value == 1
assert Color.BLUE.value >= Color.GREEN.value

# Access members via instance indexing and call syntax
assert Color()["RED"] == Color.RED
assert Color("RED") == Color.RED

# Iteration over Enum members via class instance call
print("Members list:", [member for member in Color()])
print("Names list:", [member.name for member in Color()])
print("Values list:", [member.value for member in Color()])
print()

# Instance-based interaction and comparison checks
c = Color()
print(f"Enum c instance: {c}")

assert c.RED.name == "RED"
assert c.RED.value == 1
assert c.RED == 1
assert c.RED() == 1

# Reverse Lookup via instance call
o = c(1)
print(f"c(1) lookup object: {o}, name={o.name}, value={o.value}")
assert c(1).name == "RED"
assert c(1).value == 1
assert c(1) == 1

# Verify ValueError is raised for invalid key/value lookup
try:
    Color(999)
    assert False, "Should have raised ValueError"
except ValueError as e:
    print(f"ValueError (Caught expected error): {e}\n")


# --- Usage Example 2: Enum Operations & Comparisons ---
class Status(Enum):
    IDLE = 0
    RUNNING = 1
    ERROR = 2

# This simulates receiving a status value from hardware
received_byte = 1
status = Status(received_byte)
print(f"Lookup check: Received {received_byte} -> {status}")
print(f"Enum length via class: {len(Status())}")

assert status == received_byte
assert status == Status.RUNNING
assert status.name == "RUNNING"
assert status.value == received_byte

# Test equality and arithmetic operations
print(f"Comparison check: {status} == 1 is {status == 1}")
assert status == 1
assert status != 0
assert status + 10 == 11

# Verify immutability of Enum member attributes
try:
    Status.RUNNING.value = 999
    assert False, "Should have raised AttributeError"
except AttributeError as e:
    print(f"Immutability check: Passed (Cannot modify EnumValue): {e}\n")

# Iteration over Enum members
print("Iteration check: ", end="")
for m in Status():
    print(f"{m.name}, ", end="")
print("-> Passed")

try:
    Status(999)
    assert False, "Should have raised ValueError"
except ValueError as e:
    print(f"ValueError (Invalid lookup check): Caught expected error -> {e}\n")


# --- Example 3: Functional API, Serialization and Eval ---
print("--- Functional API and Eval Check ---")

c_dump = Color.dump()
print(f"Original Dump: {c_dump}")
c2 = eval(c_dump)
print(f"Restored Class Dump: {c2.dump()}")

# Verify structural equality between restored and original class items
print(Color.__members__)
print(c2.__members__)
assert Color.__members__ == c2.__members__
print("Objects are equal: True")

# Dynamic class creation via functional API with eval()
state = eval("Enum('State', {'ON':1, 'OFF':2})")
print(f"Functional Enum class (state): {state}")
print(f"Type: {type(state)}")
assert state.ON == 1
assert state.ON.name == "ON"
assert state.ON > 0


# --- Example 4: Enum with String Values ---
# Standard Enum holding string values
class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"

api_call = HttpMethod()
print(f"Member with string value: {api_call.GET}")
assert api_call.GET == "GET"

# Lookup by raw value string and member name string via instance invocation
print(f"Lookup by value 'POST': {api_call('POST')}")
print(f"Lookup by name 'DELETE': {api_call('DELETE')}")
assert api_call("GET").name == "GET"


# --- Example 5: Empty Enum Handling ---
# Verifies container behavior when no members are defined
class Empty(Enum):
    pass

empty = Empty()
print(f"Empty Enum items: {empty.__members__}")
assert len(empty) == 0


# --- Example 6: Deep Functional API & Serialization ---
# Functional creation with explicit class name parameter and dictionary mapping
complex_enum = Enum('Config', {'MAX_RETRY': 5, 'TIMEOUT_SEC': 30})

# Verify dump output and reconstruction via eval()
dump_str = complex_enum.dump()
restored = eval(dump_str)

print(f"Restored Functional Enum: {restored.dump()}")
assert restored.MAX_RETRY == 5
assert restored.__name__ == 'Config'


# --- Example 7: Immutability & Integrity Guard ---
# Ensuring that members cannot be added or deleted dynamically post-instantiation
try:
    api_call.NEW_METHOD = "PATCH"
    assert False, "Should have raised AttributeError"
except AttributeError as e:
    print(f"Caught expected mutation error: {e}")

try:
    del api_call.GET
    assert False, "Should have raised AttributeError"
except AttributeError as e:
    print(f"Caught expected deletion error: {e}")

print("\nAll tests passed successfully!")
