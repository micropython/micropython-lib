# enum.py
# version="1.3.0"


def _make_enum(v, n, e):
    T = type(v)

    def _setattr(self, k, v):
        raise AttributeError("EnumValue is immutable")

    # Create class: type(name, bases, dict), which inherits a base type (int, str, etc.)
    return type(
        "EnumValue",
        (T,),
        {
            "name": n,
            "value": property(lambda s: v),
            "__repr__": lambda s: f"{e}.{n}: {v}",
            "__str__": lambda s: f"{e}.{n}: {v}",
            "__call__": lambda s: v,
            "__setattr__": _setattr,
        },
    )(v)


class Enum:
    def __new__(cls, name=None, names=None):
        # If a name and names are provided, create a NEW subclass of Enum
        if name and names:
            # Support Functional API: Enum("Name", {"KEY1": VALUE1, "KEY2": VALUE2, ..})
            # Dynamically create: class <name>
            new_cls = type(name, (cls,), {"_inited": True})
            for k, v in names.items():
                setattr(new_cls, k, _make_enum(v, k, name))
            return super().__new__(new_cls)

        # Reverse lookup by value or name (e.g., Color(1) or Color("RED"))
        if name and cls is not Enum:
            return cls._lookup(name)

        return super().__new__(cls)

    def __init__(self, name=None, names=None):
        if "_inited" not in self.__class__.__dict__:
            self.list()

    @classmethod
    def _lookup(cls, v):
        for m in cls.list():
            if m.value == v or m.name == v:
                return m
        raise AttributeError(f"{v} is not in {cls.__name__}")

    @classmethod
    def __iter__(cls):
        return iter(cls.list())

    @classmethod
    def list(cls):
        if "_inited" not in cls.__dict__:
            # Copy dict.items() to avoid RuntimeError when changing the dictionary
            for k, v in list(cls.__dict__.items()):
                if not k.startswith("_") and not callable(v):
                    setattr(cls, k, _make_enum(v, k, cls.__name__))
            cls._inited = True
        return [
            m for k in dir(cls) if not k.startswith("_") and hasattr(m := getattr(cls, k), "name")
        ]

    @classmethod
    def is_value(cls, v):
        return any(m.value == v or m.name == v for m in cls.list())

    def __repr__(self):
        # Supports the condition: obj == eval(repr(obj))
        d = {m.name: m.value for m in self.__class__.list()}
        # Return a string like: Enum(name='Name', names={'KEY1': VALUE1, 'KEY2': VALUE2, ..})
        return f"Enum(name='{self.__class__.__name__}', names={d})"

    def __call__(self, v):
        return self._lookup(v)

    def __setattr__(self, k, v):
        if "_inited" in self.__class__.__dict__:
            raise AttributeError(f"Enum '{self.__class__.__name__}' is immutable")
        super().__setattr__(k, v)

    def __delattr__(self, k):
        raise AttributeError("Enum is immutable")

    @classmethod
    def __len__(cls):
        return len(cls.list())

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

    # Basic access
    print(f"RED: repr={repr(Color.RED)}, type={type(Color.RED)}, {Color(1).name} ")
    print(f"RED: name={Color.RED.name}, value={Color.RED.value}, str={str(Color.RED)}, call={Color.RED()} ")
    assert Color(1).value == 1 
    assert Color.BLUE.value >= Color.GREEN.value

    print("Color.list():", Color.list())

    # Iteration
    print("Members list:", [member for member in Color()])
    print("Names list:", [member.name for member in Color()])
    print("Values list:", [member.value for member in Color()])
    print()

    # Create instance
    c = Color()
    print(f"Enum c: {c}")

    # Basic access
    print(f"RED: name={c.RED.name}, value={c.RED.value}, str={str(c.RED)}, call={c.RED()} ")

    # Assertions
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

    try:
        c(999)
        0 / 0
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
    print(Status.__len__())
    print(len(Status()))
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
        0 / 0
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
        0 / 0
    except AttributeError as e:
        print(f"\nAttributeError: Invalid lookup check: Caught expected error -> {e}\n")

    # --- Example 3: Functional API and serialization ---
    print("--- Functional API and Eval Check ---")

    # Verify that eval(repr(obj)) restores the object
    c_repr = repr(c)
    print(f"Original: {c_repr}")
    c_restored = eval(c_repr)
    print(f"Restored: {repr(c_restored)}")
    print(f"Objects are equal: {c == c_restored}")
    assert c == c_restored

    # Direct creation using the Enum base class
    state = eval("Enum(name='State', names={'ON':1, 'OFF':2})")
    print(f"Functional Enum instance (state): {state}")
    print(type(state))
    assert state.ON == 1
    assert state.ON.name == "ON"
    assert state.ON > 0
    assert state.ON.value | state.OFF.value == 3

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
        0 / 0
    except AttributeError as e:
        print(f"Caught expected mutation error: {e}")

    try:
        del api_call.GET
        0 / 0
    except AttributeError as e:
        print(f"Caught expected deletion error: {e}")

    print("\nAll tests passed successfully!")
