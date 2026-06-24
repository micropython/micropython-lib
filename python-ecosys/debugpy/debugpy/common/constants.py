"""Constants used throughout debugpy."""

# Default networking settings
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5678

# DAP message types
MSG_TYPE_REQUEST = "request"
MSG_TYPE_RESPONSE = "response"
MSG_TYPE_EVENT = "event"

# DAP events
EVENT_INITIALIZED = "initialized"
EVENT_STOPPED = "stopped"
EVENT_CONTINUED = "continued"
EVENT_THREAD = "thread"
EVENT_BREAKPOINT = "breakpoint"
EVENT_OUTPUT = "output"
EVENT_TERMINATED = "terminated"
EVENT_EXITED = "exited"

# DAP commands
CMD_INITIALIZE = "initialize"
CMD_LAUNCH = "launch"
CMD_ATTACH = "attach"
CMD_SET_BREAKPOINTS = "setBreakpoints"
CMD_CONTINUE = "continue"
CMD_NEXT = "next"
CMD_STEP_IN = "stepIn"
CMD_STEP_OUT = "stepOut"
CMD_PAUSE = "pause"
CMD_STACK_TRACE = "stackTrace"
CMD_SCOPES = "scopes"
CMD_VARIABLES = "variables"
CMD_EVALUATE = "evaluate"
CMD_DISCONNECT = "disconnect"
CMD_CONFIGURATION_DONE = "configurationDone"
CMD_THREADS = "threads"
CMD_SOURCE = "source"

# Stop reasons
STOP_REASON_STEP = "step"
STOP_REASON_BREAKPOINT = "breakpoint"
STOP_REASON_EXCEPTION = "exception"
STOP_REASON_PAUSE = "pause"
STOP_REASON_ENTRY = "entry"

# Thread reasons
THREAD_REASON_STARTED = "started"
THREAD_REASON_EXITED = "exited"

# Trace events
TRACE_CALL = "call"
TRACE_LINE = "line"
TRACE_RETURN = "return"
TRACE_EXCEPTION = "exception"

# Scope types
SCOPE_LOCALS = "locals"
SCOPE_GLOBALS = "globals"
