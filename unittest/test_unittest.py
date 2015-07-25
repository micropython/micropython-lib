import unittest

class TestUnittestAssertions(unittest.TestCase):

    def testFail(self):
        with self.assertRaises(AssertionError):
            self.fail('failure')

    def testEqual(self):
        self.assertEqual(0,0)
        self.assertEqual([0,1,2], [0,1,2])
        with self.assertRaises(AssertionError):
            self.assertEqual(0,None)
        with self.assertRaises(AssertionError):
            self.assertEqual([0,1,2], [1,2,3])

    def testNotEqual(self):
        self.assertNotEqual([0,1,2], [0,2,1])
        with self.assertRaises(AssertionError):
            self.assertNotEqual(0,0)
        with self.assertRaises(AssertionError):
            self.assertNotEqual([0,1,2], [0,1,2])

    def testIs(self):
        self.assertIs(None, None)
        with self.assertRaises(AssertionError):
            self.assertIs([1,2,3], [1,2,3])

    def testIsNot(self):
        self.assertIsNot([1,2,3], [1,2,3])
        with self.assertRaises(AssertionError):
            self.assertIsNot(None, None)

    def testTrue(self):
        self.assertTrue(True)
        with self.assertRaises(AssertionError):
            self.assertTrue(False)

    def testFalse(self):
        self.assertFalse(False)
        with self.assertRaises(AssertionError):
            self.assertFalse(True)

    def testIn(self):
        self.assertIn('t', 'cat')
        with self.assertRaises(AssertionError):
            self.assertIn('x', 'cat')

    def testIsInstance(self):
        self.assertIsInstance('cat', str)
        with self.assertRaises(AssertionError):
            self.assertIsInstance(7, str)

    def testRaises(self):
        with self.assertRaises(ZeroDivisionError):
            1/0
            pass

    @unittest.skip('test of skipping')
    def testSkip(self):
        self.assertFail('this should be skipped')

if __name__ == '__main__':
    unittest.main()
