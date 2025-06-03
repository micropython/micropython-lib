# MIT license; Copyright (c) 2022 Jim Mussared

import micropython
from micropython import const
import re
import sys
import time
import asyncio

# Import statement (needs to be global, and does not return).
_RE_IMPORT = re.compile("^import ([^ ]+)( as ([^ ]+))?")
_RE_FROM_IMPORT = re.compile("^from [^ ]+ import ([^ ]+)( as ([^ ]+))?")
# Global variable assignment.
_RE_GLOBAL = re.compile("^([a-zA-Z0-9_]+) ?=[^=]")
# General assignment expression or import statement (does not return a value).
_RE_ASSIGN = re.compile("[^=]=[^=]")

# Command hist (One reserved slot for the current command).
_HISTORY_LIMIT = const(5 + 1)


CHAR_CTRL_A = const(1)
CHAR_CTRL_B = const(2)
CHAR_CTRL_C = const(3)
CHAR_CTRL_D = const(4)
CHAR_CTRL_E = const(5)


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
import asyncio
async def __code():
    {}

__exec_task = asyncio.create_task(__code())
""".format(code)

            async def kbd_intr_task(exec_task, s):
                while True:
                    if ord(await s.read(1)) == CHAR_CTRL_C:
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
async def task(g=None, prompt="--> ", s_in=sys.stdin, s_out=sys.stdout):
    print("Starting asyncio REPL...")
    if g is None:
        g = __import__("__main__").__dict__
    try:
        micropython.kbd_intr(-1)
        s = asyncio.StreamReader(s_in)
        # clear = True
        hist = [None] * _HISTORY_LIMIT
        hist_i = 0  # Index of most recent entry.
        hist_n = 0  # Number of history entries.
        c = 0  # ord of most recent character.
        t = 0  # timestamp of most recent character.
        while True:
            hist_b = 0  # How far back in the history are we currently.
            s_out.write(prompt)
            cmd: str = ""
            paste = False
            curs = 0  # cursor offset from end of cmd buffer
            while True:
                b = await s.read(1)
                pc = c  # save previous character
                c = ord(b)
                pt = t  # save previous time
                t = time.ticks_ms()
                if c < 0x20 or c > 0x7E:
                    if c == 0x0A:
                        # LF
                        if paste:
                            s_out.write(b)
                            cmd += b
                            continue
                        # If the previous character was also LF, and was less
                        # than 20 ms ago, this was likely due to CRLF->LFLF
                        # conversion, so ignore this linefeed.
                        if pc == 0x0A and time.ticks_diff(t, pt) < 20:
                            continue
                        if curs:
                            # move cursor to end of the line
                            s_out.write("\x1b[{}C".format(curs))
                            curs = 0
                        s_out.write("\n")
                        if cmd:
                            # Push current command.
                            hist[hist_i] = cmd
                            # Increase history length if possible, and rotate ring forward.
                            hist_n = min(_HISTORY_LIMIT - 1, hist_n + 1)
                            hist_i = (hist_i + 1) % _HISTORY_LIMIT

                            result = await execute(cmd, g, s)
                            if result is not None:
                                s_out.write(repr(result))
                                s_out.write("\n")
                        break
                    elif c == 0x08 or c == 0x7F:
                        # Backspace.
                        if cmd:
                            if curs:
                                cmd = "".join((cmd[: -curs - 1], cmd[-curs:]))
                                s_out.write(
                                    "\x08\x1b[K"
                                )  # move cursor back, erase to end of line
                                s_out.write(cmd[-curs:])  # redraw line
                                s_out.write("\x1b[{}D".format(curs))  # reset cursor location
                            else:
                                cmd = cmd[:-1]
                                s_out.write("\x08 \x08")
                    elif c == CHAR_CTRL_A:
                        await raw_repl(s_in, s_out, g)
                        break
                    elif c == CHAR_CTRL_B:
                        continue
                    elif c == CHAR_CTRL_C:
                        if paste:
                            break
                        s_out.write("\n")
                        break
                    elif c == CHAR_CTRL_D:
                        if paste:
                            result = await execute(cmd, g, s)
                            if result is not None:
                                s_out.write(repr(result))
                                s_out.write("\n")
                            break

                        s_out.write("\n")
                        # Shutdown asyncio.
                        asyncio.new_event_loop()
                        return
                    elif c == CHAR_CTRL_E:
                        s_out.write("paste mode; Ctrl-C to cancel, Ctrl-D to finish\n===\n")
                        paste = True
                    elif c == 0x1B:
                        # Start of escape sequence.
                        key = await s.read(2)
                        if key in ("[A", "[B"):  # up, down
                            # Stash the current command.
                            hist[(hist_i - hist_b) % _HISTORY_LIMIT] = cmd
                            # Clear current command.
                            b = "\x08" * len(cmd)
                            s_out.write(b)
                            s_out.write(" " * len(cmd))
                            s_out.write(b)
                            # Go backwards or forwards in the history.
                            if key == "[A":
                                hist_b = min(hist_n, hist_b + 1)
                            else:
                                hist_b = max(0, hist_b - 1)
                            # Update current command.
                            cmd = hist[(hist_i - hist_b) % _HISTORY_LIMIT]
                            s_out.write(cmd)
                        elif key == "[D":  # left
                            if curs < len(cmd) - 1:
                                curs += 1
                                s_out.write("\x1b")
                                s_out.write(key)
                        elif key == "[C":  # right
                            if curs:
                                curs -= 1
                                s_out.write("\x1b")
                                s_out.write(key)
                        elif key == "[H":  # home
                            pcurs = curs
                            curs = len(cmd)
                            s_out.write("\x1b[{}D".format(curs - pcurs))  # move cursor left
                        elif key == "[F":  # end
                            pcurs = curs
                            curs = 0
                            s_out.write("\x1b[{}C".format(pcurs))  # move cursor right
                    else:
                        # s_out.write("\\x")
                        # s_out.write(hex(c))
                        pass
                else:
                    if curs:
                        # inserting into middle of line
                        cmd = "".join((cmd[:-curs], b, cmd[-curs:]))
                        s_out.write(cmd[-curs - 1 :])  # redraw line to end
                        s_out.write("\x1b[{}D".format(curs))  # reset cursor location
                    else:
                        s_out.write(b)
                        cmd += b
    finally:
        micropython.kbd_intr(3)


def raw_paste(s_in, s_out, window=512):
    s_out.write("R\x01")  # supported
    s_out.write(bytearray([window & 0xFF, window >> 8, 0x01]).decode())
    eof = False
    idx = 0
    buff = bytearray(window)
    file = b""
    while not eof:
        for idx in range(window):
            b = s_in.read(1)
            c = ord(b)
            if c == CHAR_CTRL_C or c == CHAR_CTRL_D:
                # end of file
                s_out.write(chr(CHAR_CTRL_D))
                if c == CHAR_CTRL_C:
                    raise KeyboardInterrupt
                file += buff[:idx]
                eof = True
                break
            buff[idx] = c

        if not eof:
            file += buff
            s_out.write("\x01")  # indicate window available to host

    return file


async def raw_repl(s_in: io.IOBase, s_out: io.IOBase, g: dict):
    """
    This function is blocking to prevent other
    async tasks from writing to the stdio stream and
    breaking the raw repl session.
    """
    heading = "raw REPL; CTRL-B to exit\n"
    line = ""
    s_out.write(heading)

    while True:
        line = ""
        s_out.write(">")
        while True:
            b = s_in.read(1)
            c = ord(b)
            if c == CHAR_CTRL_A:
                rline = line
                line = ""

                if len(rline) == 2 and ord(rline[0]) == CHAR_CTRL_E:
                    if rline[1] == "A":
                        line = raw_paste(s_in, s_out)
                        break
                else:
                    # reset raw REPL
                    s_out.write(heading)
                    s_out.write(">")
                continue
            elif c == CHAR_CTRL_B:
                # exit raw REPL
                s_out.write("\n")
                return 0
            elif c == CHAR_CTRL_C:
                # clear line
                line = ""
            elif c == CHAR_CTRL_D:
                # entry finished
                # indicate reception of command
                s_out.write("OK")
                break
            else:
                # let through any other raw 8-bit value
                line += b

        if len(line) == 0:
            # Normally used to trigger soft-reset but stay in raw mode.
            # Fake it for aiorepl / mpremote.
            s_out.write("Ignored: soft reboot\n")
            s_out.write(heading)

        try:
            result = exec(line, g)
            if result is not None:
                s_out.write(repr(result))
            s_out.write(chr(CHAR_CTRL_D))
        except Exception as ex:
            print(line)
            s_out.write(chr(CHAR_CTRL_D))
            sys.print_exception(ex, s_out)
        s_out.write(chr(CHAR_CTRL_D))
