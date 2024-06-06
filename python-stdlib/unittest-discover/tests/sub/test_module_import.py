import sys
import unittest


class TestModuleImport(unittest.TestCase):
    def test_ModuleImportPath(self):
        try:
            from sub.sub import imported
            assert imported
        except ImportError:
            print("This test is intended to be run with unittest discover"
                  "from the unittest-discover/tests dir. sys.path:", sys.path)
            raise
