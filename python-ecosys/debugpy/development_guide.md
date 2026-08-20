# Debugging MicroPython debugpy with VS Code

For working on this module: how to see the DAP conversation, and what a healthy
one looks like.

## Starting a session

Nothing in the program being debugged talks to the debugger. The server is
started around it: `listen()`, then `wait_for_client()`, and only then is the
program imported and run, so the breakpoints the client sent are already in
place when its first line executes. `mpremote debug` does that with a boot
script; by hand, on the unix port, the same sequence is:

```bash
<path-to>/micropython -c "import debugpy; debugpy.listen(); \
    debugpy.wait_for_client(); debugpy.debug_this_thread(); \
    import test_vscode; test_vscode.main()"
```

`test_vscode.py` is a sample program with no debugpy import and no manual
breakpoint in it. `wait_for_client()` blocks until a client has attached and
sent `configurationDone`, so there is no race to connect and no sleep to tune.

## Method 1: `--dap-log` (recommended)

If you start sessions with `mpremote debug`, pass `--dap-log`. It interposes a
proxy between the client and the device, records every complete frame in both
directions as JSONL, and reports the proxy's endpoint in place of the device's
so the client cannot bypass it:

```bash
mpremote debug --dap-log --dap-log-file dap.jsonl <target> <module>
```

Without `--dap-log-file` it writes a timestamped file in the current directory.
This works for every transport, including serial, and needs no second port or
alternate launch configuration.

## Method 2: the server's own logging

Start a session by hand, as above, and read the server's own trace from its
output. Connect to `127.0.0.1:5678` with `"logToFile": true` in the
configuration - that flag, read
from the `attach` request, is what turns on the per-message trace, so without it
you get only the handful of unconditional `[DAP]` progress lines
(`vscode_launch_example.json` sets it). From then on each message is printed as
it is handled:

```
[DAP] SEND: response attach (req_seq=2, success=True)
[DAP] RECV: request setBreakpoints (seq=3)
[DAP] SEND: response setBreakpoints (req_seq=3, success=True)
[DAP] RECV: request configurationDone (seq=4)
```

Because the flag arrives with `attach`, nothing up to and including that request
is logged - the attach *response* is the first line, as above.
This is the one method that needs nothing but the firmware, so it is what to
reach for when the question is whether the server received something at all.

## Method 3: `dap_monitor.py`

A standalone host-side proxy: it listens on 5679, forwards to 5678, and prints
the conversation. `--dap-log` supersedes it and is the supported route; this
module is kept for driving a session without mpremote. Using it means pointing
the client at 5679 instead of the port the server reports.

```bash
python3 dap_monitor.py
```

## VS Code debug logging

VS Code can log its own side:

1. Open settings (Ctrl+,)
2. Search for `debug.console.verbosity` and set it to `verbose`
3. Set `debug.allowBreakpointsEverywhere` to `true`

## Expected DAP sequence

```
1. initialize   request -> response with capabilities, then an `initialized` event
2. attach       request -> response
3. setBreakpoints request -> response with verified breakpoints
4. configurationDone request -> response
   ... the debuggee now runs
5. stopped event when execution reaches a breakpoint
6. stackTrace request -> response with frames
7. scopes / variables requests -> response with the frame's scopes
8. continue request -> response, and the program resumes
```

What each step is actually responsible for:

- **`configurationDone` is what releases the debuggee.** `wait_for_client()`
  blocks until it arrives, draining requests while it waits, so breakpoints sent
  before it are already applied when the program starts. Nothing is missed while
  a client connects. This is the only ordering the server enforces.
- **`attach` carries `pathMappings`** and installs the trace function. It is not
  what makes tracing happen when a boot script is in play: `debug_this_thread()`
  installs the same function, so a client that skips `attach` still stops at
  breakpoints - it just gets no path translation, so a breakpoint set under a
  host path will not match what the debuggee reports.
- **`launch` is answered with success and does nothing.** This module is
  attach-only.

Breakpoints can be sent at any point, before or after `configurationDone`, and
`setBreakpoints` does not require `attach` first.

## Common issues to look for

1. **No `stopped` event at all** - check the capability probe first. Without
   `sys.settrace` in the firmware there is no debugger; see the `caps` dict in
   the launcher's handshake line.
2. **Missing DAP capabilities** - check the `initialize` response.
3. **Breakpoint verification failures** - look at the `setBreakpoints` exchange,
   and at whether the path the client sent matches what the debuggee reports.
4. **Locals show as `local_00`, `local_01`, ...** - the firmware was built
   without `MICROPY_PY_SYS_SETTRACE_LOCALNAMES`; the names are not recoverable
   at runtime.
5. **Evaluation problems** - check the `evaluate` request/response pairs.
