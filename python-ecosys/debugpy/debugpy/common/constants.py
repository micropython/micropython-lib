"""Constants used throughout debugpy."""
from micropython import const

# Default networking settings
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5678

# DAP message types
MSG_TYPE_REQUEST = const("request")
MSG_TYPE_RESPONSE = const("response")
MSG_TYPE_EVENT = const("event")

# DAP events
EVENT_INITIALIZED = const("initialized")
EVENT_STOPPED = const("stopped")
EVENT_CONTINUED = const("continued")
EVENT_THREAD = const("thread")
EVENT_BREAKPOINT = const("breakpoint")
EVENT_OUTPUT = const("output")
EVENT_TERMINATED = const("terminated")
EVENT_EXITED = const("exited")

# DAP commands
CMD_INITIALIZE = const("initialize")
CMD_LAUNCH = const("launch")
CMD_ATTACH = const("attach")
CMD_SET_BREAKPOINTS = const("setBreakpoints")
CMD_CONTINUE = const("continue")
CMD_NEXT = const("next")
CMD_STEP_IN = const("stepIn")
CMD_STEP_OUT = const("stepOut")
CMD_PAUSE = const("pause")
CMD_STACK_TRACE = const("stackTrace")
CMD_SCOPES = const("scopes")
CMD_VARIABLES = const("variables")
CMD_EVALUATE = const("evaluate")
CMD_DISCONNECT = const("disconnect")
CMD_CONFIGURATION_DONE = const("configurationDone")
CMD_THREADS = const("threads")
CMD_SOURCE = const("source")

# Stop reasons
STOP_REASON_STEP = const("step")
STOP_REASON_BREAKPOINT = const("breakpoint")
STOP_REASON_EXCEPTION = const("exception")
STOP_REASON_PAUSE = const("pause")
STOP_REASON_ENTRY = const("entry")

# Thread reasons
THREAD_REASON_STARTED = const("started")
THREAD_REASON_EXITED = const("exited")

# Trace events
TRACE_CALL = const("call")
TRACE_LINE = const("line")
TRACE_RETURN = const("return")
TRACE_EXCEPTION = const("exception")

# Step modes
STEP_INTO = const("into")
STEP_OVER = const("over")
STEP_OUT = const("out")


# Scope types
SCOPE_LOCALS = const("locals")
SCOPE_GLOBALS = const("globals")
