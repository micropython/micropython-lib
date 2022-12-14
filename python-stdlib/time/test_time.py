import time
import unittest

DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)

TIME_TUPLE = (2022, 12, 14, 0, 45, 17, 2, 348, 0)


class TestStrftime(unittest.TestCase):
    def test_not_formatting(self):
        fmt = "a string with no formatting {}[]() 0123456789 !@#$^&*"
        self.assertEqual(time.strftime(fmt, TIME_TUPLE), fmt)

    def test_days(self):
        for i, day in enumerate(DAYS):
            t = (0, 0, 0, 0, 0, 0, i, 0, 0)
            self.assertEqual(time.strftime("%a%A", t), day[:3] + day)

    def test_months(self):
        for i, month in enumerate(MONTHS):
            t = (0, i + 1, 0, 0, 0, 0, 0, 0, 0)
            self.assertEqual(time.strftime("%b%B", t), month[:3] + month)

    def test_full(self):
        fmt = "%Y-%m-%d %a %b %I:%M:%S %%%P%%"
        expected = "2022-12-14 Wed Dec 00:45:17 %AM%"
        self.assertEqual(time.strftime(fmt, TIME_TUPLE), expected)
