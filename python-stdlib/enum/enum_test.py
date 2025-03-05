# enum_test.py

from enum import Enum, enum


class Direction(Enum):
    CW = "CW"
    CCW = "CCW"


class State(Direction):
    Stop = 1
    Run = 2
    Ready = 3
    Disabled = False
    Enabled = True


state = Enum()
print(state)
state = Direction()
print(state)
state = State()
print(state)
state = State({"X": 1.0, "Y": 2.0})
print(state)
state.Idle = 10
state.Triggered = 20
state.Lockout = 30
print(state)

print("Direction(Direction.CCW):", Direction(Direction.CCW))
print("Direction('CW'):", Direction("CW"))
print("state(10):", state(10))

print("state('CW'):", state("CW"))
print("type(state('CW')):", type(state("CW")))

print("state.key_from_value(20):", state.key_from_value(20))
print("len(state):", len(state))

print("state.Idle:", state.Idle)
print("type(state.Idle):", type(state.Idle))

current_state = state.Idle
print("current_state:", current_state)
if current_state == state.Idle:
    print(" Idle state")
if current_state != state.Triggered:
    print(" Not a triggered state")
    current_state = state.Idle
print("current_state:", current_state)
print("state.key_from_value(current_state):", state.key_from_value(current_state))

state2 = eval(str(state))
print(state2)
print("state == state2:", state == state2)

del state.Triggered
print(state)
print("state == state2:", state == state2)

print("state.keys():", state.keys())
print("state.values():", state.values())
print("state.items():", state.items())

try:
    del state.stop
except Exception as e:
    print("Exception:", e)

assert current_state == state.Idle
assert current_state != state.Disabled
assert state.Idle != state.Disabled
print(
    "State(State.Ready):",
    State(State.Ready),
    "type(State.Ready):",
    type(State(State.Ready)),
    "type(State.Ready):",
    type(State.Ready),
)
assert int(str(State(State.Ready))) == State.Ready
assert int(str(State(State.Ready))) != State.Disabled
print("will raise exception")
del state.Triggered
