# enum_mini.py
# Minimalist Enum implementation without metaclasses
# version="1.5.0"

# ==============================================================================
# Variable & Abbreviation Definitions:
# ==============================================================================
# Functions & Helper Methods:
#   _c(e, n, v) -> create_enum_item: Helper function to construct a typed enum instance.
#   _i()        -> items: Classmethod to lazily initialize and return the __members__ dict.
#   a(s, k, v)  -> __setattr__: Inner setter guard raising AttributeError on enum items.
#
# Helper Arguments & Local Variables:
#   e       - enum_name / enum_item: Class name string or instance of an enum item.
#   n       - name: String representing the enum member key (e.g., "RED").
#   v       - value / member value: Value assigned to, searched within, or passed to lookup.
#   c       - class / new_class: Dynamically created Enum subclass via `type()`.
#   t       - value_type: Target constraint type (`int`, `str`, or `None` for generic Enum).
#   l       - names_list: List of parsed string keys from comma/space-separated inputs.
#   d       - dict / mapping: Temporary dictionary for parsed enum members.
#   k, v    - key, value: Key-value pair during iteration over attributes or dictionaries.
#   i       - item: Individual enum member instance during iteration.
#   __members__ - Dictionary mapping enum member instances to their raw values.
#   s, k, o - self, key/attribute_name, other_enum (standard short parameters).
#   f       - function: The body function of the class being defined.
#   b       - bases: Tuple of base classes passed during class creation.
#   kw      - kwargs: Additional keyword arguments passed during class creation.
#   cls     - class object: Target class being created or initialized.
# ==============================================================================


def _c(e, n, v):
    # Inner guard to prevent modification of enum item attributes
    def a(s, k, v):
        raise AttributeError("readonly")

    # Safely extract class name string if a class or object was passed
    e = getattr(e, "__name__", str(e))

    # Create dynamic subclass inheriting the value's type (int, str, float etc.)
    return type(
        f"{e}.{n}",
        (type(v),),
        {
            "name": n,
            "value": v,
            "__str__": lambda s: f"{e}.{n}",
            "__repr__": lambda s: f"<{e}.{n}: {v!r}>",
            "__call__": lambda s: v,
            "__setattr__": a,
        },
    )(v)


class Enum:
    def __new__(cls, value=None, names=None):
        # Functional API: Enum('Name', {'KEY': 'val'})
        if value is not None and names is not None:
            if not isinstance(names, dict):
                raise TypeError("must be dict")

            # Construct and return a new Enum subclass
            c = type(str(value), (cls,), {})
            for k, v in names.items():
                setattr(c, k, v)
            c._i()
            return c

        if cls is not Enum:
            # Lazy initialization of subclass members
            cls._i()

            # Lookup existing member by value or name: e.g., Color(1) or Color("RED")
            if value is not None:
                return cls()(value)

        return super().__new__(cls)

    @classmethod
    def __contains__(cls, v):
        # Lookup member by value or name
        for i in cls._i():
            if i.value == v or i.name == v:
                return True
        return False

    @classmethod
    def __call__(cls, v=None):
        if v is None:
            return cls()

        # Lookup member by value or name
        for i in cls._i():
            if i.value == v or i.name == v:
                return i
        raise ValueError(f"invalid: {v!r}")

    # Equality checks if both classes are Enums and have identical __members__ dicts
    __eq__ = classmethod(lambda cls, o: getattr(o, "_i", False) and cls._i() == o._i())
    # Iteration yields enum member instances (keys of __members__)
    __iter__ = classmethod(lambda cls: iter(cls._i()))
    __len__ = classmethod(lambda cls: len(cls._i()))

    @classmethod
    def __setattr__(cls, k, v):
        raise AttributeError("readonly")

    @classmethod
    def __delattr__(cls, k):
        raise AttributeError("readonly")

    @classmethod
    def _i(cls):
        # Initialize and return dictionary mapping enum member instances to their values
        if "__members__" not in cls.__dict__:
            # Convert raw class attributes into typed enum instances
            cls.__members__ = {}
            for k, v in list(cls.__dict__.items()):
                if not k.startswith("_") and not callable(v):
                    if isinstance(v, cls):
                        continue
                    if v in cls.__members__:
                        raise ValueError(f"duplicate value {v!r} in {cls.__name__}")
                    e = _c(cls.__name__, k, v)
                    setattr(cls, k, e)
                    cls.__members__[e] = v
        return cls.__members__


def _finish_class(cls, bases):
    return cls()


# Share one dispatcher across full/mini and fresh imports. Retain old families
# for aliases still in use, and never replace a later cooperative wrapper.
import builtins


def _register_enum(base, finish):
    try:
        state = __ENUM_STATE__
    except NameError:
        state = None
    if state is None:
        # Read the effective builtin: MicroPython's module attribute may still
        # expose the original builtin after a cooperative override is installed.
        state = {"original": __build_class__, "families": []}

        def dispatch(body, name, *bases, **keywords):
            cls = state["original"](body, name, *bases, **keywords)
            for family, finalizer in state["families"]:
                if any(isinstance(parent, type) and issubclass(parent, family) for parent in bases):
                    return finalizer(cls, bases)
            return cls

        state["wrapper"] = dispatch
        builtins.__build_class__ = dispatch
        builtins.__ENUM_STATE__ = state
    elif "families" not in state:
        raise RuntimeError("incompatible enum builder state")
    state["families"].append((base, finish))


_register_enum(Enum, _finish_class)
