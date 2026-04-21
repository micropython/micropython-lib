# enum.py
# version="1.2.3"


class EnumValue:
    # An immutable object representing a specific enum member
    def __init__(self, value, name):
        object.__setattr__(self, 'value', value)
        object.__setattr__(self, 'name', name)

    def __repr__(self):
        return f"{self.name}: {self.value}"

#     def __str__(self):
#         return str(self.value)

    def __call__(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, EnumValue):
            return self.value == other.value
        return self.value == other

#     def __int__(self):
#         return self.value

    def __setattr__(self, key, value):
        raise AttributeError("EnumValue is immutable")


class Enum:
    def __new__(cls, name=None, names=None):
        # Scenario 1: Reverse lookup by value (e.g., Status(1))
        if name is not None and names is None:
            if cls is not Enum:
                return cls._lookup(name)

        # Scenario 2: Functional API (e.g., Enum('Color', {'RED': 1}))
        return super(Enum, cls).__new__(cls)

    def __init__(self, name=None, names=None):
        # 1. Convert class-level attributes (constants) to EnumValue objects
        self._scan_class_attrs()

        # Support Functional API: Enum('Name', {'KEY': VALUE})
        if name is not None and isinstance(names, dict):
            for key, value in names.items():
                # Prevent addition if the key already exists
                if not hasattr(self, key):
                    self._update(key, value)

        object.__setattr__(self, '_initialized', True)

    @classmethod
    def _lookup(cls, value):
        # Finds an EnumValue by its raw value
        for key in dir(cls):
            if key.startswith('_'):
                continue
            attr = getattr(cls, key)
            if isinstance(attr, EnumValue) and (attr.value == value or attr.name == value):
                return attr
            if not callable(attr) and attr == value:
                # Wrap static numbers found in class definition
                return EnumValue(attr, key)

        raise AttributeError(f"{value} is not in {cls.__name__} enum")

    def list_members(self):
        # Returns a list of tuples (name, value) for all members
        return [(m.name, m.value) for m in self]

    def _update(self, key, value):
        setattr(self.__class__, key, EnumValue(value, key))

    def _scan_class_attrs(self):
        # Converts static class attributes into EnumValue objects
        # List of methods and internal names that should not be converted
        ignored = ('is_value', 'list_members')
        for key in dir(self.__class__):
            # Skip internal names and methods
            if key.startswith('_') or key in ignored:
                continue

            value = getattr(self.__class__, key)
            # Convert only constants, not methods
            if not callable(value) and not isinstance(value, EnumValue):
                self._update(key, value)

    def is_value(self, value):
        return any(member.value == value for member in self)

    def __repr__(self):
        # Supports the condition: obj == eval(repr(obj))
        members = {m.name: m.value for m in self}
        if self.__class__.__name__ == 'Enum':
            return f"Enum(name='Enum', names={members})"
        # Return a string like: Name(names={'KEY1': VALUE1, 'KEY2': VALUE2, ..})
        return f"{self.__class__.__name__}(names={members})"

    def __call__(self, value):
        for member in self:
            if member.value == value:
                return member
        raise ValueError(f"no such value: {value}")

    def __setattr__(self, key, value):
        if hasattr(self, '_initialized'):
            raise AttributeError(f"Enum '{self.__class__.__name__}' is static")
        super().__setattr__(key, value)

    def __delattr__(self, key):
        if hasattr(self, key) and isinstance(getattr(self, key), EnumValue):
            raise AttributeError("Enum members cannot be deleted")
        super().__delattr__(key)

    def __len__(self):
        return sum(1 for _ in self)

    def __iter__(self):
        for key in dir(self.__class__):
            attr = getattr(self.__class__, key)
            if isinstance(attr, EnumValue):
                yield attr

    def __eq__(self, other):
        if not isinstance(other, Enum):
            return False
        return self.list_members() == other.list_members()


if __name__ == '__main__':
    # --- Usage Example 1 ---
    # Standard Class Definition
    class Color(Enum):
        RED = 'red'
        GREEN = 'green'

    # Create instance
    c = Color()
    print(f"Enum repr c: {c}")

    # Basic access
    print(f"RED: Name={c.RED.name}, Value={c.RED.value}, EnumValue={c.RED}, Call={c.RED()} ")

    # Assertions
    assert c.RED.name == 'RED'
    assert c.RED.value == 'red'
    assert c.RED == 'red'
    assert c.RED() == 'red'

    # Reverse Lookup via instance call
    print(f"c('red') lookup object: {c('red')}, Name={c('red').name}, value={c('red').value}")  # RED
    assert c('red').name == 'RED'
    assert c('red').value == 'red'
    assert c('red') == 'red'

    # Iteration
    print("Values list:", [member.value for member in c])
    print("Names list:", [member.name for member in c])

    try:
        c(999)
    except ValueError as e:
        print(f"\nValueError: {c} {e}\n")

    # --- Usage Example 2 ---
    # Define an Enum class
    class Status(Enum):
        IDLE = 0
        RUNNING = 1
        ERROR = 2

    # 2. Test: Reverse Lookup
    # This simulates receiving a byte from the  hardware
    received_byte = 1
    status = Status(received_byte)
    print(f"Lookup check: Received {received_byte} -> {status}")
    assert status == Status.RUNNING
    assert status.name == "RUNNING"

    # Test: Comparisons
    print(f"Comparison check: {status} == 1 is {status == 1}")
    assert status == 1
    assert status != 0
    assert status == Status.RUNNING

    # Immutability Check
    try:
        Status.RUNNING.value = 999
    except AttributeError as e:
        print(f"\nImmutability check: Passed (Cannot modify EnumValue): {e}\n")

    # Test: Iteration
    print("Iteration check: ", end="")
    for m in Status():
        print(f"{m.name}, ", end="")
    print("-> Passed")

    # Test: Error handling for invalid lookup
    try:
        Status(999)
    except AttributeError as e:
        print(f"\nAttributeError: Invalid lookup check: Caught expected error -> {e}\n")

    # --- Example 3: Functional API and serialization ---
    print("\n--- Functional API and Eval Check ---")

    # Verify that eval(repr(obj)) restores the object
    c2 = eval(repr(c))
    print(f"Original: {repr(c)}")
    print(f"Restored: {repr(c2)}")
    print(f"Objects are equal: {c == c2}")
    assert c == c2

    # Direct creation using the Enum base class
    state = eval("Enum(name='State', names={'ON':1, 'OFF':2})")
    print(f"Functional Enum instance (state): {state}")
    assert state.ON == 1
    assert state.ON.name == 'ON'

    print("\nAll tests passed successfully!")
