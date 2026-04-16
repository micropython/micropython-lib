# enum.py
# version="1.1.0"

_Err = "no such attribute: "


class ValueWrapper:
    """Universal wrapper for accessing values via .value or calling ()"""
    __slots__ = ('_v', )

    def __init__(self, v):
        self._v = v

    @property
    def value(self):
        return self._v

    def __call__(self):
        return self._v

    def __repr__(self):
        return repr(self._v)

    def __str__(self):
        return str(self._v)

    # Type conversion
    def __int__(self):
        return int(self._v)

    def __float__(self):
        return float(self._v)

    def __index__(self):
        return int(self._v)

    def __bool__(self):
        return bool(self._v)

    # Helper function to extract the raw value
    def _get_v(self, other):
        return other._v if isinstance(other, ValueWrapper) else other

    # Arithmetic and Bitwise operations (Forward)
    def __add__(self, other):
        return self._v + self._get_v(other)

    def __sub__(self, other):
        return self._v - self._get_v(other)

    def __mul__(self, other):
        return self._v * self._get_v(other)

    def __truediv__(self, other):
        return self._v / self._get_v(other)

    def __floordiv__(self, other):
        return self._v // self._get_v(other)

    def __mod__(self, other):
        return self._v % self._get_v(other)

    def __pow__(self, other):
        return self._v**self._get_v(other)

    def __and__(self, other):
        return self._v & self._get_v(other)

    def __or__(self, other):
        return self._v | self._get_v(other)

    def __xor__(self, other):
        return self._v ^ self._get_v(other)

    def __lshift__(self, other):
        return self._v << self._get_v(other)

    def __rshift__(self, other):
        return self._v >> self._get_v(other)

    # Arithmetic and Bitwise operations (Reflected)
    def __radd__(self, other):
        return self._get_v(other) + self._v

    def __rsub__(self, other):
        return self._get_v(other) - self._v

    def __rmul__(self, other):
        return self._get_v(other) * self._v

    def __rtruediv__(self, other):
        return self._get_v(other) / self._v

    def __rfloordiv__(self, other):
        return self._get_v(other) // self._v

    def __rand__(self, other):
        return self._get_v(other) & self._v

    def __ror__(self, other):
        return self._get_v(other) | self._v

    def __rxor__(self, other):
        return self._get_v(other) ^ self._v

    def __rlshift__(self, other):
        return self._get_v(other) << self._v

    def __rrshift__(self, other):
        return self._get_v(other) >> self._v

    # Unary operators
    def __neg__(self):
        return -self._v

    def __pos__(self):
        return +self._v

    def __abs__(self):
        return abs(self._v)

    def __invert__(self):
        return ~self._v

    # Comparison
    def __eq__(self, other):
        return self._v == self._get_v(other)

    def __lt__(self, other):
        return self._v < self._get_v(other)

    def __le__(self, other):
        return self._v <= self._get_v(other)

    def __gt__(self, other):
        return self._v > self._get_v(other)

    def __ge__(self, other):
        return self._v >= self._get_v(other)

    def __ne__(self, other):
        return self._v != self._get_v(other)


def enum(**kw_args):  # `**kw_args` kept backwards compatible as in the Internet examples
    return Enum(kw_args)


class Enum(dict):
    def __init__(self, arg=None, **kwargs):
        super().__init__()
        # Use __dict__ directly for internal flags
        # to avoid cluttering the dictionary keyspace
        super().__setattr__('_is_loading', True)

        # 1. Collect class-level attributes (constants)
        self._scan_class_attrs()
        # 2. Add arguments from the constructor
        if arg: self.append(arg)
        if kwargs: self.append(kwargs)

        super().__setattr__('_is_loading', False)

    def _scan_class_attrs(self):
        cls = self.__class__
        # Define attributes to skip (internal or explicitly requested)
        skipped = getattr(cls, '__skipped__', ())

        for key in dir(cls):
            # Skip internal names, methods, and excluded attributes
            if key.startswith('_') or key in ('append', 'is_value', 'key_from_value'):
                continue
            if key in skipped:
                continue

            val = getattr(cls, key)
            # Only wrap non-callable attributes (constants)
            if not callable(val):
                self[key] = ValueWrapper(val)

    def append(self, arg=None, **kwargs):
        if isinstance(arg, dict):
            for k, v in arg.items():
                self[k] = ValueWrapper(v)
        else:
            self._arg = arg  # for __str__()
        if kwargs:
            for k, v in kwargs.items():
                self[k] = ValueWrapper(v)
        return self

    def __getattr__(self, key):
        if key in self:
            return self[key]
        raise AttributeError(_Err + key)

    def __setattr__(self, key, value):
        if self._is_loading or key.startswith('_'):
            # Record directly into memory as a regular variable
            super().__setattr__(key, value)
        else:
            # Handle as an Enum element (wrap in ValueWrapper)
            self[key] = ValueWrapper(value)

    def is_value(self, value):
        return any(v._v == value for v in self.values())

    def key_from_value(self, value):
        for k, v in self.items():
            if v._v == value: return f"{self.__class__.__name__}.{k}"
        raise ValueError(_Err + str(value))

    def __dir__(self):
        # 1. Dictionary keys (your data: X1, X2, etc.)
        data_keys = list(self.keys())
        # 2. Class attributes (your methods: append, is_value, etc.)
        class_stuff = list(dir(self.__class__))
        # 3. Parent class attributes (for completeness)
        parent_attrs = list(dir(super()))
        # Combine and remove duplicates using set for clarity
        #return list(set(data_keys + class_stuff + parent_attrs))
        return list(set(data_keys + class_stuff))

    def __call__(self, value):
        if self.is_value(value):
            return value
        raise ValueError(_Err + f"{value}")


if __name__ == "__main__":
    # --- Usage Examples ---

    # 1. GPIO and Hardware Configuration
    class Pins(Enum):
        LED = 2
        BUTTON = 4
        __skipped__ = ('RESERVED_PIN', )
        RESERVED_PIN = 0

    pins = Pins(SDA=21, SCL=22)
    print(f"I2C SDA Pin: {pins.SDA}")
    print(f"Is 21 a valid pin? {pins.is_value(21)}")

    # 2. Math and Logic
    brightness = Enum(MIN=0, STEP=25, MAX=255)
    print(f"Next level: {brightness.MIN + brightness.STEP // 2}")
    print(f"Calculation: {brightness.MIN + 2 * brightness.STEP}")

    # Direct arithmetic without .value
    print(f"Complex math: {100 + brightness.STEP}")

    # 3. State Machine (Dynamic Expansion)
    status = Enum(IDLE=0, CONNECTING=1)
    status.append(CONNECTED=2, ERROR=3)
    status.DISCONNECTING = 4

    for name, val in status.items():
        print(f"Status {name} has code {val}")

    # 4. Working with different types
    commands = Enum(START="CMD_START", STOP="CMD_STOP", REBOOT_CODE=0xDEADBEEF, IS_ACTIVE=True)

    if commands.IS_ACTIVE:
        print(f"Running command: {commands.START}")

    # 5. Class Config and dir()
    class WebConfig(Enum):
        PORT = 80
        TIMEOUT = 5.0

    config = WebConfig({'IP': '192.168.1.1'})
    print(f"Available keys in config: {list(config.keys())}")
