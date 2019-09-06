import sys

class s:
   CYAN = str('\033[96m')
   BLUE = str('\033[94m')
   GREEN = str('\033[92m')
   YELLOW = str('\033[93m')
   RED = str('\033[91m')
   BOLD = str('\033[1m')
   WHITE = str('\033[37m')
   BLACK = str('\033[30m')
   ON_RED = str('\033[41m')
   MSG = str('\033[37m')
   NAME = str('\033[96m')
   END = str('\033[0m')


CRITICAL = 50
ERROR    = 40
WARNING  = 30
INFO     = 20
DEBUG    = 10
NOTSET   = 0

_nocolor_dict = {
    CRITICAL: "CRIT",
    ERROR: "ERROR",
    WARNING: "WARN",
    INFO: "INFO",
    DEBUG: "DEBUG",
}

_level_dict = {
    CRITICAL: s.ON_RED+s.BOLD+s.WHITE+"CRIT"+s.END,
    ERROR: s.BOLD+s.RED+"ERROR"+s.END,
    WARNING: s.BOLD+s.YELLOW+"WARN"+s.END,
    INFO: s.BLUE+"INFO"+s.END,
    DEBUG: s.GREEN+"DEBUG"+s.END,
}

_stream = sys.stderr

class Logger:

    level = NOTSET

    def __init__(self, name):
        self.name = s.NAME+name+s.END

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
        if level >= (self.level or _level):
            _stream.write("%s:%s:" % (self._level_str(level), self.name))
            if not args:
                print(s.MSG+msg+s.END, file=_stream)
            else:
                print(s.MSG+msg+s.END, file=_stream)

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

def basicConfig(level=INFO, filename=None, stream=None, format=None, color=False):
    global _level, _stream, _level_dict
    _level = level
    if stream:
        _stream = stream
    if not color:
        _level_dict = _nocolor_dict
        s.NAME, s.MSG = "", ""
    if filename is not None:
        print("logging.basicConfig: filename arg is not supported")
    if format is not None:
        print("logging.basicConfig: format arg is not supported")
