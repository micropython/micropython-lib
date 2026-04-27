# enum.py
# version="1.2.6"


class EnumValue:
    # An immutable object representing a specific enum member
    def __init__(self, v, n):
        object.__setattr__(self, "value", v)
        object.__setattr__(self, "name", n)

    def __repr__(self):
        return f"{self.name}: {self.value}"

    def __call__(self):
        return self.value

    def __setattr__(self, k, v):
        raise AttributeError("EnumValue is immutable")

    # Helper function to extract the raw value
    def _get_value(self, o):
        return o.value if isinstance(o, EnumValue) else o

    # Arithmetic and Bitwise operations (Forward)
    def __add__(self, o):
        return self.value + self._get_value(o)

    def __sub__(self, o):
        return self.value - self._get_value(o)

    def __mul__(self, o):
        return self.value * self._get_value(o)

    def __truediv__(self, o):
        return self.value / self._get_value(o)

    def __floordiv__(self, o):
        return self.value // self._get_value(o)

    def __mod__(self, o):
        return self.value % self._get_value(o)

    def __pow__(self, o):
        return self.value ** self._get_value(o)

    def __and__(self, o):
        return self.value & self._get_value(o)

    def __or__(self, o):
        return self.value | self._get_value(o)

    def __xor__(self, o):
        return self.value ^ self._get_value(o)

    def __lshift__(self, o):
        return self.value << self._get_value(o)

    def __rshift__(self, o):
        return self.value >> self._get_value(o)

    # Arithmetic and Bitwise operations (Reflected)
    def __radd__(self, o):
        return self._get_value(o) + self.value

    def __rsub__(self, o):
        return self._get_value(o) - self.value

    def __rmul__(self, o):
        return self._get_value(o) * self.value

    def __rtruediv__(self, o):
        return self._get_value(o) / self.value

    def __rfloordiv__(self, o):
        return self._get_value(o) // self.value

    def __rand__(self, o):
        return self._get_value(o) & self.value

    def __ror__(self, o):
        return self._get_value(o) | self.value

    def __rxor__(self, o):
        return self._get_value(o) ^ self.value

    def __rlshift__(self, o):
        return self._get_value(o) << self.value

    def __rrshift__(self, o):
        return self._get_value(o) >> self.value

    # Unary operators
    def __neg__(self):
        return -self.value

    def __pos__(self):
        return +self.value

    def __abs__(self):
        return abs(self.value)

    def __invert__(self):
        return ~self.value

    # Comparison
    def __eq__(self, o):
        return self.value == self._get_value(o)

    def __lt__(self, o):
        return self.value < self._get_value(o)

    def __le__(self, o):
        return self.value <= self._get_value(o)

    def __gt__(self, o):
        return self.value > self._get_value(o)

    def __ge__(self, o):
        return self.value >= self._get_value(o)

    def __ne__(self, o):
        return self.value != self._get_value(o)


class Enum:
    def __new__(cls, name=None, names=None):
        # If a name and names are provided, create a NEW subclass of Enum
        if name and names:
            # Support Functional API: Enum("Name", {"KEY": VALUE})
            # Dynamically create: class <name>
            new_cls = type(name, (cls,), {})
            for k, v in names.items():
                new_cls._up(k, v)
            new_cls._inited = True
            return super().__new__(new_cls)

        # Reverse lookup by value or name (e.g., Color(1) or Color("RED"))
        if name and not names and cls is not Enum:
            return cls._lookup(name)

        return super().__new__(cls)

    def __init__(self, name=None, names=None):
        if "_inited" not in self.__class__.__dict__:
            self._scan()

    @classmethod
    def _lookup(cls, v):
        if "_inited" not in cls.__dict__:
            cls._scan()

        # Finds an EnumValue by its raw value or name
        for k in dir(cls):
            a = getattr(cls, k)
            if isinstance(a, EnumValue) and (a.value == v or a.name == v):
                return a
        raise AttributeError(f"{v} is not in {cls.__name__}")

    @classmethod
    def __iter__(cls):
        if "_inited" not in cls.__dict__:
            cls._scan()

        for k in dir(cls):
            attr = getattr(cls, k)
            if isinstance(attr, EnumValue):
                yield attr

    @classmethod
    def list(cls):
        if "_inited" not in cls.__dict__:
            cls._scan()

        # Returns a list of all members
        return [getattr(cls, k) for k in dir(cls) if isinstance(getattr(cls, k), EnumValue)]

    @classmethod
    def _up(cls, k, v):
        setattr(cls, k, EnumValue(v, k))

    @classmethod
    def _scan(cls):
        # Convert class-level attributes (constants) to EnumValue objects
        for k, v in list(cls.__dict__.items()):
            if not k.startswith("_") and not callable(v) and not isinstance(v, EnumValue):
                cls._up(k, v)
        cls._inited = True

    def is_value(self, v):
        return any(m.value == v for m in self)

    def __repr__(self):
        # Supports the condition: obj == eval(repr(obj))
        d = {m.name: m.value for m in self}
        # Return a string like: Enum(name='Name', names={'KEY1': VALUE1, 'KEY2': VALUE2, ..})
        return f"Enum(name='{self.__class__.__name__}', names={d})"

    def __call__(self, v):
        if "_inited" in self.__class__.__dict__:
            self._scan()

        return self._lookup(v)

    def __setattr__(self, k, v):
        if "_inited" in self.__class__.__dict__:
            raise AttributeError(f"Enum '{self.__class__.__name__}' is immutable")
        super().__setattr__(k, v)

    def __delattr__(self, k):
        raise AttributeError("Enum is immutable")

    def __len__(self):
        return sum(1 for _ in self)

    def __eq__(self, o):
        if not isinstance(o, Enum):
            return False
        return self.list() == o.list()


