""" Test code for functools.total_ordering

Copyright © 2001-2023 Python Software Foundation.  All rights reserved.

This code was extracted from CPython v3.7.17 Lib/test/test_functools.py

This code is distributed under the Python Software License.
"""

import unittest

import functools

class TestTotalOrdering(unittest.TestCase):

    def test_total_ordering_lt(self):
        @functools.total_ordering
        class A:
            def __init__(self, value):
                self.value = value
            def __lt__(self, other):
                return self.value < other.value
            def __eq__(self, other):
                return self.value == other.value
        self.assertTrue(A(1) < A(2))
        self.assertTrue(A(2) > A(1))
        self.assertTrue(A(1) <= A(2))
        self.assertTrue(A(2) >= A(1))
        self.assertTrue(A(2) <= A(2))
        self.assertTrue(A(2) >= A(2))
        self.assertFalse(A(1) > A(2))

    def test_total_ordering_le(self):
        @functools.total_ordering
        class A:
            def __init__(self, value):
                self.value = value
            def __le__(self, other):
                return self.value <= other.value
            def __eq__(self, other):
                return self.value == other.value
        self.assertTrue(A(1) < A(2))
        self.assertTrue(A(2) > A(1))
        self.assertTrue(A(1) <= A(2))
        self.assertTrue(A(2) >= A(1))
        self.assertTrue(A(2) <= A(2))
        self.assertTrue(A(2) >= A(2))
        self.assertFalse(A(1) >= A(2))

    def test_total_ordering_gt(self):
        @functools.total_ordering
        class A:
            def __init__(self, value):
                self.value = value
            def __gt__(self, other):
                return self.value > other.value
            def __eq__(self, other):
                return self.value == other.value
        self.assertTrue(A(1) < A(2))
        self.assertTrue(A(2) > A(1))
        self.assertTrue(A(1) <= A(2))
        self.assertTrue(A(2) >= A(1))
        self.assertTrue(A(2) <= A(2))
        self.assertTrue(A(2) >= A(2))
        self.assertFalse(A(2) < A(1))

    def test_total_ordering_ge(self):
        @functools.total_ordering
        class A:
            def __init__(self, value):
                self.value = value
            def __ge__(self, other):
                return self.value >= other.value
            def __eq__(self, other):
                return self.value == other.value
        self.assertTrue(A(1) < A(2))
        self.assertTrue(A(2) > A(1))
        self.assertTrue(A(1) <= A(2))
        self.assertTrue(A(2) >= A(1))
        self.assertTrue(A(2) <= A(2))
        self.assertTrue(A(2) >= A(2))
        self.assertFalse(A(2) <= A(1))

# This test does not appear to work due to the lack of attributes on builtin types.
# This appears to lead to the comparison operators not being inherited by default.
#     def test_total_ordering_no_overwrite(self):
#         # new methods should not overwrite existing
#         import sys
#         @functools.total_ordering
#         class A(int):
#             pass
#         self.assertTrue(A(1) < A(2))
#         self.assertTrue(A(2) > A(1))
#         self.assertTrue(A(1) <= A(2))
#         self.assertTrue(A(2) >= A(1))
#         self.assertTrue(A(2) <= A(2))
#         self.assertTrue(A(2) >= A(2))

    def test_no_operations_defined(self):
        with self.assertRaises(ValueError):
            @functools.total_ordering
            class A:
                pass

    def test_type_error_when_not_implemented(self):
        # bug 10042; ensure stack overflow does not occur
        # when decorated types return NotImplemented
        @functools.total_ordering
        class ImplementsLessThan:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                if isinstance(other, ImplementsLessThan):
                    return self.value == other.value
                return False
            def __lt__(self, other):
                if isinstance(other, ImplementsLessThan):
                    return self.value < other.value
                return NotImplemented

        @functools.total_ordering
        class ImplementsGreaterThan:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                if isinstance(other, ImplementsGreaterThan):
                    return self.value == other.value
                return False
            def __gt__(self, other):
                if isinstance(other, ImplementsGreaterThan):
                    return self.value > other.value
                return NotImplemented

        @functools.total_ordering
        class ImplementsLessThanEqualTo:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                if isinstance(other, ImplementsLessThanEqualTo):
                    return self.value == other.value
                return False
            def __le__(self, other):
                if isinstance(other, ImplementsLessThanEqualTo):
                    return self.value <= other.value
                return NotImplemented

        @functools.total_ordering
        class ImplementsGreaterThanEqualTo:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                if isinstance(other, ImplementsGreaterThanEqualTo):
                    return self.value == other.value
                return False
            def __ge__(self, other):
                if isinstance(other, ImplementsGreaterThanEqualTo):
                    return self.value >= other.value
                return NotImplemented

        @functools.total_ordering
        class ComparatorNotImplemented:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                if isinstance(other, ComparatorNotImplemented):
                    return self.value == other.value
                return False
            def __lt__(self, other):
                return NotImplemented

        with self.subTest("LT < 1"), self.assertRaises(TypeError):
            ImplementsLessThan(-1) < 1

        with self.subTest("LT < LE"), self.assertRaises(TypeError):
            ImplementsLessThan(0) < ImplementsLessThanEqualTo(0)

        with self.subTest("LT < GT"), self.assertRaises(TypeError):
            ImplementsLessThan(1) < ImplementsGreaterThan(1)

        with self.subTest("LE <= LT"), self.assertRaises(TypeError):
            ImplementsLessThanEqualTo(2) <= ImplementsLessThan(2)

        with self.subTest("LE <= GE"), self.assertRaises(TypeError):
            ImplementsLessThanEqualTo(3) <= ImplementsGreaterThanEqualTo(3)

        with self.subTest("GT > GE"), self.assertRaises(TypeError):
            ImplementsGreaterThan(4) > ImplementsGreaterThanEqualTo(4)

        with self.subTest("GT > LT"), self.assertRaises(TypeError):
            ImplementsGreaterThan(5) > ImplementsLessThan(5)

        with self.subTest("GE >= GT"), self.assertRaises(TypeError):
            ImplementsGreaterThanEqualTo(6) >= ImplementsGreaterThan(6)

        with self.subTest("GE >= LE"), self.assertRaises(TypeError):
            ImplementsGreaterThanEqualTo(7) >= ImplementsLessThanEqualTo(7)

        with self.subTest("GE when equal"):
            a = ComparatorNotImplemented(8)
            b = ComparatorNotImplemented(8)
            self.assertEqual(a, b)
            with self.assertRaises(TypeError):
                a >= b

        with self.subTest("LE when equal"):
            a = ComparatorNotImplemented(9)
            b = ComparatorNotImplemented(9)
            self.assertEqual(a, b)
            with self.assertRaises(TypeError):
                a <= b

# Leaving pickle support for a later date
#    def test_pickle(self):
#        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
#            for name in '__lt__', '__gt__', '__le__', '__ge__':
#                with self.subTest(method=name, proto=proto):
#                    method = getattr(Orderable_LT, name)
#                    method_copy = pickle.loads(pickle.dumps(method, proto))
#                    self.assertIs(method_copy, method)

# @functools.total_ordering
# class Orderable_LT:
#     def __init__(self, value):
#         self.value = value
#     def __lt__(self, other):
#         return self.value < other.value
#     def __eq__(self, other):
#         return self.value == other.value

if __name__ == "__main__":
    unittest.main()

