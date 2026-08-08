"""Main debug session handling DAP protocol communication."""

import sys
import time

from ..common.constants import (
    CMD_ATTACH,
    CMD_CONFIGURATION_DONE,
    CMD_CONTINUE,
    CMD_DISCONNECT,
    CMD_EVALUATE,
    CMD_INITIALIZE,
    CMD_LAUNCH,
    CMD_NEXT,
    CMD_PAUSE,
    CMD_RESTART,
    CMD_SCOPES,
    CMD_SET_BREAKPOINTS,
    CMD_SET_VARIABLE,
    CMD_SOURCE,
    CMD_STACK_TRACE,
    CMD_STEP_IN,
    CMD_STEP_OUT,
    CMD_THREADS,
    CMD_VARIABLES,
    EVENT_CONTINUED,
    EVENT_INITIALIZED,
    EVENT_OUTPUT,
    EVENT_STOPPED,
    EVENT_TERMINATED,
    STOP_REASON_BREAKPOINT,
    STOP_REASON_PAUSE,
    STOP_REASON_STEP,
    TRACE_CALL,
    TRACE_EXCEPTION,
    TRACE_LINE,
    TRACE_RETURN,
    WAIT_FOR_CLIENT_TIMEOUT_S,
)
from ..common.messaging import JsonMessageChannel
from .pdb_adapter import PdbAdapter


class RestartRequest(BaseException):
    """Raised inside the debugged program to unwind it back to its launcher.

    A restart cannot wait for the target to return - the ordinary embedded
    shape is a main loop that never does - and nothing else on the device can
    interrupt it: there is no second thread, and the DAP message pump runs
    inside the trace function, where raising would kill the program with an
    error belonging to the debug channel. A deliberate raise from the trace
    function is the one remaining mechanism, and it is how CPython debuggers
    unwind a target too.

    Derived from BaseException so a target's own `except Exception` does not
    swallow the unwind and leave the restart silently undone. A target that
    catches BaseException (or uses a bare `except:`) can still swallow it;
    there is no mechanism behind that, only documentation.
    """


def _is_placeholder_local_name(name):
    """True if `name` is a positional `local_N` placeholder, not a real name.

    Without MICROPY_PY_SYS_SETTRACE_SAVE_NAMES, frame.f_locals synthesizes
    names as `local_1`, `local_2`, ... (see py/profile.c). This is the only
    reliable signal that separates the two cases at runtime.
    """
    if not name.startswith("local_"):
        return False
    return name[len("local_") :].isdigit()


# Compiled by the running firmware at probe time; see _probe_local_names.
_LOCAL_NAMES_PROBE_SRC = """
def _probe():
    _mpdbg_probe_local = 1
    return list(sys._getframe().f_locals.keys())
"""


def _probe_local_names(frame):
    """Local names as seen in a frame the *running firmware* compiled.

    Names are attached to a code object when that object is compiled, so
    reading this module's own frame measures whichever compiler produced
    this module, not the firmware. Those differ whenever debugpy is
    installed cross-compiled: mpy-cross only persists names into .mpy with
    MICROPY_PY_SYS_SETTRACE_LOCALNAMES_PERSIST, which is off by default (it
    corrupts line numbers), so an .mpy install always reports placeholders
    however the firmware was built.

    Compiling a throwaway function here measures the firmware's own
    compiler, which is what the `save_names` capability claims. A firmware
    without `exec` cannot compile source at all, so there `frame` - the
    caller's own - is the only frame available and the honest answer.
    """
    namespace = {"sys": sys}
    try:
        exec(_LOCAL_NAMES_PROBE_SRC, namespace)
    except Exception:
        return list(frame.f_locals.keys())
    return namespace["_probe"]()


