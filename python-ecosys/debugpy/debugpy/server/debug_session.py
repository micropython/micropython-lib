"""Main debug session handling DAP protocol communication."""

import sys
from ..common.messaging import JsonMessageChannel
from ..common.constants import (
    CMD_INITIALIZE, CMD_LAUNCH, CMD_ATTACH, CMD_SET_BREAKPOINTS,
    CMD_CONTINUE, CMD_NEXT, CMD_STEP_IN, CMD_STEP_OUT, CMD_PAUSE,
    CMD_STACK_TRACE, CMD_SCOPES, CMD_VARIABLES, CMD_EVALUATE, CMD_DISCONNECT,
    CMD_CONFIGURATION_DONE, CMD_THREADS, CMD_SOURCE, EVENT_INITIALIZED, EVENT_STOPPED, EVENT_CONTINUED, EVENT_TERMINATED,
    STOP_REASON_BREAKPOINT, STOP_REASON_STEP, STOP_REASON_PAUSE,
    TRACE_CALL, TRACE_LINE, TRACE_RETURN, TRACE_EXCEPTION
)
from .pdb_adapter import PdbAdapter


class DebugSession:
    """Manages a debugging session with a DAP client."""

    def __init__(self, client_socket):
        self.debug_logging = False  # Initialize first
        self.channel = JsonMessageChannel(client_socket, self._debug_print)
        self.pdb = PdbAdapter()
        self.pdb._debug_session = self  # Allow PDB to process messages during wait
        self.initialized = False
        self.connected = True
        self.thread_id = 1  # Simple single-thread model
        self.stepping = False
        self.paused = False

    def _debug_print(self, message):
        """Print debug message only if debug logging is enabled."""
        if self.debug_logging:
            print(message)

    @property
    def _baremetal(self) -> bool:
        return sys.platform not in ("linux") # to be expanded

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
                    if message.get('command') == 'attach':
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
        """Process any pending DAP messages without blocking."""
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
            # Reset to blocking mode
            self.channel.sock.settimeout(None)

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
            elif command == CMD_EVALUATE:
                self._handle_evaluate(seq, args)
            elif command == CMD_DISCONNECT:
                self._handle_disconnect(seq, args)
            elif command == CMD_CONFIGURATION_DONE:
                self._handle_configuration_done(seq, args)
            elif command == CMD_THREADS:
                self._handle_threads(seq, args)
            elif command == CMD_SOURCE:
                self._handle_source(seq, args)
            else:
                self.channel.send_response(command, seq, success=False,
                                         message=f"Unknown command: {command}")

        except Exception as e:
            self.channel.send_response(command, seq, success=False,
                                     message=str(e))

    def _handle_initialize(self, seq, args):
        """Handle initialize request."""
        capabilities = {
            "supportsConfigurationDoneRequest": True,
            "supportsFunctionBreakpoints": False,
            "supportsConditionalBreakpoints": False,
            "supportsHitConditionalBreakpoints": False,
            "supportsEvaluateForHovers": True,
            "supportsStepBack": False,
            "supportsSetVariable": False,
            "supportsRestartFrame": False,
            "supportsGotoTargetsRequest": False,
            "supportsStepInTargetsRequest": False,
            "supportsCompletionsRequest": False,
            "supportsModulesRequest": False,
            "additionalModuleColumns": [],
            "supportedChecksumAlgorithms": [],
            "supportsRestartRequest": False,
            "supportsExceptionOptions": False,
            "supportsValueFormattingOptions": False,
            "supportsExceptionInfoRequest": False,
            "supportTerminateDebuggee": True,
            "supportSuspendDebuggee": True,
            "supportsDelayedStackTraceLoading": False,
            "supportsLoadedSourcesRequest": False,
            "supportsLogPoints": False,
            "supportsTerminateThreadsRequest": False,
            "supportsSetExpression": False,
            "supportsTerminateRequest": True,
            "supportsDataBreakpoints": False,
            "supportsReadMemoryRequest": False,
            "supportsWriteMemoryRequest": False,
            "supportsDisassembleRequest": False,
            "supportsCancelRequest": False,
            "supportsBreakpointLocationsRequest": False,
            "supportsClipboardContext": False,
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
        print(f"[DAP] Debug logging {'enabled' if self.debug_logging else 'disabled'} (logToFile={self.debug_logging})")

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

        self.channel.send_response(CMD_SET_BREAKPOINTS, seq,
                                 body={"breakpoints": actual_breakpoints})

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
        self.channel.send_response(CMD_STACK_TRACE, seq,
                                 body={"stackFrames": stack_frames, "totalFrames": len(stack_frames)})

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

    def _handle_evaluate(self, seq, args):
        """Handle evaluate request."""
        expression = args.get("expression", "")
        frame_id = args.get("frameId")
        context = args.get("context", "watch")
        if not expression:
            self.channel.send_response(CMD_EVALUATE, seq, success=False,
                                     message="No expression provided")
            return
        try:
            result = self.pdb.evaluate_expression(expression, frame_id)
            self.channel.send_response(CMD_EVALUATE, seq, body={
                "result": str(result),
                "variablesReference": 0
            })
        except Exception as e:
            self.channel.send_response(CMD_EVALUATE, seq, success=False,
                                     message=str(e))

    def _handle_disconnect(self, seq, args):
        """Handle disconnect request."""
        self.channel.send_response(CMD_DISCONNECT, seq)
        self.disconnect()

    def _handle_configuration_done(self, seq, args):
        """Handle configurationDone request."""
        # This indicates that the client has finished configuring breakpoints
        # and is ready to start debugging
        self.channel.send_response(CMD_CONFIGURATION_DONE, seq)

    def _handle_threads(self, seq, args):
        """Handle threads request."""
        # MicroPython is single-threaded, so return one thread
        threads = [{
            "id": self.thread_id,
            "name": "main"
        }]
        self.channel.send_response(CMD_THREADS, seq, body={"threads": threads})

    def _handle_source(self, seq, args):
        """Handle source request."""
        source = args.get("source", {})
        source_path = source.get("path", "")
        if self._baremetal or not source_path:
            # BUGBUG: unable to read the source on ESP32
            # Possible an effect of the import / inialization sequence ?
            # Nothe that other source files ( other.py) do not seem to get requested in the same way
            self.channel.send_response(CMD_SOURCE, seq, success=False)
            return
        self._debug_print(f"[DAP] Processing source request for path: {source}")
        try:
            # Try to read the source file
            with open(source_path) as f:
                content = f.read()
            self.channel.send_response(CMD_SOURCE, seq, body={"content": content})
        except Exception:
            self.channel.send_response(CMD_SOURCE, seq, success=False,
                                    message="cancelled"
                                    #  message=f"Could not read source: {e}"
                                     )

    def _trace_function(self, frame, event, arg):
        """Trace function called by sys.settrace."""
        # Process any pending DAP messages frequently
        self.process_pending_messages()

        # Handle breakpoints and stepping
        if self.pdb.should_stop(frame, event, arg):
            self._send_stopped_event(STOP_REASON_BREAKPOINT if self.pdb.hit_breakpoint else
                                   STOP_REASON_STEP if self.stepping else STOP_REASON_PAUSE)
            # Wait for continue command
            self.pdb.wait_for_continue()

        return self._trace_function

    def _send_stopped_event(self, reason):
        """Send stopped event to client."""
        self.channel.send_event(EVENT_STOPPED,
                              reason=reason,
                              threadId=self.thread_id,
                              allThreadsStopped=True)

    def wait_for_client(self):
        """Wait for client to initialize."""
        # This is a simplified version - in a real implementation
        # we might want to wait for specific initialization steps

    def trigger_breakpoint(self):
        """Trigger a manual breakpoint."""
        if self.initialized:
            self._send_stopped_event(STOP_REASON_BREAKPOINT)

    def debug_this_thread(self):
        """Enable debugging for current thread."""
        if hasattr(sys, 'settrace'):
            sys.settrace(self._trace_function)

    def is_connected(self):
        """Check if client is connected."""
        return self.connected and not self.channel.closed

    def disconnect(self):
        """Disconnect from client."""
        self.connected = False
        if hasattr(sys, 'settrace'):
            sys.settrace(None)
        self.pdb.cleanup()
        self.channel.close()
