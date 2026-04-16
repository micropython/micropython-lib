# enum.py
# version="1.2.1"


class EnumValue:
    def __init__(self, value, name):
        object.__setattr__(self, 'value', value)
        object.__setattr__(self, 'name', name)

    def __repr__(self):
        return str(self.value)

    def __call__(self):
        return self.value

    def __eq__(self, other):
        return self.value == (other.value if isinstance(other, EnumValue) else other)

    def __setattr__(self, key, value):
        raise AttributeError("EnumValue is immutable")


class Enum:
    def __new__(cls, *args, **kwargs):
        if len(args) > 0:
            raise TypeError(f"{cls.__name__}() kwargs allowed only, not {args} args")
        return super(Enum, cls).__new__(cls)

    def __init__(self, **kwargs):
        # 1. Collect class-level attributes (constants)
        self._scan_class_attrs()
        # 2. Add arguments from the constructor
        if kwargs:
            self.append(**kwargs)

    def _update(self, key, value):
        setattr(self.__class__, key, EnumValue(value, key))

    def _scan_class_attrs(self):
        # Converts static class attributes into EnumValue objects
        # List of methods and internal names that should not be converted
        ignored = ('is_value', 'append')

        for key in dir(self.__class__):
            # Skip internal names and methods
            if key.startswith('_') or key in ignored:
                continue

            value = getattr(self.__class__, key)
            # Convert only constants, not methods
            if not callable(value) and not isinstance(value, EnumValue):
                self._update(key, value)

    def is_value(self, value):
        # Оптимізація: ітеруємося по self (де вже є __iter__), а не через dir()
        return any(member.value == value for member in self)

    def append(self, **kwargs):
        forbidden = ('is_value', 'append', '_update', '_scan_class_attrs')
        for key, value in kwargs.items():
            if key in forbidden or key.startswith('_'):
                raise NameError(f"Cannot add enum member with reserved name: {key}")
            if hasattr(self.__class__, key):
                existing = getattr(self.__class__, key)
                if isinstance(existing, EnumValue):
                    raise AttributeError(f"Enum member '{key}' already exists and is immutable")
            self._update(key, value)
        return self

    def __repr__(self):
        # Implementation of the principle: obj == eval(repr(obj))
        # Use !r to correctly represent values ​​(e.g., quotes for strings)
        members = [f"{k}={getattr(self.__class__, k).value!r}" for k in dir(self.__class__) if not k.startswith('_') and isinstance(getattr(self.__class__, k), EnumValue)]
        # Return a string like: Color(RED=1, GREEN=2, BLUE=3)
        return f"{type(self).__name__}({', '.join(members)})"

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
    # --- Usage Example ---

    # 1. Creation via class
    class Color(Enum):
        RED = 1
        GREEN = 2

    # Create instance
    c = Color()
    print(f"Enum repr: {c}")

    # 2. Strict __init__ control check
    try:
        c_bad = Color('BLACK')
    except TypeError as e:
        print(f"\nTypeError: Strict Init Check: {e}\n")

    # 3. Dynamic addition
    c.append(BLUE=3)
    print(f"c after append: {c}")

    print('dir(c):', dir(c))

    # 4. Immutability and name protection check
    try:
        c.append(append=True)
    except NameError as e:
        print(f"\nNameError: Reserved name protection: {e}\n")

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
