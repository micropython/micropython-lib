import unittest


TESTFN = '@test'

def run_unittest(*classes):
    suite = unittest.TestSuite()
    for c in classes:
        suite.addTest(c)
    runner = unittest.TestRunner()
    result = runner.run(suite)
    msg = "Ran %d tests" % result.testsRun
    if result.skippedNum > 0:
        msg += " (%d skipped)" % result.skippedNum
    print(msg)

def can_symlink():
    return False

def skip_unless_symlink(test):
    """Skip decorator for tests that require functional symlink"""
    ok = can_symlink()
    msg = "Requires functional symlink implementation"
    return test if ok else unittest.skip(msg)(test)

def create_empty_file(name):
    open(name, "w").close()
