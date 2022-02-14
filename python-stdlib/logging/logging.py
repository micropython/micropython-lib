import os
import socket
import sys
import time

CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20
DEBUG = 10
NOTSET = 0

SYSLOG_FORMAT = "<%(pri)s>1 %(asctime)s %(ip)s - - - - %(message)s"
SYSLOG_DATE_FORMAT = "{0}-{1:02}-{2:02}T{3:02}:{4:02}:{5:02}Z"

DEFAULT_FORMAT = "%(levelname)s:%(name)s:%(message)s"
DEFAULT_DATE_FORMAT = "%d-%02d-%02d %02d:%02d:%02d"

SYSLOG_LOCAL_0 = 16

_level_dict = {
    CRITICAL: "CRIT",
    ERROR: "ERROR",
    WARNING: "WARN",
    INFO: "INFO",
    DEBUG: "DEBUG",
}

_syslog_severity = {
    CRITICAL: 2,
    ERROR: 3,
    WARNING: 4,
    INFO: 6,
    DEBUG: 7,
}


class LogRecord:
    def __init__(self):
        self.__dict__ = {}

    def __getattr__(self, key):
        return self.__dict__[key]


class Handler:
    def __init__(self):
        pass

    def setFormatter(self, fmt):
        self.formatter = fmt

    def format(self, record):
        return self.formatter.format(record)


class Logger:

    level = NOTSET
    handlers = []
    record = LogRecord()

    def __init__(self, name):
        self.name = name

    def _level_str(self, level):
        l = _level_dict.get(level)
        if l is not None:
            return l
        return "LVL%s" % level

    def setLevel(self, level):
        self.level = level

    def isEnabledFor(self, level):
        return level >= (self.level or _level)

    def log(self, level, msg, *args):
        if self.isEnabledFor(level):
            d = self.record.__dict__
            d["levelname"] = self._level_str(level)
            d["levelno"] = level
            d["msg"] = msg
            d["args"] = args
            d["name"] = self.name
            d["created"] = time.time()
            d["uptime"] = time.ticks_ms() // 1000
            d["pri"] = (SYSLOG_LOCAL_0 << 3) + _syslog_severity[level]
            if self.handlers:
                for h in self.handlers:
                    h.emit(self.record)
            else:
                print(_formatter.format(self.record), file=_stream)

    def debug(self, msg, *args):
        self.log(DEBUG, msg, *args)

    def info(self, msg, *args):
        self.log(INFO, msg, *args)

    def warning(self, msg, *args):
        self.log(WARNING, msg, *args)

    def error(self, msg, *args):
        self.log(ERROR, msg, *args)

    def critical(self, msg, *args):
        self.log(CRITICAL, msg, *args)

    def exc(self, e, msg, *args):
        self.log(ERROR, msg, *args)
        sys.print_exception(e, _stream)

    def exception(self, msg, *args):
        self.exc(sys.exc_info()[1], msg, *args)

    def addHandler(self, hndlr):
        self.handlers.append(hndlr)


class Formatter():
    def __init__(self, fmt=None, datefmt=None, style="%", defaults=None):
        self.fmt = fmt or DEFAULT_FORMAT
        self.datefmt = datefmt or DEFAULT_DATE_FORMAT

        if style not in ("%", "{"):
            raise ValueError("Style must be one of: %, {")

        self.style = style
        self.defaults = defaults if defaults else {}

    def usesTime(self):
        if self.style == "%":
            return "%(asctime)" in self.fmt
        elif self.style == "{":
            return "{asctime" in self.fmt

    def format(self, record):
        # merge formatter defaults dict
        if self.defaults:
            record.__dict__.update(self.defaults)

        # The message attribute of the record is computed using msg % args.
        if record.args:
            record.__dict__["message"] = record.msg % record.args
        else:
            record.__dict__["message"] = record.msg

        # If the formatting string contains "(asctime)", formatTime() is called to
        # format the event time.
        if self.usesTime():
            record.__dict__["asctime"] = self.formatTime(record, self.datefmt)

        # The record’s attribute dictionary is used as the operand to a string
        # formatting operation.
        if self.style == "%":
            return self.fmt % record.__dict__
        else:
            return self.fmt.format(**record.__dict__)

    def formatTime(self, record, datefmt=None):
        if not datefmt:
            datefmt = self.datefmt
        created = time.gmtime(record.created)[:6]
        _result = datefmt.format(*created)
        return _result if _result != datefmt else datefmt % created

    def formatException(self, exc_info):
        raise NotImplementedError()

    def formatStack(self, stack_info):
        raise NotImplementedError()


