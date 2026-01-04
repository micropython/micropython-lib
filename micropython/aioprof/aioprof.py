import json as jsonlib
from time import ticks_ms, ticks_diff
import uasyncio as asyncio

## Public API


def enable():
    """
    Once enabled, all new asyncio tasks will be tracked.
    Existing tasks will not be tracked.
    """
    asyncio.Task = Task
    asyncio.core.Task = Task


def reset():
    """
    Reset all the accumlated task data
    """
    global timing
    timing = {}


def report():
    """
    Print a report to repl of task run count and timing.
    """
    details = [
        (name, str(value[0]), str(value[1]))
        for name, value in reversed(sorted(timing.items(), key=lambda i: i[1][1]))
    ]

    nlen = max([len(n) for n, i, t in details])
    ilen = max((len("count"), max([len(i) for n, i, t in details])))
    tlen = max([len(t) for n, i, t in details])

    print("┌─" + "─" * nlen + "─┬─" + "─" * ilen + "─┬─" + "─" * tlen + "─┐")
    print(f"│ function name {' '*(nlen-14)} │ count{' '*(ilen-5)} │ ms {' '*(tlen-2)}│")
    print("├─" + "─" * nlen + "─┼─" + "─" * ilen + "─┼─" + "─" * tlen + "─┤")
    for name, i, t in details:
        npad = " " * (nlen - len(name))
        ipad = " " * (ilen - len(i))
        tpad = " " * (tlen - len(t))
        print(f"│ {name}{npad} │ {i}{ipad} │ {t}{tpad} │")
    print("└─" + "─" * nlen + "─┴─" + "─" * ilen + "─┴─" + "─" * tlen + "─┘")


def json():
    """
    Directly dump the task [run-count,timing] details as json.
    """
    return jsonlib.dumps(timing)


## Internal functionality

__task = asyncio.Task
timing = {}


class Coro:
    def __init__(self, c) -> None:
        self.name = str(c)
        self.c = c

    def send(self, *args, **kwargs):
        t_name = self.name
        t_start = ticks_ms()
        try:
            ret = self.c.send(*args, **kwargs)
        finally:
            if t_name not in timing:
                timing[t_name] = [0, 0]

            t = timing[t_name]
            t[0] += 1
            t[1] += ticks_diff(ticks_ms(), t_start)
        return ret

    def __getattr__(self, name: str):
        return getattr(self.c, name)


def Task(coro, glob):
    return __task(Coro(coro), glob)
