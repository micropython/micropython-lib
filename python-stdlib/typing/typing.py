def cast(type, val):
    return val


def get_origin(type):
    return None


def get_args(type):
    return ()


def no_type_check(arg):
    return arg


def overload(func):
    return None


class _AnyCall:
    def __init__(*args, **kwargs):
        pass

    def __call__(*args, **kwargs):
        pass


_anyCall = _AnyCall()


class _SubscriptableType:
    def __getitem__(self, arg):
        return _anyCall


_Subscriptable = _SubscriptableType()


def TypeVar(type, *types):
    return None


def NewType(name, type):
    return type


class Any:
    pass


class BinaryIO:
    pass


class ClassVar:
    pass


class Final:
    pass


class Hashable:
    pass


class IO:
    pass


class NoReturn:
    pass


class Sized:
    pass


class SupportsInt:
    pass


class SupportsFloat:
    pass


class SupportsComplex:
    pass


class SupportsBytes:
    pass


class SupportsIndex:
    pass


class SupportsAbs:
    pass


class SupportsRound:
    pass


class TextIO:
    pass


AnyStr = str
Text = str
Pattern = str
Match = str
TypedDict = dict

AbstractSet = _Subscriptable
AsyncContextManager = _Subscriptable
AsyncGenerator = _Subscriptable
AsyncIterable = _Subscriptable
AsyncIterator = _Subscriptable
Awaitable = _Subscriptable
Callable = _Subscriptable
ChainMap = _Subscriptable
Collection = _Subscriptable
Container = _Subscriptable
ContextManager = _Subscriptable
Coroutine = _Subscriptable
Counter = _Subscriptable
DefaultDict = _Subscriptable
Deque = _Subscriptable
Dict = _Subscriptable
FrozenSet = _Subscriptable
Generator = _Subscriptable
Generic = _Subscriptable
Iterable = _Subscriptable
Iterator = _Subscriptable
List = _Subscriptable
Literal = _Subscriptable
Mapping = _Subscriptable
MutableMapping = _Subscriptable
MutableSequence = _Subscriptable
MutableSet = _Subscriptable
NamedTuple = _Subscriptable
Optional = _Subscriptable
OrderedDict = _Subscriptable
Sequence = _Subscriptable
Set = _Subscriptable
Tuple = _Subscriptable
Type = _Subscriptable
Union = _Subscriptable

TYPE_CHECKING = False
