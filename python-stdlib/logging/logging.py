from micropython import const
import io
import sys
import time

CRITICAL = const(50)
ERROR = const(40)
WARNING = const(30)
INFO = const(20)
DEBUG = const(10)
NOTSET = const(0)

_DEFAULT_LEVEL = const(WARNING)

_level_dict = {
    CRITICAL: "CRITICAL",
    ERROR: "ERROR",
    WARNING: "WARNING",
    INFO: "INFO",
    DEBUG: "DEBUG",
    NOTSET: "NOTSET",
}

_loggers = {}
_stream = sys.stderr
_default_fmt = "%(levelname)s:%(name)s:%(message)s"
_default_datefmt = "%Y-%m-%d %H:%M:%S"


class LogRecord:
    def __init__(self, name, level, message, extra=None):
        self.name = name
        self.levelno = level
        self.levelname = _level_dict[level]
        self.message = message
        self.ct = time.time()
        self.msecs = int((self.ct - int(self.ct)) * 1000)
        self.asctime = None
        if extra is not None:
            for key in extra:
                if (key in ["message", "asctime"]) or (key in self.__dict__):
                    raise KeyError("Attempt to overwrite %r in LogRecord" % key)
                setattr(self, key, extra[key])


class Handler:
    def __init__(self, level=NOTSET):
        self.level = level
        self.formatter = None

    def close(self):
        pass

    def setLevel(self, level):
        self.level = level

    def setFormatter(self, formatter):
        self.formatter = formatter

    def format(self, record):
        return self.formatter.format(record)


class StreamHandler(Handler):
    def __init__(self, stream=None):
        super().__init__()
        self.stream = _stream if stream is None else stream
        self.terminator = "\n"

    def close(self):
        if hasattr(self.stream, "flush"):
            self.stream.flush()

    def emit(self, record):
        if record.levelno >= self.level:
            self.stream.write(self.format(record) + self.terminator)


class FileHandler(StreamHandler):
    def __init__(self, filename, mode="a", encoding="UTF-8"):
        super().__init__(stream=open(filename, mode=mode, encoding=encoding))

    def close(self):
        super().close()
        self.stream.close()


class Formatter:
    def __init__(self, fmt=None, datefmt=None):
        self.fmt = _default_fmt if fmt is None else fmt
        self.datefmt = _default_datefmt if datefmt is None else datefmt

    def usesTime(self):
        return "asctime" in self.fmt

    def formatTime(self, datefmt, record):
        if hasattr(time, "strftime"):
            return time.strftime(datefmt, time.localtime(record.ct))
        return None

    def format(self, record):
        if self.usesTime():
            record.asctime = self.formatTime(self.datefmt, record)
        return self.fmt % {
            "name": record.name,
            "message": record.message,
            "msecs": record.msecs,
            "asctime": record.asctime,
            "levelname": record.levelname,
        }


class Logger:
    def __init__(self, name, level=NOTSET):
        self.name = name
        self.level = level
        self.handlers = []

    def setLevel(self, level):
        self.level = level

    def isEnabledFor(self, level):
        return level >= self.getEffectiveLevel()

    def getEffectiveLevel(self):
        return self.level or getLogger().level or _DEFAULT_LEVEL

    def log(self, level, msg, *args, exc_info=False, extra=None):
        if self.isEnabledFor(level):
            if args:
                if isinstance(args[0], dict):
                    args = args[0]
                msg = msg % args
            record = LogRecord(self.name, level, msg, extra)
            handlers = self.handlers
            if not handlers:
                handlers = getLogger().handlers
            for h in handlers:
                h.emit(record)

        tb = None
        if isinstance(exc_info, BaseException):
            tb = exc_info
        elif hasattr(sys, "exc_info"):
            tb = sys.exc_info()[1]
        if tb:
            buf = io.StringIO()
            sys.print_exception(tb, buf)
            self.log(ERROR, buf.getvalue())

    def debug(self, msg, *args, **kwargs):
        self.log(DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.log(INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.log(WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.log(ERROR, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.log(CRITICAL, msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self.log(ERROR, msg, *args, **kwargs)

    def addHandler(self, handler):
        self.handlers.append(handler)

    def hasHandlers(self):
        return len(self.handlers) > 0


def getLogger(name=None):
    if name is None:
        name = "root"
    if name not in _loggers:
        _loggers[name] = Logger(name)
        if name == "root":
            basicConfig()
    return _loggers[name]


def log(level, msg, *args, **kwargs):
    getLogger().log(level, msg, *args, **kwarg)


def debug(msg, *args, **kwargs):
    getLogger().debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    getLogger().info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    getLogger().warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    getLogger().error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    getLogger().critical(msg, *args, **kwargs)


def exception(msg, *args, exc_info=True, **kwargs):
    getLogger().exception(msg, *args, exc_info=exc_info, **kwargs)


def shutdown():
    for k, logger in _loggers.items():
        for h in logger.handlers:
            h.close()
        _loggers.pop(logger, None)


def addLevelName(level, name):
    _level_dict[level] = name


def basicConfig(
    filename=None,
    filemode="a",
    format=None,
    datefmt=None,
    level=WARNING,
    stream=None,
    encoding="UTF-8",
    force=False,
):
    if "root" not in _loggers:
        _loggers["root"] = Logger("root")

    logger = _loggers["root"]

    if force or not logger.handlers:
        for h in logger.handlers:
            h.close()
        logger.handlers = []

        if filename is None:
            handler = StreamHandler(stream)
        else:
            handler = FileHandler(filename, filemode, encoding)

        handler.setLevel(level)
        handler.setFormatter(Formatter(format, datefmt))

        logger.setLevel(level)
        logger.addHandler(handler)


if hasattr(sys, "atexit"):
    sys.atexit(shutdown)