if __name__ == "__main__":
    # --- Usage Example 1 ---
    # Standard Class Definition
    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    print("Color.list():", Color.list())

    # Iteration
    print("Members list:", [member for member in Color()])
    print("Names list:", [member.name for member in Color()])
    print("Values list:", [member.value for member in Color()])

    # Create instance
    c = Color()
    print(f"Enum c: {c}")

    # Basic access
    print(f"RED: Name={c.RED.name}, Value={c.RED.value}, EnumValue={c.RED}, Call={c.RED()} ")

    # Assertions
    assert c.RED.name == "RED"
    assert c.RED.value == 1
    assert c.RED == 1
    assert c.RED() == 1

    # Reverse Lookup via instance call
    print(f"c(1) lookup object: {c(1)}, name={c(1).name}, value={c(1).value}")  # RED
    assert c(1).name == "RED"
    assert c(1).value == 1
    assert c(1) == 1

    try:
        c(999)
    except AttributeError as e:
        print(f"\nAttributeError: {e}: {c}\n")

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
    assert status == received_byte
    assert status == Status.RUNNING
    assert status.name == "RUNNING"
    assert status.value == received_byte

    # Test: Comparisons
    print(f"Comparison check: {status} == 1 is {status == 1}")
    assert status == 1
    assert status != 0

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
    print("--- Functional API and Eval Check ---")

    # Verify that eval(repr(obj)) restores the object
    c_repr = repr(c)
    c_restored = eval(c_repr)
    print(f"Original: {c_repr}")
    print(f"Restored: {repr(c_restored)}")
    print(f"Objects are equal: {c == c_restored}")
    assert c == c_restored

    # Direct creation using the Enum base class
    state = eval("Enum(name='State', names={'ON':1, 'OFF':2})")
    print(f"Functional Enum instance (state): {state}")
    print(type(state))
    assert state.ON == 1
    assert state.ON.name == "ON"

    # --- 1. Unique Data Types & Class Methods ---
    # Enums can hold more than just integers; here we use strings and add a method.
    class HttpMethod(Enum):
        GET = "GET"
        POST = "POST"
        DELETE = "DELETE"

        def is_safe(self):
            # Demonstrates that custom logic can coexist with Enum members
            return self.list()[0] == self.GET  # Simplistic example check

    api_call = HttpMethod()
    print(f"Member with string value: {api_call.GET}")
    assert api_call.GET == "GET"

    # --- 2. Advanced Reverse Lookup Scenarios ---
    # Demonstrates lookup by both name string and raw value string.
    print(f"Lookup by value 'POST': {api_call('POST')}")
    print(f"Lookup by name 'DELETE': {api_call('DELETE')}")
    assert api_call("GET").name == "GET"

    # --- 3. Empty Enum Handling ---
    # Verifies behavior when no members are defined.
    class Empty(Enum):
        pass

    empty_inst = Empty()
    print(f"Empty Enum list: {empty_inst.list()}")
    assert len(empty_inst) == 0

    # --- 4. Deep Functional API & Serialization ---
    # Testing complex name strings and verifying the 'eval' round-trip for functional enums.
    complex_enum = Enum(name='Config', names={'MAX_RETRY': 5, 'TIMEOUT_SEC': 30})

    # Verify serialization maintains the dynamic class name
    repr_str = repr(complex_enum)
    restored = eval(repr_str)

    print(f"Restored Functional Enum: {restored}")
    assert restored.MAX_RETRY == 5
    assert type(restored).__name__ == 'Config'

    # --- 5. Immutability & Integrity Guard ---
    # Ensuring the Enum structure cannot be tampered with after creation.
    try:
        api_call.NEW_METHOD = "PATCH"
    except AttributeError as e:
        print(f"Caught expected mutation error: {e}")

    try:
        del api_call.GET
    except AttributeError as e:
        print(f"Caught expected deletion error: {e}")

    print("\nAll tests passed successfully!")