class StreamHandler(Handler):
    def __init__(self, stream=None):
        self.stream = stream or sys.stderr
        self.formatter = Formatter()

    def emit(self, record):
        try:
            self.stream.write(self.format(record))
        except OSError:
            pass

    def flush(self):
        pass


class SocketHandler(Handler):
    def __init__(self, host, port, socktype=socket.SOCK_DGRAM):
        if socktype not in (socket.SOCK_STREAM, socket.SOCK_DGRAM):
            raise ValueError("Invalid socktype")

        self.s = socket.socket(socket.AF_INET, socktype)
        self.addr = socket.getaddrinfo(host, port)[0][-1]
        self.terminator = ""
        self.socktype = socktype
        self.formatter = Formatter()
        self.connected = False

        if socktype == socket.SOCK_STREAM:
            self.terminator = "\n"    # adds PUSH flag to TCP packets
            try:
                self.s.connect(self.addr)
                self.connected = True
            except OSError as e:
                if e.errno == 118:
                    print("No network connection. ", end="")
                elif e.errno == 113:
                    print("Connection timeout. ", end="")
                else:
                    print("Network error. ", end="")
                print("Cannot connect to server {0} on TCP port {1}.".format(self.addr[0], self.addr[1]))

    def emit(self, record):
        try:
            if self.socktype == socket.SOCK_DGRAM or self.connected:
                self.s.sendto(self.format(record) + self.terminator, self.addr)
        except OSError:
            print("Network error, cannot send log to the server.")


class SysLogHandler(SocketHandler):
    """Mostly RFC 5424 compliant logging handler. Does not implement TLS-based transport."""
    def __init__(self, host, port=514, socktype=socket.SOCK_DGRAM):
        super().__init__(host, port, socktype)
        self.formatter = Formatter(fmt=SYSLOG_FORMAT, datefmt=SYSLOG_DATE_FORMAT, defaults={"ip": "-"})


class CircularFileHandler(Handler):
    def __init__(self, filename, maxsize=128_000):
        if maxsize < 256:
            raise ValueError("maxsize must be at least 256 B")
        self.filename = filename
        self.maxsize = maxsize
        self.formatter = Formatter()

        try:
            # checks if file exists and prevents overwriting it
            self.pos = os.stat(self.filename)[6]
            self.file = open(filename, "r+")
        except OSError:
            self.pos = 0
            self.file = open(filename, "w+")

        self.file.seek(self.pos)

    def emit(self, record):
        message = self.format(record)
        if len(message) + self.pos > self.maxsize:
            remaining = self.maxsize - self.pos
            self.file.write(message[:remaining])
            message = message[remaining:]
            self.pos = 0
            self.file.seek(self.pos)
        self.file.write(message)
        self.file.write("\n")
        self.file.flush()
        self.pos += len(message) + 1


_stream = sys.stderr
_level = INFO
_loggers = {}
_formatter = Formatter()

def getLogger(name="root"):
    if name in _loggers:
        return _loggers[name]
    l = Logger(name)
    _loggers[name] = l
    return l

def critical(msg, *args):
    getLogger().critical(msg, *args)

def error(msg, *args):
    getLogger().error(msg, *args)

def warning(msg, *args):
    getLogger().warning(msg, *args)

def info(msg, *args):
    getLogger().info(msg, *args)

def debug(msg, *args):
    getLogger().debug(msg, *args)

def basicConfig(level=INFO, filename=None, stream=None, format=None, datefmt=None, style=None):
    global _level, _stream, _formatter
    _level = level
    getLogger().handlers = []
    if stream:
        _stream = stream
    if filename:
        if stream:
            getLogger().addHandler(StreamHandler(stream))
        getLogger().addHandler(CircularFileHandler(filename))
    if format:
        if not style:
            raise ValueError("style must be specified when the `format` option is used")
        _formatter = Formatter(fmt=format, datefmt=datefmt, style=style)
        for handler in getLogger().handlers:
            handler.setFormatter(_formatter)
