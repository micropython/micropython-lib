import unittest


TESTFN = '@test'

def run_unittest(*classes):
    for c in classes:
        unittest.run_class(c)

def can_symlink():
    return False

def skip_unless_symlink(test):
    """Skip decorator for tests that require functional symlink"""
    ok = can_symlink()
    msg = "Requires functional symlink implementation"
    return test if ok else unittest.skip(msg)(test)

def create_empty_file(name):
    open(name, "w").close()
