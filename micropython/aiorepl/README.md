# aiorepl

This library provides "asyncio REPL", a simple REPL that can be used even
while your program is running, allowing you to inspect program state, create
tasks, and await asynchronous functions.

This is inspired by Python's `asyncio` module when run via `python -m asyncio`.

## Background

The MicroPython REPL is unavailable while your program is running. This
library runs a background REPL using the asyncio scheduler.

Furthermore, it is not possible to `await` at the main REPL because it does
not know about the asyncio scheduler.

## Usage

To use this library, you need to import the library and then start the REPL task.

For example, in main.py:

```py
import asyncio
import aiorepl

async def demo():
    await asyncio.sleep_ms(1000)
    print("async demo")

state = 20

async def task1():
    while state:
        #print("task 1")
        await asyncio.sleep_ms(500)
    print("done")

async def main():
    print("Starting tasks...")

    # Start other program tasks.
    t1 = asyncio.create_task(task1())

    # Start the aiorepl task.
    repl = asyncio.create_task(aiorepl.task())

    await asyncio.gather(t1, repl)

asyncio.run(main())
```

An optional globals dictionary can be passed to `aiorepl.task()`, which allows
you to specify what will be in scope for the REPL. By default it uses the
globals dictionary from the `__main__` module, which is the same scope as the
regular REPL (and `main.py`). In the example above, the REPL will be able to
call the `demo()` function as well as get/set the `state` variable.

You can also provide your own dictionary, e.g. `aiorepl.task({"obj": obj })`,
or use the globals dict from the current module, e.g.
`aiorepl.task(globals())`. Note that you cannot use a class instance's members
dictionary, e.g. `aiorepl.task(obj.__dict__)`, as this is read-only in
MicroPython.

Instead of the regular `>>> ` prompt, the asyncio REPL will show `--> `.

```
--> 1+1
2
--> await demo()
async demo
--> state
20
--> import myapp.core
--> state = await myapp.core.query_state()
--> 1/0
ZeroDivisionError: divide by zero
--> def foo(x): return x + 1
--> await asyncio.sleep(foo(3))
--> 
```

History is supported via the up/down arrow keys.

## Cancellation

During command editing (the "R" phase), pressing Ctrl-C will cancel the current command and display a new prompt, like the regular REPL.

While a command is being executed, Ctrl-C will cancel the task that is executing the command. This will have no effect on blocking code (e.g. `time.sleep()`), but this should be rare in an asyncio-based program.

Ctrl-D at the asyncio REPL command prompt will terminate the current event loop, which will stop the running program and return to the regular REPL.

## Limitations

The following features are unsupported:

* Tab completion is not supported (also unsupported in `python -m asyncio`).
* Multi-line continuation. However you can do single-line definitions of functions, see demo above.
* Exception tracebacks. Only the exception type and message is shown, see demo above.
* Emacs shortcuts (e.g. Ctrl-A, Ctrl-E, to move to start/end of line).
* Unicode handling for input.
