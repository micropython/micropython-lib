import sys
import utime

CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20
DEBUG = 10
NOTSET = 0

_level_dict = {
    CRITICAL: "CRIT",
    ERROR: "ERROR",
    WARNING: "WARN",
    INFO: "INFO",
    DEBUG: "DEBUG",
}



class LogRecord:
    def __init__(self):
        self.__dict__ = {}
        ct = utime.time()
        self.message = ""
        self.asctime = None
        self.exc_info = None
        self.exc_text = None
        self.created = ct

    def __getattr__(self, key):
        return self.__dict__[key]


class Handler:
    def __init__(self):
        self.formatter = Formatter()

    def setFormatter(self, fmt):
        self.formatter = fmt

class StreamHandler(Handler):
    def __init__(self, stream=None):
        self._stream = stream or sys.stderr
        self.terminator = "\n"
        self.formatter = Formatter()

    def emit(self, record):
        self._stream.write(self.formatter.format(record) + self.terminator)

    def flush(self):
        pass

class FileHandler(Handler):
    def __init__(self, filename, mode="a", encoding=None, delay=False):
        super().__init__()

        self.encoding = encoding
        self.mode = mode
        self.delay = delay
        self.terminator = "\n"
        self.filename = filename
        self._f = None


    def emit(self, record):

        self._f = open(self.filename, self.mode)
        self._f.write(self.formatter.format(record) + self.terminator)

    def close(self):
        if self._f is not None:
            self._f.close()


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
            levelname = self._level_str(level)
            if args:
                msg = msg % args
            if self.handlers:
                d = self.record.__dict__
                d["levelname"] = levelname
                d["levelno"] = level
                d["message"] = msg
                d["name"] = self.name
                for h in self.handlers:
                    self.record.message = msg
                    h.emit(self.record)
            else:
                print(levelname, ":", self.name, ":", msg, sep="", file=_stream)

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

class Formatter:
    def __init__(self, fmt=None, datefmt=None, style="%"):
        self.fmt = fmt or "%(message)s"
        self.datefmt = datefmt

        if style not in ("%", "{"):
            raise ValueError("Style must be one of: %, {")

        self.style = style

    def usesTime(self):
        if self.style == "%":
            return "%(asctime)" in self.fmt
        elif self.style == "{":
            return "{asctime" in self.fmt

    def format(self, record):
        # If the formatting string contains '(asctime)', formatTime() is called to
        # format the event time.
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
            record.__dict__["asctime"] = record.asctime

        # If there is exception information, it is formatted using formatException()
        # and appended to the message. The formatted exception information is cached
        # in attribute exc_text.
        if record.exc_info is not None:
            record.exc_text += self.formatException(record.exc_info)
            record.message += "\n" + record.exc_text

        # The record’s attribute dictionary is used as the operand to a string
        # formatting operation.
        if self.style == "%":
            return self.fmt % record.__dict__
        elif self.style == "{":
            return self.fmt.format(**record.__dict__)
        else:
            raise ValueError(
                "Style {0} is not supported by logging.".format(self.style)
            )

    def formatTime(self, record, datefmt=None):
        assert datefmt is None  # datefmt is not supported
        ct = utime.localtime(record.created)
        return "{0}-{1}-{2} {3}:{4}:{5}".format(*ct)

    def formatException(self, exc_info):
        raise NotImplementedError()

    def formatStack(self, stack_info):
        raise NotImplementedError()

_level = INFO
_loggers = {}


def getLogger(name="root"):
    if name in _loggers:
        return _loggers[name]
    if name == "root":
        l = Logger(name)
        sh = StreamHandler()
        sh.formatter = Formatter()
        l.addHandler(sh)
    else:
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


def basicConfig(level=INFO, filename=None, stream=None, format=None, style="%"):
    global _level
    _level = level
    if filename:
        h = FileHandler(filename)
    else:
        h = StreamHandler(stream)
    h.setFormatter(Formatter(format, style=style))
    root = getLogger()
    root.handlers.clear()
    root.addHandler(h)
