# Dummy file to preclude import errors
# Should be reimplemented for MicroPython
# Reason:
# Basic, useful module, by CPython impl depends on module "string" which
# uses metaclasses.

CRITICAL = 50
ERROR    = 40
WARNING  = 30
INFO     = 20
DEBUG    = 10
NOTSET   = 0

_level_dict = {
    CRITICAL: "CRIT",
    ERROR: "ERROR",
    WARNING: "WARN",
    INFO: "INFO",
    DEBUG: "DEBUG",
}

class Logger:

    def __init__(self, name):
        self.level = NOTSET
        self.name = name

    def _level_str(self, level):
        if level in _level_dict:
            return _level_dict[level]
        return "LVL" + str(level)

    def log(self, level, msg, *args):
        if level >= (self.level or _level):
            print(("%s:%s:" + msg) % ((self._level_str(level), self.name) + args))

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


_level = INFO
_loggers = {}

def getLogger(name):
    if name in _loggers:
        return _loggers[name]
    l = Logger(name)
    _loggers[name] = l
    return l

def info(msg, *args):
    getLogger(None).info(msg, *args)

def debug(msg, *args):
    getLogger(None).debug(msg, *args)

def basicConfig(level=INFO, filename=None, format=None):
    global _level
    _level = level
    if filename is not None:
        print("logging.basicConfig: filename arg is not supported")
    if format is not None:
        print("logging.basicConfig: format arg is not supported")
