import sys

def format_tb(tb, limit):
    return ["traceback.format_tb() not implemented\n"]

def format_exception_only(type, value):
    return [repr(value) + "\n"]

def print_exception(t, e, tb, limit=None, file=None, chain=True):
    if file is None:
        file = sys.stdout
    sys.print_exception(e, file)

def print_exc(limit=None, file=None, chain=True):
    print_exception(*sys.exc_info(), limit=limit, file=file, chain=chain)
