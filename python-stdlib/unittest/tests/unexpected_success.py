# @expectedFailure test that unexpectedly passes -> the run must exit non-zero.
# Not named "test_*.py" so discovery skips it; tools/ci.sh runs it explicitly.

import unittest


class TestUnexpectedSuccess(unittest.TestCase):
    @unittest.expectedFailure
    def test_unexpectedly_passes(self):
        self.assertEqual(1, 1)


if __name__ == "__main__":
    unittest.main()
