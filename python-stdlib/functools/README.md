# functools

In CPython, `@functools.lru_cache` would also record the *order* of the keyword
arguments as they are passed to the function to cache the output for.  So, a
function called with `(a=1, b=2)` and called with `(b=2, a=1)` will take up two
entries in the LRU cache even though they are virtually the same function
invocation.

MicroPython, however, seems to pre-sort keyword arguments.  This means the
keyword arguments order is lost, and therefore the behaviour of
`@functools.lru_cache` differs slightly between the two implementations.
