# This doesn't quite test everything but just serves to verify that basic syntax works,
# which for MicroPython means everything typing-related should be ignored.

from typing import *

MyAlias = str
Vector = List[float]
Nested = Iterable[Tuple[int, ...]]
UserId = NewType("UserId", int)
T = TypeVar("T", int, float, complex)

hintedGlobal: Any = None


def func_with_hints(c: int, b: MyAlias, a: Union[int, None], lst: List[float] = [0.0]) -> Any:
    pass


class ClassWithHints(Generic[T]):

    a: int = 0

    def foo(self, other: int) -> None:
        pass
