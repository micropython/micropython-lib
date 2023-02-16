"""Tests using unittest.subtest as an example reference for how it is used"""

import unittest


def factorial(value: int) -> int:
    """Iterative factorial algorithm implementation"""
    result = 1

    for i in range(1, value + 1):
        result *= i

    return result


class Person:
    """Represents a person with a name, age, and who can make friends"""

    def __init__(self, name: str, age: int) -> None:
        self.name = name
        self.age = age
        self.friends = set()

    def __repr__(self) -> str:
        return f"Person({self.name})"

    def add_friend(self, friend):
        """Logs that this Person has made a new friend"""
        self.friends.add(friend)

    def has_friend(self, friend_candidate) -> bool:
        """Determines if this Person has the friend `friend_candidate`"""
        return friend_candidate in self.friends

    def is_oldest_friend(self) -> bool:
        """Determines whether this Person is the oldest out of themself and their friends"""
        return self.age > max(friend.age for friend in self.friends)


class TestSubtest(unittest.TestCase):
    """Examples/tests of unittest.subTest()"""

    def test_sorted(self) -> None:
        """Test that the selection sort function correctly sorts lists"""
        tests = [
            {
                "unsorted": [-68, 15, 52, -54, -64, 20, 2, 66, 33],
                "sorted": [-68, -64, -54, 2, 15, 20, 33, 52, 66],
                "correct": True,
            },
            {
                "unsorted": [-68, 15, 52, -54, -64, 20, 2, 66, 33],
                "sorted": [-68, -54, -64, 2, 15, 20, 33, 52, 66],
                "correct": False,
            },
            {
                "unsorted": [-68, 15, 52, 54, -64, 20, 2, 66, 33],
                "sorted": [-68, -64, -54, 2, 15, 20, 33, 52, 66],
                "correct": False,
            },
            {
                "unsorted": [],
                "sorted": [],
                "correct": True,
            },
            {
                "unsorted": [42],
                "sorted": [42],
                "correct": True,
            },
            {
                "unsorted": [42],
                "sorted": [],
                "correct": False,
            },
            {
                "unsorted": [],
                "sorted": [24],
                "correct": False,
            },
            {
                "unsorted": [43, 44],
                "sorted": [43, 44],
                "correct": True,
            },
            {
                "unsorted": [44, 43],
                "sorted": [43, 44],
                "correct": True,
            },
        ]

        for test in tests:
            with self.subTest():  # Subtests continue to be tested, even if an earlier one fails
                if test["correct"]:  # Tests that match what is expected
                    self.assertEqual(sorted(test["unsorted"]), test["sorted"])
                else:  # Tests that are meant to fail
                    with self.assertRaises(AssertionError):
                        self.assertEqual(sorted(test["unsorted"]), test["sorted"])

    def test_factorial(self) -> None:
        """Test that the factorial fuction correctly calculates factorials

        Makes use of `msg` argument in subtest method to clarify which subtests had an
        error in the results
        """
        tests = [
            {
                "operand": 0,
                "result": 1,
                "correct": True,
            },
            {
                "operand": 1,
                "result": 1,
                "correct": True,
            },
            {
                "operand": 1,
                "result": 0,
                "correct": False,
            },
            {
                "operand": 2,
                "result": 2,
                "correct": True,
            },
            {
                "operand": 3,
                "result": 6,
                "correct": True,
            },
            {
                "operand": 3,
                "result": -6,
                "correct": False,
            },
            {
                "operand": 4,
                "result": 24,
                "correct": True,
            },
            {
                "operand": 15,
                "result": 1_307_674_368_000,
                "correct": True,
            },
            {
                "operand": 15,
                "result": 1_307_674_368_001,
                "correct": False,
            },
            {
                "operand": 11,
                "result": 39_916_800,
                "correct": True,
            },
        ]

        for test in tests:
            with self.subTest(
                f"{test['operand']}!"
            ):  # Let's us know we were testing "x!" when we get an error
                if test["correct"]:
                    self.assertEqual(factorial(test["operand"]), test["result"])
                else:
                    with self.assertRaises(AssertionError):
                        self.assertEqual(factorial(test["operand"]), test["result"])

    def test_person(self) -> None:
        """Test the Person class and its friend-making ability

        Makes use of subtest's params to specify relevant data about the tests, which is
        helpful for debugging
        """
        # Create a friendship
        alice = Person("Alice", 22)
        bob = Person("Bob", 23)
        alice.add_friend(bob)

        # Test friendship init
        with self.subTest(
            "Alice should have Bob as a friend", name=alice.name, friends=bob.friends
        ):  # Params `name` and `friends` provide useful data for debugging purposes
            self.assertTrue(alice.has_friend(bob))

        with self.subTest(
            "Bob should not have Alice as a friend", name=bob.name, friends=bob.friends
        ):
            self.assertFalse(bob.has_friend(alice))

        # Friendship is not always  commutative, so Bob is not implicitly friends with Alice
        with self.subTest("Alice and Bob should not both be friends with eachother"):
            with self.assertRaises(AssertionError):
                self.assertTrue(bob.has_friend(alice) and alice.has_friend(bob))

        # Bob becomes friends with Alice
        bob.add_friend(alice)

        with self.subTest(
            "Bob should now have Alice as a friend", name=bob.name, friends=bob.friends
        ):
            self.assertTrue(bob.has_friend(alice))

        with self.subTest(
            "Bob should be the oldest of his friends",
            age=bob.age,
            friend_ages=[friend.age for friend in bob.friends],
        ):  # Different params can be used for different subtests in the same test
            self.assertTrue(bob.is_oldest_friend())


if __name__ == "__main__":
    unittest.main()
