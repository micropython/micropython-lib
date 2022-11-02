import unittest


class TestUnittestAssertions(unittest.TestCase):
    def testFail(self):
        with self.assertRaises(AssertionError):
            self.fail("failure")

    def testEqual(self):
        self.assertEqual(0, 0)
        self.assertEqual([0, 1, 2], [0, 1, 2])
        with self.assertRaises(AssertionError):
            self.assertEqual(0, None)
        with self.assertRaises(AssertionError):
            self.assertEqual([0, 1, 2], [1, 2, 3])

    def test_AlmostEqual(self):
        self.assertAlmostEqual(1.00000001, 1.0)
        self.assertNotAlmostEqual(1.0000001, 1.0)
        with self.assertRaises(AssertionError):
            self.assertAlmostEqual(1.0000001, 1.0)
        with self.assertRaises(AssertionError):
            self.assertNotAlmostEqual(1.00000001, 1.0)

        self.assertAlmostEqual(1.1, 1.0, places=0)
        with self.assertRaises(AssertionError):
            self.assertAlmostEqual(1.1, 1.0, places=1)

        self.assertAlmostEqual(0, 0.1 + 0.1j, places=0)
        self.assertNotAlmostEqual(0, 0.1 + 0.1j, places=1)
        with self.assertRaises(AssertionError):
            self.assertAlmostEqual(0, 0.1 + 0.1j, places=1)
        with self.assertRaises(AssertionError):
            self.assertNotAlmostEqual(0, 0.1 + 0.1j, places=0)

        self.assertAlmostEqual(float("inf"), float("inf"))
        with self.assertRaises(AssertionError):
            self.assertNotAlmostEqual(float("inf"), float("inf"))

    def test_AlmostEqualWithDelta(self):
        self.assertAlmostEqual(1.1, 1.0, delta=0.5)
        self.assertAlmostEqual(1.0, 1.1, delta=0.5)
        self.assertNotAlmostEqual(1.1, 1.0, delta=0.05)
        self.assertNotAlmostEqual(1.0, 1.1, delta=0.05)

        self.assertAlmostEqual(1.0, 1.0, delta=0.5)
        with self.assertRaises(AssertionError):
            self.assertNotAlmostEqual(1.0, 1.0, delta=0.5)
        with self.assertRaises(AssertionError):
            self.assertAlmostEqual(1.1, 1.0, delta=0.05)
        with self.assertRaises(AssertionError):
            self.assertNotAlmostEqual(1.1, 1.0, delta=0.5)
        with self.assertRaises(TypeError):
            self.assertAlmostEqual(1.1, 1.0, places=2, delta=2)
        with self.assertRaises(TypeError):
            self.assertNotAlmostEqual(1.1, 1.0, places=2, delta=2)

    def testNotEqual(self):
        self.assertNotEqual([0, 1, 2], [0, 2, 1])
        with self.assertRaises(AssertionError):
            self.assertNotEqual(0, 0)
        with self.assertRaises(AssertionError):
            self.assertNotEqual([0, 1, 2], [0, 1, 2])

    def testIs(self):
        self.assertIs(None, None)
        with self.assertRaises(AssertionError):
            self.assertIs([1, 2, 3], [1, 2, 3])

    def testIsNot(self):
        self.assertIsNot([1, 2, 3], [1, 2, 3])
        with self.assertRaises(AssertionError):
            self.assertIsNot(None, None)

    def testIsNone(self):
        self.assertIsNone(None)
        with self.assertRaises(AssertionError):
            self.assertIsNone(0)

    def testIsNotNone(self):
        self.assertIsNotNone(0)
        with self.assertRaises(AssertionError):
            self.assertIsNotNone(None)

    def testTrue(self):
        self.assertTrue(True)
        with self.assertRaises(AssertionError):
            self.assertTrue(False)

    def testFalse(self):
        self.assertFalse(False)
        with self.assertRaises(AssertionError):
            self.assertFalse(True)

    def testIn(self):
        self.assertIn("t", "cat")
        with self.assertRaises(AssertionError):
            self.assertIn("x", "cat")

    def testIsInstance(self):
        self.assertIsInstance("cat", str)
        with self.assertRaises(AssertionError):
            self.assertIsInstance(7, str)

    def testRaises(self):
        with self.assertRaises(ZeroDivisionError):
            1 / 0
            pass

    @unittest.skip("test of skipping")
    def testSkip(self):
        self.fail("this should be skipped")

    def testAssert(self):

        e1 = None
        try:

            def func_under_test(a):
                assert a > 10

            self.assertRaises(AssertionError, func_under_test, 20)
        except AssertionError as e:
            e1 = e

        if not e1 or "not raised" not in e1.args[0]:
            self.fail("Expected to catch lack of AssertionError from assert in func_under_test")

    @unittest.expectedFailure
    def testExpectedFailure(self):
        self.assertEqual(1, 0)

    def testExpectedFailureNot(self):
        @unittest.expectedFailure
        def testInner():
            self.assertEqual(1, 1)

        try:
            testInner()
        except:
            pass
        else:
            self.fail("Unexpected success was not detected")

    @unittest.skip("test because it was found to be failing out of the box.")
    def test_NotChangedByOtherTest(self):
        # TODO: This has been noticed to be failing from master, so added a skip and needs to be fixed in the future.
        global global_context
        assert global_context is None
        global_context = True

    def test_subtest_even(self):
        """
        Test that numbers between 0 and 5 are all even.
        """
        for i in range(0, 10, 2):
            with self.subTest("Should only pass for even numbers", i=i):
                self.assertEqual(i % 2, 0)

    def testAssertCountEqual(self):
        a = object()
        self.assertCountEqual([1, 2, 3], [3, 2, 1])
        self.assertCountEqual(["foo", "bar", "baz"], ["bar", "baz", "foo"])
        self.assertCountEqual([a, a, 2, 2, 3], (a, 2, 3, a, 2))
        self.assertCountEqual([1, "2", "a", "a"], ["a", "2", True, "a"])
        self.assertRaises(
            self.failureException, self.assertCountEqual, [1, 2] + [3] * 100, [1] * 100 + [2, 3]
        )
        self.assertRaises(
            self.failureException, self.assertCountEqual, [1, "2", "a", "a"], ["a", "2", True, 1]
        )
        self.assertRaises(self.failureException, self.assertCountEqual, [10], [10, 11])
        self.assertRaises(self.failureException, self.assertCountEqual, [10, 11], [10])
        self.assertRaises(self.failureException, self.assertCountEqual, [10, 11, 10], [10, 11])

        # Test that sequences of unhashable objects can be tested for sameness:
        self.assertCountEqual([[1, 2], [3, 4], 0], [False, [3, 4], [1, 2]])
        # Test that iterator of unhashable objects can be tested for sameness:
        self.assertCountEqual(iter([1, 2, [], 3, 4]), iter([1, 2, [], 3, 4]))

        # hashable types, but not orderable
        self.assertRaises(
            self.failureException, self.assertCountEqual, [], [divmod, "x", 1, 5j, 2j, frozenset()]
        )
        # comparing dicts
        self.assertCountEqual([{"a": 1}, {"b": 2}], [{"b": 2}, {"a": 1}])
        # comparing heterogeneous non-hashable sequences
        self.assertCountEqual([1, "x", divmod, []], [divmod, [], "x", 1])
        self.assertRaises(
            self.failureException, self.assertCountEqual, [], [divmod, [], "x", 1, 5j, 2j, set()]
        )
        self.assertRaises(self.failureException, self.assertCountEqual, [[1]], [[2]])

        # Same elements, but not same sequence length
        self.assertRaises(self.failureException, self.assertCountEqual, [1, 1, 2], [2, 1])
        self.assertRaises(
            self.failureException,
            self.assertCountEqual,
            [1, 1, "2", "a", "a"],
            ["2", "2", True, "a"],
        )
        self.assertRaises(
            self.failureException,
            self.assertCountEqual,
            [1, {"b": 2}, None, True],
            [{"b": 2}, True, None],
        )

        # Same elements which don't reliably compare, in
        # different order, see issue 10242
        a = [{2, 4}, {1, 2}]
        b = a[::-1]
        self.assertCountEqual(a, b)

        # test utility functions supporting assertCountEqual()

        diffs = set(unittest.TestCase()._count_diff_all_purpose("aaabccd", "abbbcce"))
        expected = {(3, 1, "a"), (1, 3, "b"), (1, 0, "d"), (0, 1, "e")}
        self.assertEqual(diffs, expected)

        diffs = unittest.TestCase()._count_diff_all_purpose([[]], [])
        self.assertEqual(diffs, [(1, 0, [])])

    def testAssertRaisesRegex(self):
        class ExceptionMock(Exception):
            pass

        def Stub():
            raise ExceptionMock("We expect")

        self.assertRaisesRegex(ExceptionMock, "expect$", Stub)

    def testAssertNotRaisesRegex(self):
        self.assertRaisesRegex(
            self.failureException,
            "^<class 'Exception'> not raised$",
            self.assertRaisesRegex,
            Exception,
            "x",
            lambda: None,
        )
        # NOTE: Chosen not to support a custom message.

    def testAssertRaisesRegexInvalidRegex(self):
        # Issue 20145.
        class MyExc(Exception):
            pass

        self.assertRaises(TypeError, self.assertRaisesRegex, MyExc, lambda: True)

    def testAssertRaisesRegexMismatch(self):
        def Stub():
            raise Exception("Unexpected")

        self.assertRaisesRegex(
            self.failureException,
            r'"\^Expected\$" does not match "Unexpected"',
            self.assertRaisesRegex,
            Exception,
            "^Expected$",
            Stub,
        )

    def testAssertRaisesRegexNoExceptionType(self):
        with self.assertRaises(TypeError):
            self.assertRaisesRegex()
        with self.assertRaises(TypeError):
            self.assertRaisesRegex(ValueError)
        with self.assertRaises(TypeError):
            self.assertRaisesRegex(1, "expect")
        with self.assertRaises(TypeError):
            self.assertRaisesRegex(object, "expect")
        with self.assertRaises(TypeError):
            self.assertRaisesRegex((ValueError, 1), "expect")
        with self.assertRaises(TypeError):
            self.assertRaisesRegex((ValueError, object), "expect")


if __name__ == "__main__":
    unittest.main()