class DebugSession:
    """Manages a debugging session with a DAP client."""

    def __init__(self, client_socket, is_stream, restart_supported=False):
        self.debug_logging = False  # Initialize first
        self.channel = JsonMessageChannel(client_socket, self._debug_print)
        self.pdb = PdbAdapter()
        # Lets the adapter pump DAP messages while it waits.
        self.pdb._debug_session = self  # type: ignore[assignment]
        self.initialized = False
        self.connected = True
        self.thread_id = 1  # Simple single-thread model
        self.stepping = False
        self.paused = False
        self.configuration_done = False
        self._pumping = False
        # Whether the launcher can actually re-run the target. Only it knows,
        # so a session never assumes it: `restart` is refused, and
        # supportsRestartRequest not advertised, unless it was told otherwise.
        self.restart_supported = restart_supported
        self.restart_requested = False
        # is_stream comes from the caller (_accept_and_initialize already
        # knows which kind of channel client_socket is) rather than being
        # re-derived here, so there is exactly one place that decides it.
        # Probed once at session start; never inferred from a build/variant name.
        self.capabilities = self.probe_capabilities(is_stream)
        self.pdb.capabilities = self.capabilities

    def _debug_print(self, message):
        """Print debug message only if debug logging is enabled."""
        if self.debug_logging:
            print(message)

    @property
    def _baremetal(self) -> bool:
        return sys.platform not in ("linux")  # to be expanded

    @staticmethod
    def probe_capabilities(is_stream):
        """Probe what the running firmware actually supports.

        Returns a dict with at least `settrace`, `save_names`, `set_local`,
        `f_back` and `serial_dap`, each derived by exercising the real
        interpreter - never by reading a build/variant name, which does not
        reliably reflect what a given firmware image supports (see
        BACKGROUND.md). `serial_dap` is the one exception to "probe, don't
        ask": whether the DAP channel is a stream rather than a TCP socket
        is a fact about *this session*, decided by whichever boot script
        called `listen_stream()` vs `listen()`. `is_stream` is that fact -
        required, not defaulted, so a caller cannot silently report "not a
        stream" by forgetting the argument - passed in by the caller rather
        than guessed here, so the two can never disagree. Safe to call on
        both the unix port and bare-metal builds; never raises.

        `save_names` is measured on code the firmware compiles here rather
        than on this module's own frame, so it reports the firmware and not
        how debugpy itself was deployed (see _probe_local_names).
        """
        caps = {
            "settrace": hasattr(sys, "settrace"),
            "f_back": False,
            "save_names": False,
            "set_local": False,
            "serial_dap": is_stream,
        }
        if not caps["settrace"]:
            return caps

        try:
            frame = sys._getframe()
        except Exception:
            return caps

        try:
            caps["f_back"] = hasattr(frame, "f_back")
        except Exception:
            pass

        try:
            caps["set_local"] = hasattr(frame, "_set_local")
        except Exception:
            pass

        try:
            local_names = _probe_local_names(frame)
            # An empty locals dict (e.g. probing from module scope) proves
            # nothing either way; only trust the signal when there is at
            # least one local name to inspect for the placeholder pattern.
            caps["save_names"] = bool(local_names) and not any(
                _is_placeholder_local_name(n) for n in local_names
            )
        except Exception:
            pass

        return caps

    def start(self):
        """Start the debug session message loop."""
        try:
            while self.connected and not self.channel.closed:
                message = self.channel.recv_message()
                if message is None:
                    break

                self._handle_message(message)

        except Exception as e:
            print(f"Debug session error: {e}")
        finally:
            self.disconnect()

    def initialize_connection(self):
        """Initialize the connection - handle just the essential initial messages then return."""
        # Note: debug_logging not available yet during init, so we always show these messages
        print("[DAP] Processing initial DAP messages...")

        try:
            # Process initial messages quickly and return control to main thread
            # We'll handle ongoing messages in the trace function
            attached = False
            message_count = 0
            max_init_messages = 6  # Just handle the first few essential messages

            while message_count < max_init_messages and not attached:
                try:
                    # Short timeout - don't block the main thread for long
                    self.channel.sock.settimeout(1.0)
                    message = self.channel.recv_message()
                    if message is None:
                        print("[DAP] No more messages in initial batch")
                        break

                    print(f"[DAP] Initial message #{message_count + 1}: {message.get('command')}")
                    self._handle_message(message)
                    message_count += 1

                    # Just wait for attach, then we can return control
                    if message.get("command") == "attach":
                        attached = True
                        print("[DAP] ✅ Attach received - returning control to main thread")
                        break

                except Exception as e:
                    print(f"[DAP] Exception in initial processing: {e}")
                    break
                finally:
                    self.channel.sock.settimeout(None)

            # After attach, continue processing a few more messages quickly
            if attached:
                self._debug_print("[DAP] Processing remaining setup messages...")
                additional_count = 0
                while additional_count < 4:  # Just a few more
                    try:
                        self.channel.sock.settimeout(0.5)  # Short timeout
                        message = self.channel.recv_message()
                        if message is None:
                            break
                        self._debug_print(f"[DAP] Setup message: {message.get('command')}")
                        self._handle_message(message)
                        additional_count += 1
                    except:
                        break
                    finally:
                        self.channel.sock.settimeout(None)

            print("[DAP] Initial setup complete - main thread can continue")

        except Exception as e:
            print(f"[DAP] Initialization error: {e}")

    def process_pending_messages(self):
        """Process any pending DAP messages without blocking.

        Not re-entered: the trace function calls this on entry to every new
        frame, so handling a message here can call it again. A nested call
        must not touch the socket timeout, because its `finally` would put the
        socket back into blocking mode underneath the outer loop, whose next
        recv() then waits for a message the client will not send until it has
        seen an event this loop is what produces. MicroPython sockets have no
        gettimeout(), so the nesting is tracked rather than the timeout saved.

        Nothing here may raise: every caller is `_trace_function`, so an
        exception escaping this method lands in whichever line of the
        debugged program was being traced and kills that program with an
        errno belonging to the debug channel, not to anything the program
        did.
        """
        if self._pumping:
            return
        self._pumping = True
        try:
            # Set socket to non-blocking mode for message processing
            self.channel.sock.settimeout(0.001)  # Very short timeout

            while True:
                message = self.channel.recv_message()
                if message is None:
                    break
                self._handle_message(message)

        except Exception:
            # No messages available or socket error
            pass
        finally:
            self._pumping = False
            # Reset to blocking mode - but only against a channel that is
            # still there. Restoring the timeout is a socket operation like
            # any other and fails on a closed socket, and the loop above is
            # exactly what closes it: a `disconnect` request handled there
            # runs the whole session teardown, so on the way out of that
            # request this socket is already gone. A client that vanishes
            # without sending `disconnect` reaches the same place without
            # setting the flag, hence the guard as well as the check.
            # Either way the session is over, so end it here rather than
            # leaving a trace function installed that pumps a dead channel.
            if self.channel.closed:
                return
            try:
                self.channel.sock.settimeout(None)
            except Exception:
                self.disconnect()

    def _handle_message(self, message):
        """Handle incoming DAP messages."""
        msg_type = message.get("type")
        command = message.get("command", message.get("event", "unknown"))
        seq = message.get("seq", 0)

        self._debug_print(f"[DAP] RECV: {msg_type} {command} (seq={seq})")
        if message.get("arguments"):
            self._debug_print(f"[DAP]   args: {message['arguments']}")

        if msg_type == "request":
            self._handle_request(message)
        elif msg_type == "response":
            # We don't expect responses from client
            self._debug_print(f"[DAP] Unexpected response from client: {message}")
        elif msg_type == "event":
            # We don't expect events from client
            self._debug_print(f"[DAP] Unexpected event from client: {message}")

    def _handle_request(self, message):
        """Handle DAP request messages."""
        command = message.get("command")
        seq = message.get("seq", 0)
        args = message.get("arguments", {})

        try:
            if command == CMD_INITIALIZE:
                self._handle_initialize(seq, args)
            elif command == CMD_LAUNCH:
                self._handle_launch(seq, args)
            elif command == CMD_ATTACH:
                self._handle_attach(seq, args)
            elif command == CMD_SET_BREAKPOINTS:
                self._handle_set_breakpoints(seq, args)
            elif command == CMD_CONTINUE:
                self._handle_continue(seq, args)
            elif command == CMD_NEXT:
                self._handle_next(seq, args)
            elif command == CMD_STEP_IN:
                self._handle_step_in(seq, args)
            elif command == CMD_STEP_OUT:
                self._handle_step_out(seq, args)
            elif command == CMD_PAUSE:
                self._handle_pause(seq, args)
            elif command == CMD_STACK_TRACE:
                self._handle_stack_trace(seq, args)
            elif command == CMD_SCOPES:
                self._handle_scopes(seq, args)
            elif command == CMD_VARIABLES:
                self._handle_variables(seq, args)
            elif command == CMD_SET_VARIABLE:
                self._handle_set_variable(seq, args)
            elif command == CMD_EVALUATE:
                self._handle_evaluate(seq, args)
            elif command == CMD_RESTART:
                self._handle_restart(seq, args)
            elif command == CMD_DISCONNECT:
                self._handle_disconnect(seq, args)
            elif command == CMD_CONFIGURATION_DONE:
                self._handle_configuration_done(seq, args)
            elif command == CMD_THREADS:
                self._handle_threads(seq, args)
            elif command == CMD_SOURCE:
                self._handle_source(seq, args)
            else:
                self.channel.send_response(
                    command, seq, success=False, message=f"Unknown command: {command}"
                )

        except Exception as e:
            self.channel.send_response(command, seq, success=False, message=str(e))

    def _handle_initialize(self, seq, args):
        """Handle initialize request."""
        capabilities = {
            "supportsConfigurationDoneRequest": True,
            "supportsEvaluateForHovers": True,
            "supportTerminateDebuggee": True,
            "supportSuspendDebuggee": True,
            "supportsTerminateRequest": True,
            "supportsSetVariable": True,
            # "supportsFunctionBreakpoints": False,
            # "supportsConditionalBreakpoints": False,
            # "supportsHitConditionalBreakpoints": False,
            # "supportsStepBack": False,
            # "supportsRestartFrame": False,
            # "supportsGotoTargetsRequest": False,
            # "supportsStepInTargetsRequest": False,
            # "supportsCompletionsRequest": False,
            # "supportsModulesRequest": False,
            # "additionalModuleColumns": [],
            # "supportedChecksumAlgorithms": [],
            # Advertised only when the launcher runs the target in a loop it
            # can re-enter; a client that sees this offers a restart button
            # and expects the debuggee to come back, not the session to end.
            "supportsRestartRequest": self.restart_supported,
            # "supportsExceptionOptions": False,
            # "supportsValueFormattingOptions": False,
            # "supportsExceptionInfoRequest": False,
            # "supportsDelayedStackTraceLoading": False,
            # "supportsLoadedSourcesRequest": False,
            # "supportsLogPoints": False,
            # "supportsTerminateThreadsRequest": False,
            # "supportsSetExpression": False,
            # "supportsDataBreakpoints": False,
            # "supportsReadMemoryRequest": False,
            # "supportsWriteMemoryRequest": False,
            # "supportsDisassembleRequest": False,
            # "supportsCancelRequest": False,
            # "supportsBreakpointLocationsRequest": False,
            # "supportsClipboardContext": False,
        }

        self.channel.send_response(CMD_INITIALIZE, seq, body=capabilities)
        self.channel.send_event(EVENT_INITIALIZED)
        self.initialized = True

    def _handle_launch(self, seq, args):
        """Handle launch request."""
        # For attach-mode debugging, we don't need to launch anything
        self.channel.send_response(CMD_LAUNCH, seq)

    def _handle_attach(self, seq, args):
        """Handle attach request."""
        # Check if debug logging should be enabled
        self.debug_logging = args.get("logToFile", False)

        self._debug_print(f"[DAP] Processing attach request with args: {args}")
        print(
            f"[DAP] Debug logging {'enabled' if self.debug_logging else 'disabled'} (logToFile={self.debug_logging})"
        )

        # get debugger root and debuggee root from pathMappings
        for pm in args.get("pathMappings", []):
            # debuggee - debugger. Trailing slashes are stripped so "/remote"
            # and "/remote/" name the same root: pdb_adapter's translation
            # matches a mapping on a path-separator boundary it adds itself,
            # and a root that already carries one would double it up.
            remote_root = pm.get("remoteRoot", "./").rstrip("/")
            local_root = pm.get("localRoot", "./").rstrip("/")
            self.pdb.path_mappings.append((remote_root, local_root))
        # # TODO: justMyCode, debugOptions  ,

        # Enable trace function
        self.pdb.set_trace_function(self._trace_function)
        self.channel.send_response(CMD_ATTACH, seq)

        # After successful attach, we might need to send additional events
        # Some debuggers expect a 'process' event or thread events
        self._debug_print("[DAP] Attach completed, debugging is now active")

    def _handle_set_breakpoints(self, seq, args):
        """Handle setBreakpoints request."""
        source = args.get("source", {})
        filename = source.get("path", "<unknown>")
        breakpoints = args.get("breakpoints", [])

        # Debug log the source information
        self._debug_print(f"[DAP] setBreakpoints source info: {source}")

        # Set breakpoints in pdb adapter
        actual_breakpoints = self.pdb.set_breakpoints(filename, breakpoints)

        self.channel.send_response(
            CMD_SET_BREAKPOINTS, seq, body={"breakpoints": actual_breakpoints}
        )

    def _handle_continue(self, seq, args):
        """Handle continue request."""
        self.stepping = False
        self.paused = False
        self.pdb.continue_execution()
        self.channel.send_response(CMD_CONTINUE, seq)

    def _handle_next(self, seq, args):
        """Handle next (step over) request."""
        self.stepping = True
        self.paused = False
        self.pdb.step_over()
        self.channel.send_response(CMD_NEXT, seq)

    def _handle_step_in(self, seq, args):
        """Handle stepIn request."""
        self.stepping = True
        self.paused = False
        self.pdb.step_into()
        self.channel.send_response(CMD_STEP_IN, seq)

    def _handle_step_out(self, seq, args):
        """Handle stepOut request."""
        self.stepping = True
        self.paused = False
        self.pdb.step_out()
        self.channel.send_response(CMD_STEP_OUT, seq)

    def _handle_pause(self, seq, args):
        """Handle pause request."""
        self.paused = True
        self.pdb.pause()
        self.channel.send_response(CMD_PAUSE, seq)

    def _handle_stack_trace(self, seq, args):
        """Handle stackTrace request."""
        stack_frames = self.pdb.get_stack_trace()
        self.channel.send_response(
            CMD_STACK_TRACE,
            seq,
            body={"stackFrames": stack_frames, "totalFrames": len(stack_frames)},
        )

    def _handle_scopes(self, seq, args):
        """Handle scopes request."""
        frame_id = args.get("frameId", 0)
        self._debug_print(f"[DAP] Processing scopes request for frameId={frame_id}")
        scopes = self.pdb.get_scopes(frame_id)
        self._debug_print(f"[DAP] Generated scopes: {scopes}")
        self.channel.send_response(CMD_SCOPES, seq, body={"scopes": scopes})

    def _handle_variables(self, seq, args):
        """Handle variables request."""
        variables_ref = args.get("variablesReference", 0)
        variables = self.pdb.get_variables(variables_ref)
        self.channel.send_response(CMD_VARIABLES, seq, body={"variables": variables})

    def _handle_set_variable(self, seq, args):
        """Handle setVariable request."""
        variables_ref = args.get("variablesReference", 0)
        name = args.get("name", "")
        value = args.get("value", "")

        if not name:
            self.channel.send_response(
                CMD_SET_VARIABLE, seq, success=False, message="No variable name provided"
            )
            return

        self._debug_print(
            f"[DAP] Processing setVariable request: name={name}, value={value}, ref={variables_ref}"
        )

        try:
            updated_variable = self.pdb.set_variable(variables_ref, name, value)
            self.channel.send_response(CMD_SET_VARIABLE, seq, body=updated_variable)
        except Exception as e:
            self.channel.send_response(CMD_SET_VARIABLE, seq, success=False, message=str(e))

    def _handle_evaluate(self, seq, args):
        """Handle evaluate request.

        `context` selects the contract PdbAdapter.evaluate_expression applies:
        `repl`/`clipboard` (Debug Console, "Copy as Expression") may execute a
        statement when `expression` isn't a valid expression; `watch`/`hover`
        and any other or absent context stay read-only eval.
        """
        expression = args.get("expression", "")
        frame_id = args.get("frameId")
        context = args.get("context", "watch")
        if not expression:
            self.channel.send_response(
                CMD_EVALUATE, seq, success=False, message="No expression provided"
            )
            return
        try:
            result = self.pdb.evaluate_expression(expression, frame_id, context)
            self.channel.send_response(
                CMD_EVALUATE, seq, body={"result": str(result), "variablesReference": 0}
            )
        except Exception as e:
            self.channel.send_response(CMD_EVALUATE, seq, success=False, message=str(e))

    def _handle_restart(self, seq, args):
        """Handle restart request: unwind the target so the launcher re-runs it.

        The session outlives the restart deliberately. Breakpoints live in
        `self.pdb`, and a client that sent `restart` rather than reconnecting
        does not re-send them, so keeping the one session alive is what makes
        them still bind on the next run - and it costs no re-attach round trip.

        Only the flag is set here. Whatever the target is doing, it is doing it
        somewhere below this call: this runs inside the trace function, so the
        unwind happens where that returns to, not here.
        """
        if not self.restart_supported:
            self.channel.send_response(
                CMD_RESTART,
                seq,
                success=False,
                message="the target was not launched in a loop that can re-run it",
            )
            return

        self.restart_requested = True
        # A target stopped at a breakpoint is inside wait_for_continue(); it has
        # to be let go before it can be unwound. Stepping is cleared with it, so
        # a pending step does not stop the target again on its way out.
        self.stepping = False
        self.pdb.step_mode = None
        self.pdb.paused = False
        self.pdb.continue_event = True

        self.channel.send_response(CMD_RESTART, seq)
        # The client last heard `stopped`; without this its UI stays stopped on
        # a frame that is about to cease to exist.
        self.channel.send_event(EVENT_CONTINUED, threadId=self.thread_id, allThreadsContinued=True)

    def _raise_if_restarting(self):
        """Unwind the target if a restart arrived, clearing the request.

        Cleared here, not by the launcher, so the exception itself is the whole
        signal: one restart unwinds one run, and a second request during the
        unwind is a fresh one rather than a repeat of this.
        """
        if self.restart_requested:
            self.restart_requested = False
            raise RestartRequest

    def console(self, text):
        """Show `text` in the client's debug console (a DAP `output` event).

        The only route a target's own notes have to the user on a transport
        where device stdout never reaches the host: a mounted serial session's
        filesystem pump discards everything the device prints. Run-boundary
        markers go through here as well as to stdout so they are visible on
        every transport, not just the ones with a readable console.
        """
        self.channel.send_event(EVENT_OUTPUT, category="console", output=text)

    def wait_for_restart(self):
        """Pump DAP messages between runs, until a restart or the client leaves.

        A target that returned normally is no longer generating trace events, so
        nothing would service the socket and a restart request would sit unread
        in it. Returns True if a restart arrived, False if the client went away,
        in which case there is nothing left to restart for.

        `terminated` is deliberately not what marks the end of a run: a client
        that sees it tears the session down, which is the opposite of what loop
        mode exists for. An `output` event says the same thing without ending
        anything, and is the only notice a client gets that the program has
        finished and a restart is what comes next.

        Callers must not be traced while they wait here: a restart handled by
        the pump below would otherwise unwind the caller itself.
        """
        self.console("Target finished; waiting for a restart request.\n")
        while True:
            if self.restart_requested:
                self.restart_requested = False
                return True
            if not self.connected or self.channel.closed:
                return False
            self.process_pending_messages()
            time.sleep(0.01)

    def _handle_disconnect(self, seq, args):
        """Handle disconnect request."""
        self.channel.send_response(CMD_DISCONNECT, seq)
        self.disconnect()

    def _handle_configuration_done(self, seq, args):
        """Handle configurationDone request."""
        # This indicates that the client has finished configuring breakpoints
        # and is ready to start debugging
        self.configuration_done = True
        self.channel.send_response(CMD_CONFIGURATION_DONE, seq)

    def _handle_threads(self, seq, args):
        """Handle threads request."""
        # MicroPython is single-threaded, so return one thread
        threads = [{"id": self.thread_id, "name": "main"}]
        self.channel.send_response(CMD_THREADS, seq, body={"threads": threads})

    def _handle_source(self, seq, args):
        """Handle source request."""
        source = args.get("source", {})
        source_path = source.get("path", "")
        if self._baremetal or not source_path:
            # BUG: unable to read the source on ESP32
            # Possible an effect of the import / initialization sequence ?
            # Note that other source files ( other.py) do not seem to get requested in the same way
            self.channel.send_response(CMD_SOURCE, seq, success=False)
            return
        self._debug_print(f"[DAP] Processing source request for path: {source}")
        try:
            # Try to read the source file
            with open(source_path) as f:
                content = f.read()
            self.channel.send_response(CMD_SOURCE, seq, body={"content": content})
        except Exception:
            self.channel.send_response(
                CMD_SOURCE,
                seq,
                success=False,
                message="cancelled",
                #  message=f"Could not read source: {e}"
            )

    def _trace_function(self, frame, event: str, arg):
        """Trace function called by sys.settrace."""
        # https://docs.python.org/3/library/sys.html#sys.settrace
        global _twiddel
        # Process any pending DAP messages frequently

        self.process_pending_messages()
        # Before any breakpoint work: a restart that arrived above wants this
        # program gone, not stopped somewhere else on the way out.
        self._raise_if_restarting()
        # Handle breakpoints and stepping
        if self.pdb.should_stop(frame, event, arg):
            self._send_stopped_event(
                STOP_REASON_BREAKPOINT
                if self.pdb.hit_breakpoint
                else STOP_REASON_STEP
                if self.stepping
                else STOP_REASON_PAUSE
            )
            # Wait for continue command
            self.pdb.wait_for_continue()
            # A restart is one of the things that ends that wait.
            self._raise_if_restarting()

        # The trace function is invoked (with event set to 'call') whenever a new local scope is entered;
        # it should return a reference to a local trace function to be used for the new scope,
        # or None if the scope shouldn't be traced.

        return self._trace_function

    def _send_stopped_event(self, reason):
        """Send stopped event to client."""
        self.channel.send_event(
            EVENT_STOPPED, reason=reason, threadId=self.thread_id, allThreadsStopped=True
        )

    def wait_for_client(self, timeout_s=WAIT_FOR_CLIENT_TIMEOUT_S):
        """Block until the client has sent configurationDone, or time out.

        Same busy-poll shape as PdbAdapter.wait_for_continue(): there is no
        server thread, so nothing services the socket unless this loop drains
        it. Replaces a fixed sleep with a deterministic handshake - breakpoints
        set before configurationDone are already applied by the time this
        returns because process_pending_messages() has drained them too.
        Returns True once configurationDone arrives, False if the bounded
        timeout elapses first (a hard failure is worse than continuing with a
        clear log message: a client that never configures is a client bug or
        a dropped connection, not something to hang on forever).
        """
        start = time.ticks_ms()
        while not self.configuration_done:
            self.process_pending_messages()
            if not self.connected or self.channel.closed:
                print("[DAP] wait_for_client: connection closed before configurationDone")
                return False
            if time.ticks_diff(time.ticks_ms(), start) > timeout_s * 1000:
                print(
                    "[DAP] wait_for_client: timed out after {}s waiting for configurationDone".format(
                        timeout_s
                    )
                )
                return False
            time.sleep(0.01)
        return True

    def trigger_breakpoint(self):
        """Trigger a manual breakpoint."""
        if self.initialized:
            self._send_stopped_event(STOP_REASON_BREAKPOINT)

    def debug_this_thread(self):
        """Enable debugging for current thread."""
        if hasattr(sys, "settrace"):
            sys.settrace(self._trace_function)

    def is_connected(self):
        """Check if client is connected."""
        return self.connected and not self.channel.closed

    def disconnect(self):
        """Disconnect from client."""
        self.connected = False
        if hasattr(sys, "settrace"):
            sys.settrace(None)
        self.pdb.cleanup()
        self.channel.close()
