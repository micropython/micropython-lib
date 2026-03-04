#!/usr/bin/env python3
"""PTY-based integration test for aiorepl features.

Requires the unix port of micropython.

Usage:
    python3 test_aiorepl_pty.py [path/to/micropython]

The micropython binary must have MICROPY_HELPER_REPL and
MICROPY_PY_MICROPYTHON_STDIO_RAW enabled (unix standard build).
MICROPYPATH is set automatically to include frozen modules and this
directory (for aiorepl).
"""

import os
import pty
import re
import select
import subprocess
import sys


MICROPYTHON = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
    "MICROPY_MICROPYTHON", "micropython"
)


def get(master, timeout=0.02, required=False):
    """Read from PTY master until *timeout* seconds of silence."""
    rv = b""
    while True:
        ready = select.select([master], [], [], timeout)
        if ready[0] == [master]:
            rv += os.read(master, 1024)
        else:
            if not required or rv:
                return rv


def send_get(master, data, timeout=0.02):
    """Write *data* to PTY master and return response after silence."""
    os.write(master, data)
    return get(master, timeout)


def strip_ansi(data):
    """Remove ANSI escape sequences from bytes."""
    return re.sub(rb"\x1b\[[0-9;]*[A-Za-z]", b"", data)


class TestFailure(Exception):
    pass


def assert_in(needle, haystack, label):
    if needle not in haystack:
        raise TestFailure(
            f"[{label}] expected {needle!r} in output, got: {haystack!r}"
        )


def assert_not_in(needle, haystack, label):
    if needle in haystack:
        raise TestFailure(
            f"[{label}] did not expect {needle!r} in output, got: {haystack!r}"
        )


def main():
    master, slave = pty.openpty()

    # Build MICROPYPATH: frozen modules + this directory (for aiorepl).
    this_dir = os.path.dirname(os.path.abspath(__file__))
    env = os.environ.copy()
    env["MICROPYPATH"] = ".frozen:" + this_dir

    p = subprocess.Popen(
        [MICROPYTHON],
        stdin=slave,
        stdout=slave,
        stderr=subprocess.STDOUT,
        bufsize=0,
        env=env,
    )

    passed = 0
    failed = 0

    try:
        # Wait for the standard REPL banner and >>> prompt.
        banner = get(master, timeout=0.1, required=True)
        if b">>>" not in banner:
            raise TestFailure(f"No REPL banner/prompt, got: {banner!r}")

        # --- Test 1: Start aiorepl ---
        # Standard REPL readline handles both \r and \n as enter.
        resp = send_get(
            master,
            b"import asyncio, aiorepl; asyncio.run(aiorepl.task())\r",
            timeout=0.1,
        )
        assert_in(b"Starting asyncio REPL", resp, "startup")
        assert_in(b"--> ", resp, "startup prompt")
        print("PASS: startup")
        passed += 1

        # Once aiorepl is running, the terminal is in raw mode (ICRNL cleared),
        # and aiorepl only handles 0x0A (LF) as enter — not 0x0D (CR).
        # All subsequent commands must use \n.

        # --- Test 2: Single tab completion ---
        # Type "impo" then tab. Should complete to "import " (suffix "rt ").
        resp = send_get(master, b"impo\x09", timeout=0.05)
        clean = strip_ansi(resp)
        assert_in(b"rt ", clean, "single tab completion")
        # Ctrl-C to clear and get fresh prompt.
        resp = send_get(master, b"\x03", timeout=0.05)
        assert_in(b"--> ", resp, "prompt after ctrl-c")
        print("PASS: single tab completion")
        passed += 1

        # --- Test 3: Attribute tab completion ---
        # First import sys.
        resp = send_get(master, b"import sys\n", timeout=0.1)
        # Now type "sys.ver" + tab. Should complete common prefix "sion".
        resp = send_get(master, b"sys.ver\x09", timeout=0.05)
        clean = strip_ansi(resp)
        assert_in(b"sion", clean, "attribute tab completion")
        # Ctrl-C to clear.
        resp = send_get(master, b"\x03", timeout=0.05)
        print("PASS: attribute tab completion")
        passed += 1

        # --- Test 4: Multiple-match completion ---
        # Create two globals sharing prefix "_tc".
        resp = send_get(master, b"_tca=1;_tcb=2\n", timeout=0.1)
        # Type "_tc" + tab. Multiple matches -> candidates printed, returns None.
        resp = send_get(master, b"_tc\x09", timeout=0.05)
        clean = strip_ansi(resp)
        assert_in(b"_tca", clean, "multi-match candidates")
        assert_in(b"_tcb", clean, "multi-match candidates")
        # The prompt and partial input should be redrawn.
        assert_in(b"--> ", clean, "multi-match prompt redraw")
        # Ctrl-C to clear.
        resp = send_get(master, b"\x03", timeout=0.05)
        print("PASS: multiple-match completion")
        passed += 1

        # --- Test 5: Command execution ---
        resp = send_get(master, b"print(42)\n", timeout=0.1)
        assert_in(b"42", resp, "command execution")
        print("PASS: command execution")
        passed += 1

        # --- Test 6: Terminal mode verification ---
        # aiorepl calls _stdio_raw(False) before execute(), so during execution
        # the terminal should be in original (non-raw) mode with LFLAG non-zero.
        resp = send_get(
            master,
            b"import termios; print('lflag:', termios.tcgetattr(0)[3] != 0)\n",
            timeout=0.1,
        )
        assert_in(b"lflag: True", resp, "terminal mode")
        print("PASS: terminal mode verification")
        passed += 1

        # --- Test 7: Ctrl-D exit ---
        # Ctrl-D on empty line should exit aiorepl and return to standard REPL.
        resp = send_get(master, b"\x04", timeout=0.1)
        assert_in(b">>>", resp, "ctrl-d exit")
        print("PASS: ctrl-d exit")
        passed += 1

    except TestFailure as e:
        print(f"FAIL: {e}")
        failed += 1
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        failed += 1
    finally:
        try:
            p.kill()
        except ProcessLookupError:
            pass
        p.wait()
        os.close(master)
        os.close(slave)

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
