# enum.py
# version="1.2.2"


class EnumValue:
    # An immutable object representing a specific enum member
    def __init__(self, value, name):
        object.__setattr__(self, 'value', value)
        object.__setattr__(self, 'name', name)

    def __repr__(self):
        return f"<{self.name}: {self.value}>"

    def __str__(self):
        return str(self.value)

    def __call__(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, EnumValue):
            return self.value == other.value
        return self.value == other

    def __int__(self):
        return self.value

    def __setattr__(self, key, value):
        raise AttributeError("EnumValue is immutable")


class Enum:
    def __new__(cls, *args, **kwargs):
        # Scenario 1: Reverse lookup by value (e.g., Status(1))
        if len(args) == 1:
            if cls is not Enum:
                return cls._lookup(args[0])
            return super(Enum, cls).__new__(cls)

        # Scenario 2: Restriction on multiple positional arguments
        elif len(args) > 1:
            raise TypeError(f"{cls.__name__}() takes at most 1 positional argument ({len(args)} given)")

        # Scenario 3: Creating an instance (e.g. Color() або Color(BLUE=3))
        return super(Enum, cls).__new__(cls)

    def __init__(self, **kwargs):
        # 1. Convert class-level attributes (constants) to EnumValue objects
        self._scan_class_attrs()
        # 2. Add dynamic arguments from constructor
        if kwargs:
            self.append(**kwargs)

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
                return attr

        raise AttributeError(f"{value} is not in {cls.__name__} enum")

    def list_members(self):
        # Returns a list of tuples (name, value) for all members
        return [(m.name, m.value) for m in self]

    def _update(self, key, value):
        setattr(self.__class__, key, EnumValue(value, key))

    def _scan_class_attrs(self):
        # Converts static class attributes into EnumValue objects
        # List of methods and internal names that should not be converted
        ignored = ('append', 'is_value', 'list_members')
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

    def append(self, **kwargs):
        # Adds new members dynamically.
        for key, value in kwargs.items():
            if hasattr(self, key):
                raise AttributeError(f"Enum key '{key}' is immutable")
            self._update(key, value)

    def __repr__(self):
        members = [f"{m.name}={m.value}" for m in self]
        # Return a string like: Color(RED=1, GREEN=2, BLUE=3)
        return f"{self.__class__.__name__}({', '.join(members)})"

    def __call__(self, value):
        for member in self:
            if member.value == value:
                return member
        raise ValueError(f"no such value: {value}")

    def __setattr__(self, key, value):
        if hasattr(self, key) and isinstance(getattr(self, key), EnumValue):
            raise AttributeError(f"Enum member '{key}' is immutable")
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


def enum(**kwargs):  # `**kwargs` kept backwards compatible as in the Internet examples
    return Enum(**kwargs)


if __name__ == '__main__':
    # --- Usage Example 1 ---
    # 1. Creation via class
    class Color(Enum):
        RED = 1
        GREEN = 2

    # 2. Create instance
    c = Color()
    print(f"Enum repr c: {c}")

    # 3. Dynamic addition
    c.append(BLUE=3)
    print(f"c after append: {c}")

    print('dir(c):', dir(c))

    # 4. Immutability and name protection check
    try:
        c.append(append=True)
    except AttributeError as e:
        print(f"\nAttributeError: Reserved name protection: {e}\n")

    # 5. Basic access
    print(f"RED: Name={c.RED.name}, Value={c.RED.value}, EnumValue={c.RED}, Call={c.RED()} ")

    # 6. Assertions
    assert c.RED == 1
    assert c.RED.value == 1
    assert c.RED.name == 'RED'

    # 7. Reverse lookup
    print(f"c(1) lookup object: {c(1)}, Name={c(1).name}")  # RED
    assert c(1).name == 'RED'
    assert c(1) == 1

    # 8. Iteration
    print("Values list:", [member.value for member in c])
    print("Names list:", [member.name for member in c])

    try:
        c(7)
    except ValueError as e:
        print(f"\nValueError: {c} {e}\n")

    # --- Usage Example 2 ---
    # 1. Define an Enum class
    class Status(Enum):
        IDLE = 0
        RUNNING = 1
        ERROR = 2

    # 2. Test: Reverse Lookup
    # This simulates receiving a byte from the  hardware
    received_byte = 1
    status = Status(received_byte)
    print(f"Lookup check: Received {received_byte} -> {status!r}")
    assert status == Status.RUNNING
    assert status.name == "RUNNING"

    # 3. Test: Comparisons
    print(f"Comparison check: {status} == 1 is {status == 1}")
    assert status == 1
    assert status != 0
    assert status == Status.RUNNING

    # 4. Test: Immutability
    try:
        Status.RUNNING.value = 99
    except AttributeError as e:
        print(f"\nImmutability check: Passed (Cannot modify EnumValue): {e}\n")

    # 5. Test: Dynamic Append
    powers = Enum()
    powers.append(LOW=10, HIGH=100)
    print(f"Dynamic Enum check: {powers}")
    assert powers.LOW == 10

    # 6. Test: Iteration
    print("Iteration check: ", end="")
    for m in Status():
        print(f"{m.name}, ", end="")
    print("-> Passed")

    # 7. Test: Error handling for invalid lookup
    try:
        Status(99)
    except AttributeError as e:
        print(f"\nAttributeError: Invalid lookup check: Caught expected error -> {e}\n")

    print("\nAll tests passed successfully!")
