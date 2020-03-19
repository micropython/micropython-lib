uasyncio
========

uasyncio is MicroPython's asynchronous sheduling library, roughly
modeled after CPython's asyncio.

uasyncio doesn't use naive always-iterating scheduling algorithm,
but performs a real time-based scheduling, which allows it (and
thus the whole system) to sleep when there is nothing to do (actual
implementation of that depends on I/O scheduling algorithm which
actually performs the wait operation).

Major conceptual differences to asyncio:

* Avoids defining a notion of Future, and especially wrapping coroutines
  in Futures, like CPython asyncio does. uasyncio works directly with
  coroutines (and callbacks).
* Methods provided are more consistently coroutines.
* uasyncio uses wrap-around millisecond timebase (as native to all
  MicroPython ports.)
* Instead of single large package, number of subpackages are provided
  (each installable separately).

Specific differences:

* For millisecond scheduling, ``loop.call_later_ms()`` and
  ``uasyncio.sleep_ms()`` are provided.
* As there's no monotonic time, ``loop.call_at()`` is not provided.
  Instead, there's ``loop.call_at_()`` which is considered an internal
  function and has slightly different signature.
* ``call_*`` funcions don't return Handle and callbacks scheduled by
  them aren't cancellable. If they need to be cancellable, they should
  accept an object as an argument, and a "cancel" flag should be set
  in the object, for a callback to test.
* ``Future`` object is not available.
* ``ensure_future()`` and ``Task()`` perform just scheduling operations
  and return a native coroutine, not Future/Task objects.
* Some other functions are not (yet) implemented.
* StreamWriter method(s) are coroutines. While in CPython asyncio,
  StreamWriter.write() is a normal function (which potentially buffers
  unlimited amount of data), uasyncio offers coroutine StreamWriter.awrite()
  instead. Also, both StreamReader and StreamWriter have .aclose()
  coroutine method.
