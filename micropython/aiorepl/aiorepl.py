# MIT license; Copyright (c) 2022 Jim Mussared

import micropython
from micropython import const
import re
import sys
import time
import uasyncio as asyncio

# Import statement (needs to be global, and does not return).
_RE_IMPORT = re.compile("^import ([^ ]+)( as ([^ ]+))?")
_RE_FROM_IMPORT = re.compile("^from [^ ]+ import ([^ ]+)( as ([^ ]+))?")
# Global variable assignment.
_RE_GLOBAL = re.compile("^([a-zA-Z0-9_]+) ?=[^=]")
# General assignment expression or import statement (does not return a value).
_RE_ASSIGN = re.compile("[^=]=[^=]")

# Command hist (One reserved slot for the current command).
_HISTORY_LIMIT = const(5 + 1)


async def execute(code, g, s):
    if not code.strip():
        return

    try:
        if "await " in code:
            # Execute the code snippet in an async context.
            if m := _RE_IMPORT.match(code) or _RE_FROM_IMPORT.match(code):
                code = "global {}\n    {}".format(m.group(3) or m.group(1), code)
            elif m := _RE_GLOBAL.match(code):
                code = "global {}\n    {}".format(m.group(1), code)
            elif not _RE_ASSIGN.search(code):
                code = "return {}".format(code)

            code = """
import uasyncio as asyncio
async def __code():
    {}

__exec_task = asyncio.create_task(__code())
""".format(
                code
            )

            async def kbd_intr_task(exec_task, s):
                while True:
                    if ord(await s.read(1)) == 0x03:
                        exec_task.cancel()
                        return

            l = {"__exec_task": None}
            exec(code, g, l)
            exec_task = l["__exec_task"]

            # Concurrently wait for either Ctrl-C from the stream or task
            # completion.
            intr_task = asyncio.create_task(kbd_intr_task(exec_task, s))

            try:
                try:
                    return await exec_task
                except asyncio.CancelledError:
                    pass
            finally:
                intr_task.cancel()
                try:
                    await intr_task
                except asyncio.CancelledError:
                    pass
        else:
            # Excute code snippet directly.
            try:
                try:
                    micropython.kbd_intr(3)
                    try:
                        return eval(code, g)
                    except SyntaxError:
                        # Maybe an assignment, try with exec.
                        return exec(code, g)
                except KeyboardInterrupt:
                    pass
            finally:
                micropython.kbd_intr(-1)

    except Exception as err:
        print("{}: {}".format(type(err).__name__, err))


# REPL task. Invoke this with an optional mutable globals dict.
async def task(g=None, prompt="--> "):
    print("Starting asyncio REPL...")
    if g is None:
        g = __import__("__main__").__dict__
    try:
        micropython.kbd_intr(-1)
        s = asyncio.StreamReader(sys.stdin)
        # clear = True
        hist = [None] * _HISTORY_LIMIT
        hist_i = 0  # Index of most recent entry.
        hist_n = 0  # Number of history entries.
        c = 0  # ord of most recent character.
        t = 0  # timestamp of most recent character.
        while True:
            hist_b = 0  # How far back in the history are we currently.
            sys.stdout.write(prompt)
            cmd = ""
            while True:
                b = await s.read(1)
                pc = c  # save previous character
                c = ord(b)
                pt = t  # save previous time
                t = time.ticks_ms()
                if c < 0x20 or c > 0x7E:
                    if c == 0x0A:
                        # LF
                        # If the previous character was also LF, and was less
                        # than 20 ms ago, this was likely due to CRLF->LFLF
                        # conversion, so ignore this linefeed.
                        if pc == 0x0A and time.ticks_diff(t, pt) < 20:
                            continue
                        sys.stdout.write("\n")
                        if cmd:
                            # Push current command.
                            hist[hist_i] = cmd
                            # Increase history length if possible, and rotate ring forward.
                            hist_n = min(_HISTORY_LIMIT - 1, hist_n + 1)
                            hist_i = (hist_i + 1) % _HISTORY_LIMIT

                            result = await execute(cmd, g, s)
                            if result is not None:
                                sys.stdout.write(repr(result))
                                sys.stdout.write("\n")
                        break
                    elif c == 0x08 or c == 0x7F:
                        # Backspace.
                        if cmd:
                            cmd = cmd[:-1]
                            sys.stdout.write("\x08 \x08")
                    elif c == 0x02:
                        # Ctrl-B
                        continue
                    elif c == 0x03:
                        # Ctrl-C
                        if pc == 0x03 and time.ticks_diff(t, pt) < 20:
                            # Two very quick Ctrl-C (faster than a human
                            # typing) likely means mpremote trying to
                            # escape.
                            asyncio.new_event_loop()
                            return
                        sys.stdout.write("\n")
                        break
                    elif c == 0x04:
                        # Ctrl-D
                        sys.stdout.write("\n")
                        # Shutdown asyncio.
                        asyncio.new_event_loop()
                        return
                    elif c == 0x1B:
                        # Start of escape sequence.
                        key = await s.read(2)
                        if key in ("[A", "[B"):
                            # Stash the current command.
                            hist[(hist_i - hist_b) % _HISTORY_LIMIT] = cmd
                            # Clear current command.
                            b = "\x08" * len(cmd)
                            sys.stdout.write(b)
                            sys.stdout.write(" " * len(cmd))
                            sys.stdout.write(b)
                            # Go backwards or forwards in the history.
                            if key == "[A":
                                hist_b = min(hist_n, hist_b + 1)
                            else:
                                hist_b = max(0, hist_b - 1)
                            # Update current command.
                            cmd = hist[(hist_i - hist_b) % _HISTORY_LIMIT]
                            sys.stdout.write(cmd)
                    else:
                        # sys.stdout.write("\\x")
                        # sys.stdout.write(hex(c))
                        pass
                else:
                    sys.stdout.write(b)
                    cmd += b
    finally:
        micropython.kbd_intr(3)
