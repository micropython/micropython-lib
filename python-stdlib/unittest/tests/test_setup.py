import collections
import helpers
import unittest


class _TestMethodCalls(
    collections.namedtuple(
        "TestMethodCalls", ("init", "setUpClass", "setUp", "test", "tearDown", "tearDownClass")
    )
):
    pass


class TestSetupTeardown(helpers.BaseTestCase):
    class TracingTestCase(unittest.TestCase):
        # NOTE: We are using/abusing the fact that we only use immutable types
        # (int, tuple, etc), and perform all of the mutations using `+=` to
        # track these method counts per subclass (as opposed to a global counter
        # on the super class).
        #
        # When we increment something with `+=`, it first tries to read the
        # current value, performs the mutation, then writes the value back. The
        # important thing here is that if the class variable has never been
        # assigned in a child class, it will read the value on the parent class.
        # The subsequent write will always happen on the child class.
        #
        # If we used a mutable type here (eg, list), we would mutate underlying
        # list in the parent class.
        init_called_times: int = 0
        setup_class_called_times: int = 0
        setup_called_times: int = 0
        test_called_times: int = 0
        teardown_called_times: int = 0
        teardown_class_called_times: int = 0
        method_call_order: tuple[str, ...] = ()

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            cls = self.__class__
            cls.init_called_times += 1
            cls.method_call_order += ("__init__",)

        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            cls.setup_class_called_times += 1
            cls.method_call_order += ("setUpClass",)

        def setUp(self):
            super().setUp()
            cls = self.__class__
            cls.setup_called_times += 1
            cls.method_call_order += ("setUp",)

        def test(self):
            cls = self.__class__
            cls.test_called_times += 1
            cls.method_call_order += ("test",)

        def tearDown(self):
            super().tearDown()
            cls = self.__class__
            cls.teardown_called_times += 1
            cls.method_call_order += ("tearDown",)

        @classmethod
        def tearDownClass(cls):
            super().tearDownClass()
            cls.teardown_class_called_times += 1
            cls.method_call_order += ("tearDownClass",)

    def assertTestMethodCountsEqual(
        self,
        test_case: type[TracingTestCase],
        *,
        init: int,
        setUpClass: int,
        setUp: int,
        test: int,
        tearDown: int,
        tearDownClass: int,
    ):
        actual = _TestMethodCalls(
            test_case.init_called_times,
            test_case.setup_class_called_times,
            test_case.setup_called_times,
            test_case.test_called_times,
            test_case.teardown_called_times,
            test_case.teardown_class_called_times,
        )
        expected = _TestMethodCalls(init, setUpClass, setUp, test, tearDown, tearDownClass)
        self.assertEqual(actual, expected)

    def test_simple(self):
        class Test(self.__class__.TracingTestCase):
            pass

        result, output = helpers.run_tests_in_testcase(self, Test)
        self.assertTestResult(result, testsRun=1, numFailures=0, numErrors=0, numSkipped=0)
        self.assertTestMethodCountsEqual(
            Test, init=1, setUpClass=1, setUp=1, test=1, tearDown=1, tearDownClass=1
        )
        self.assertEqual(output, f"test ({self.full_test_name()}.Test) ... ok\n")

    def test_multiple_tests(self):
        class Test(self.__class__.TracingTestCase):
            def test(self):
                super().test()

            test2 = test

        result, output = helpers.run_tests_in_testcase(self, Test)
        self.assertTestResult(result, testsRun=2, numFailures=0, numErrors=0, numSkipped=0)
        self.assertTestMethodCountsEqual(
            Test, init=1, setUpClass=1, setUp=2, test=2, tearDown=2, tearDownClass=1
        )
        self.assertEqual(
            output,
            f"test ({self.full_test_name()}.Test) ... ok\n"
            f"test2 ({self.full_test_name()}.Test) ... ok\n",
        )

    @unittest.skip("Exceptions/Assertions in setUp are not caught")
    def test_setup_failure_skips_test(self):
        class Test(self.__class__.TracingTestCase):
            def setUp(self):
                super().setUp()
                raise AssertionError

        result, output = helpers.run_tests_in_testcase(self, Test)
        self.assertTestResult(result, testsRun=1, numFailures=1, numErrors=0, numSkipped=0)
        self.assertTestMethodCountsEqual(
            Test, init=1, setUpClass=1, setUp=1, test=0, tearDown=0, tearDownClass=1
        )
        self.assertEqual(output, f"test ({self.full_test_name()}.Test) ... FAIL\n")

    @unittest.skip("Exceptions/Assertions in setUp are not caught")
    def test_setup_errors_skips_test(self):
        class Test(self.__class__.TracingTestCase):
            def setUp(self):
                super().setUp()
                raise ValueError

        result, output = helpers.run_tests_in_testcase(self, Test)
        self.assertTestResult(result, testsRun=1, numFailures=0, numErrors=1, numSkipped=0)
        self.assertTestMethodCountsEqual(
            Test, init=1, setUpClass=1, setUp=1, test=0, tearDown=0, tearDownClass=1
        )
        self.assertEqual(output, f"test ({self.full_test_name()}.Test) ... ERROR\n")

    @unittest.skip("Exceptions/Assertions in setUp are not caught")
    def test_setup_skiptest_skips_test(self):
        class Test(self.__class__.TracingTestCase):
            def setUp(self):
                super().setUp()
                self.skipTest("reason1")

        result, output = helpers.run_tests_in_testcase(self, Test)
        self.assertTestResult(result, testsRun=1, numFailures=0, numErrors=0, numSkipped=1)
        self.assertTestMethodCountsEqual(
            Test, init=1, setUpClass=1, setUp=1, test=0, tearDown=0, tearDownClass=1
        )
        self.assertEqual(output, f"test ({self.full_test_name()}.Test) ... skipped: reason1\n")

    @unittest.skip("Exceptions/Assertions in setUp are not caught")
    def test_class_setup_failure_skips_test(self):
        class Test(self.__class__.TracingTestCase):
            @classmethod
            def setUpClass(cls):
                super().setUpClass()
                raise AssertionError

        result, output = helpers.run_tests_in_testcase(self, Test)
        self.assertTestResult(result, testsRun=0, numFailures=0, numErrors=1, numSkipped=0)
        self.assertTestMethodCountsEqual(
            Test, init=1, setUpClass=1, setUp=0, test=0, tearDown=0, tearDownClass=0
        )
        self.assertEqual(output, f"setUpClass ({self.full_test_name()}.Test) ... FAIL\n")

    @unittest.skip("Exceptions/Assertions in setUp are not caught")
    def test_class_setup_errors_skips_test(self):
        class Test(self.__class__.TracingTestCase):
            @classmethod
            def setUpClass(cls):
                super().setUpClass()
                raise ValueError

        result, output = helpers.run_tests_in_testcase(self, Test)
        self.assertTestResult(result, testsRun=0, numFailures=0, numErrors=1, numSkipped=0)
        self.assertTestMethodCountsEqual(
            Test, init=1, setUpClass=1, setUp=0, test=0, tearDown=0, tearDownClass=0
        )
        self.assertEqual(output, f"setUpClass ({self.full_test_name()}.Test) ... ERROR\n")

    @unittest.skip("Exceptions/Assertions in setUp are not caught")
    def test_class_setup_skiptest_skips_test(self):
        class Test(self.__class__.TracingTestCase):
            @classmethod
            def setUpClass(cls):
                super().setUpClass()
                self.skipTest("reason1")

        result, output = helpers.run_tests_in_testcase(self, Test)
        self.assertTestResult(result, testsRun=0, numFailures=0, numErrors=0, numSkipped=1)
        self.assertTestMethodCountsEqual(
            Test, init=1, setUpClass=1, setUp=0, test=0, tearDown=0, tearDownClass=0
        )
        self.assertEqual(
            output, f"setUpClass ({self.full_test_name()}.Test) ... skipped: reason1\n"
        )

    @unittest.skip("Exceptions/Assertions in setUp are not caught")
    def test_teardown_failure_is_failure(self):
        class Test(self.__class__.TracingTestCase):
            def tearDown(self):
                super().tearDown()
                raise AssertionError

        result, output = helpers.run_tests_in_testcase(self, Test)
        self.assertTestResult(result, testsRun=1, numFailures=1, numErrors=0, numSkipped=0)
        self.assertTestMethodCountsEqual(
            Test, init=1, setUpClass=1, setUp=1, test=1, tearDown=1, tearDownClass=1
        )
        self.assertEqual(output, f"test ({self.full_test_name()}.Test) ... FAIL\n")

    @unittest.skip("Exceptions/Assertions in setUp are not caught")
    def test_teardown_errors_are_errors(self):
        class Test(self.__class__.TracingTestCase):
            def tearDown(self):
                super().tearDown()
                raise ValueError

        result, output = helpers.run_tests_in_testcase(self, Test)
        self.assertTestResult(result, testsRun=1, numFailures=0, numErrors=1, numSkipped=0)
        self.assertTestMethodCountsEqual(
            Test, init=1, setUpClass=1, setUp=1, test=1, tearDown=1, tearDownClass=1
        )
        self.assertEqual(output, f"test ({self.full_test_name()}.Test) ... ERROR\n")

    @unittest.skip("Exceptions/Assertions in setUp are not caught")
    def test_teardown_skiptest_is_skip(self):
        class Test(self.__class__.TracingTestCase):
            def tearDown(self):
                super().tearDown()
                self.skipTest("reason1")

        result, output = helpers.run_tests_in_testcase(self, Test)
        self.assertTestResult(result, testsRun=1, numFailures=0, numErrors=0, numSkipped=1)
        self.assertTestMethodCountsEqual(
            Test, init=1, setUpClass=1, setUp=1, test=1, tearDown=1, tearDownClass=1
        )
        self.assertEqual(output, f"test ({self.full_test_name()}.Test) ... skipped: reason1\n")

    def test_setup_teardown_ordering(self):
        class Test(self.__class__.TracingTestCase):
            def test(self):
                super().test()

            test2 = test

        result, output = helpers.run_tests_in_testcase(self, Test)
        self.assertTestResult(result, testsRun=2, numFailures=0, numErrors=0, numSkipped=0)
        self.assertEqual(
            Test.method_call_order,
            (
                "__init__",
                # NOTE: CPython calls __init__ here a second time
                "setUpClass",
                "setUp",
                "test",
                "tearDown",
                "setUp",
                "test",
                "tearDown",
                "tearDownClass",
            ),
        )
        self.assertTrue(result.wasSuccessful())
        self.assertEqual(
            output,
            f"test ({self.full_test_name()}.Test) ... ok\n"
            f"test2 ({self.full_test_name()}.Test) ... ok\n",
        )


if __name__ == "__main__":
    unittest.main()
