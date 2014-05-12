import unittest

def run_unittest(*classes):
    for c in classes:
        unittest.run_class(c)
