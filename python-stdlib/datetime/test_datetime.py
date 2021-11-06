# See https://github.com/python/cpython/blob/3.9/Lib/test/datetimetester.py
import unittest
from datetime import timedelta as td, timezone as tz, datetime as dt, fromisoformat as fif


### timedelta ################################################################

a = td(hours=7)
b = td(minutes=6)
c = td(seconds=10)
ns = td(nanoseconds=1)
t1 = td(2, 3, 4)
t2 = td(2, 3, 4)
t3 = td(2, 3, 5)


class TestTimeDelta(unittest.TestCase):
    def test_constructor01(self):
        self.assertEqual(td(), td(weeks=0, days=0, hours=0, minutes=0, seconds=0))

    def test_constructor02(self):
        self.assertEqual(td(weeks=1), td(days=7))

    def test_constructor03(self):
        self.assertEqual(td(days=1), td(hours=24))

    def test_constructor04(self):
        self.assertEqual(td(hours=1), td(minutes=60))

    def test_constructor05(self):
        self.assertEqual(td(minutes=1), td(seconds=60))

    def test_constructor06(self):
        self.assertEqual(td(seconds=1), td(milliseconds=1000))

    def test_constructor07(self):
        self.assertEqual(td(milliseconds=1), td(microseconds=1000))

    def test_constructor08(self):
        self.assertEqual(td(microseconds=1), td(nanoseconds=1000))

    def test_constructor09(self):
        self.assertEqual(td(weeks=1.0 / 7), td(days=1))

    def test_constructor10(self):
        self.assertEqual(td(days=1.0 / 24), td(hours=1))

    def test_constructor11(self):
        self.assertEqual(td(hours=1.0 / 60), td(minutes=1))

    def test_constructor12(self):
        self.assertEqual(td(minutes=1.0 / 60), td(seconds=1))

    def test_constructor13(self):
        self.assertEqual(td(seconds=0.001), td(milliseconds=1))

    def test_constructor14(self):
        self.assertEqual(td(milliseconds=0.001), td(microseconds=1))

    def test_constructor15(self):
        self.assertEqual(td(microseconds=0.001), td(nanoseconds=1))

    def test_constant01(self):
        self.assertTrue(td(0, 0, 0, 365 * td.MINYEAR).total_seconds() >= -(2 ** 63) / 10 ** 9)

    def test_constant02(self):
        self.assertFalse(
            td(0, 0, 0, 365 * (td.MINYEAR - 1)).total_seconds() >= -(2 ** 63) / 10 ** 9
        )

    def test_constant03(self):
        self.assertTrue(
            td(23, 59, 59, 365 * td.MAXYEAR).total_seconds() <= (2 ** 63 - 1) / 10 ** 9
        )

    def test_constant04(self):
        self.assertFalse(
            td(23, 59, 59, 365 * (td.MAXYEAR + 1)).total_seconds() <= (2 ** 63 - 1) / 10 ** 9
        )

    def test_computation01(self):
        self.assertEqual(a + b + c, td(7, 6, 10))

    def test_computation02(self):
        self.assertEqual(a - b, td(6, 60 - 6))

    def test_computation03(self):
        self.assertEqual(-a, td(-7))

    def test_computation04(self):
        self.assertEqual(+a, td(7))

    def test_computation05(self):
        self.assertEqual(-b, td(-1, 54))

    def test_computation06(self):
        self.assertEqual(-c, td(-1, 59, 50))

    def test_computation07(self):
        self.assertEqual(abs(a), a)

    def test_computation08(self):
        self.assertEqual(abs(-a), a)

    def test_computation09(self):
        self.assertEqual(td(6, 60), a)

    def test_computation10(self):
        self.assertEqual(td(0, 0, 60 * 6), b)

    def test_computation11(self):
        self.assertEqual(a * 10, td(70))

    def test_computation12(self):
        self.assertEqual(a * 10, 10 * a)

    def test_computation13(self):
        self.assertEqual(a * 10, 10 * a)

    def test_computation14(self):
        self.assertEqual(b * 10, td(0, 60))

    def test_computation15(self):
        self.assertEqual(10 * b, td(0, 60))

    def test_computation16(self):
        self.assertEqual(c * 10, td(0, 0, 100))

    def test_computation17(self):
        self.assertEqual(10 * c, td(0, 0, 100))

    def test_computation18(self):
        self.assertEqual(a * -1, -a)

    def test_computation19(self):
        self.assertEqual(b * -2, -b - b)

    def test_computation20(self):
        self.assertEqual(c * -2, -c + -c)

    def test_computation21(self):
        self.assertEqual(b * (60 * 24), (b * 60) * 24)

    def test_computation22(self):
        self.assertEqual(b * (60 * 24), (60 * b) * 24)

    def test_computation23(self):
        self.assertEqual(c * 6, td(0, 1))

    def test_computation24(self):
        self.assertEqual(6 * c, td(0, 1))

    def test_computation25(self):
        self.assertEqual(a // 7, td(1))

    def test_computation26(self):
        self.assertEqual(b // 6, td(0, 1))

    def test_computation27(self):
        self.assertEqual(c // 10, td(0, 0, 1))

    def test_computation28(self):
        self.assertEqual(a // 10, td(0, 7 * 6))

    def test_computation29(self):
        self.assertEqual(a // 3600, td(0, 0, 7))

    def test_computation30(self):
        self.assertEqual(a / 0.5, td(14))

    def test_computation31(self):
        self.assertEqual(b / 0.5, td(0, 12))

    def test_computation32(self):
        self.assertEqual(a / 7, td(1))

    def test_computation33(self):
        self.assertEqual(b / 6, td(0, 1))

    def test_computation34(self):
        self.assertEqual(c / 10, td(0, 0, 1))

    def test_computation35(self):
        self.assertEqual(a / 10, td(0, 7 * 6))

    def test_computation36(self):
        self.assertEqual(a / 3600, td(0, 0, 7))

    def test_computation37(self):
        self.assertEqual((3 * ns) * 0.5, 2 * ns)

    def test_computation38(self):
        self.assertEqual((5 * ns) * 0.5, 2 * ns)

    def test_computation39(self):
        self.assertEqual(0.5 * (3 * ns), 2 * ns)

    def test_computation40(self):
        self.assertEqual(0.5 * (5 * ns), 2 * ns)

    def test_computation41(self):
        self.assertEqual((-3 * ns) * 0.5, -2 * ns)

    def test_computation42(self):
        self.assertEqual((-5 * ns) * 0.5, -2 * ns)

    def test_computation43(self):
        self.assertEqual((3 * ns) / 2, 2 * ns)

    def test_computation44(self):
        self.assertEqual((5 * ns) / 2, 2 * ns)

    def test_computation45(self):
        self.assertEqual((-3 * ns) / 2.0, -2 * ns)

    def test_computation46(self):
        self.assertEqual((-5 * ns) / 2.0, -2 * ns)

    def test_computation47(self):
        self.assertEqual((3 * ns) / -2, -2 * ns)

    def test_computation48(self):
        self.assertEqual((5 * ns) / -2, -2 * ns)

    def test_computation49(self):
        self.assertEqual((3 * ns) / -2.0, -2 * ns)

    def test_computation50(self):
        self.assertEqual((5 * ns) / -2.0, -2 * ns)

    def test_computation51(self):
        for i in range(-10, 10):
            # with self.subTest(i=i): not supported by Micropython
                self.assertEqual((i * ns / 3) // ns, round(i / 3))

    def test_computation52(self):
        for i in range(-10, 10):
            # with self.subTest(i=i): not supported by Micropython
                self.assertEqual((i * ns / -3) // ns, round(i / -3))

    def test_total_seconds(self):
        d = td(days=365)
        self.assertEqual(d.total_seconds(), 31536000.0)

    def test_carries(self):
        t1 = td(
            days=100,
            weeks=-7,
            hours=-24 * (100 - 49),
            minutes=-3,
            seconds=3 * 60 + 1,
        )
        t2 = td(seconds=1)
        self.assertEqual(t1, t2)

    def test_compare01(self):
        self.assertEqual(t1, t2)

    def test_compare02(self):
        self.assertTrue(t1 <= t2)

    def test_compare03(self):
        self.assertTrue(t1 >= t2)

    def test_compare04(self):
        self.assertTrue(not t1 != t2)

    def test_compare05(self):
        self.assertTrue(not t1 < t2)

    def test_compare06(self):
        self.assertTrue(not t1 > t2)

    def test_compare07(self):
        self.assertTrue(t1 < t3)

    def test_compare08(self):
        self.assertTrue(t3 > t1)

    def test_compare09(self):
        self.assertTrue(t1 <= t3)

    def test_compare10(self):
        self.assertTrue(t3 >= t1)

    def test_compare11(self):
        self.assertTrue(t1 != t3)

    def test_compare12(self):
        self.assertTrue(t3 != t1)

    def test_compare13(self):
        self.assertTrue(not t1 == t3)

    def test_compare14(self):
        self.assertTrue(not t3 == t1)

    def test_compare15(self):
        self.assertTrue(not t1 > t3)

    def test_compare16(self):
        self.assertTrue(not t3 < t1)

    def test_compare17(self):
        self.assertTrue(not t1 >= t3)

    def test_compare18(self):
        self.assertTrue(not t3 <= t1)

    def test_str01(self):
        self.assertEqual(str(td(days=1)), "1d 00:00:00")

    def test_str02(self):
        self.assertEqual(str(td(days=-1)), "-1d 00:00:00")

    def test_str03(self):
        self.assertEqual(str(td(days=2)), "2d 00:00:00")

    def test_str04(self):
        self.assertEqual(str(td(days=-2)), "-2d 00:00:00")

    def test_str05(self):
        self.assertEqual(str(td(12, 58, 59)), "12:58:59")

    def test_str06(self):
        self.assertEqual(str(td(2, 3, 4)), "02:03:04")

    def test_repr01(self):
        self.assertEqual(repr(td(1)), "datetime.timedelta(seconds={})".format(1 * 3600.0))

    def test_repr02(self):
        self.assertEqual(
            repr(td(10, 2)), "datetime.timedelta(seconds={})".format(10 * 3600 + 2 * 60.0)
        )

    def test_repr03(self):
        self.assertEqual(
            repr(td(-10, 2, 40)),
            "datetime.timedelta(seconds={})".format(-10 * 3600 + 2 * 60 + 40.0),
        )

    def test_bool01(self):
        self.assertTrue(td(1))

    def test_bool02(self):
        self.assertTrue(td(0, 1))

    def test_bool03(self):
        self.assertTrue(td(0, 0, 1))

    def test_bool04(self):
        self.assertTrue(not td(0))

    def test_division01(self):
        t = td(hours=1, minutes=24, seconds=19)
        second = td(seconds=1)
        self.assertEqual(t / second, 5059.0)
        self.assertEqual(t // second, 5059)

    def test_division02(self):
        t = td(minutes=2, seconds=30)
        minute = td(minutes=1)
        self.assertEqual(t / minute, 2.5)
        self.assertEqual(t // minute, 2)

    def test_remainder01(self):
        t = td(minutes=2, seconds=30)
        r = t % td(minutes=1)
        self.assertEqual(r, td(seconds=30))

    def test_remainder02(self):
        t = td(minutes=-2, seconds=30)
        r = t % td(minutes=1)
        self.assertEqual(r, td(seconds=30))

    def test_divmod01(self):
        t = td(minutes=2, seconds=30)
        q, r = divmod(t, td(minutes=1))
        self.assertEqual(q, 2)
        self.assertEqual(r, td(seconds=30))

    def test_divmod02(self):
        t = td(minutes=-2, seconds=30)
        q, r = divmod(t, td(minutes=1))
        self.assertEqual(q, -2)
        self.assertEqual(r, td(seconds=30))


### timezone #################################################################


class Cet(tz):
    # Central European Time (see https://en.wikipedia.org/wiki/Summer_time_in_Europe)

    def __init__(self):
        super().__init__(td(hours=1), "CET")

    def dst(self, dt):
        return td(hours=1) if self.isdst(dt) else td(0)

    def tzname(self, dt):
        return "CEST" if self.isdst(dt) else "CET"

    def isdst(self, dt):
        if dt is None:
            return False
        year, month, day, hour, minute, second, nanosecond, tz = dt.tuple()
        if not 2000 <= year < 2100:
            raise ValueError
        if 3 < month < 10:
            return True
        if month == 3:
            beg = 31 - (5 * year // 4 + 4) % 7  # last Sunday of March
            if day < beg:
                return False
            if day > beg:
                return True
            return hour >= 3
        if month == 10:
            end = 31 - (5 * year // 4 + 1) % 7  # last Sunday of October
            if day < end:
                return True
            if day > end:
                return False
            return hour < 3
        return False


tz1 = tz(td(hours=-1))
tz2 = Cet()


class TestTimeZone(unittest.TestCase):
    def test_constructor01(self):
        self.assertEqual(str(tz1), "UTC-01:00")

    def test_constructor02(self):
        self.assertEqual(str(tz2), "CET")

    def test_utcoffset01(self):
        self.assertEqual(str(tz2.utcoffset(None)), "01:00:00")

    def test_utcoffset02(self):
        self.assertEqual(str(tz2.utcoffset(dt(2010, 3, 27, 12))), "01:00:00")

    def test_utcoffset03(self):
        self.assertEqual(str(tz2.utcoffset(dt(2010, 3, 28, 12))), "02:00:00")

    def test_utcoffset04(self):
        self.assertEqual(str(tz2.utcoffset(dt(2010, 10, 30, 12))), "02:00:00")

    def test_utcoffset05(self):
        self.assertEqual(str(tz2.utcoffset(dt(2010, 10, 31, 12))), "01:00:00")

    def test_isoformat01(self):
        self.assertEqual(tz2.isoformat(dt(2011, 1, 1)), "UTC+01:00")

    def test_isoformat02(self):
        self.assertEqual(tz2.isoformat(dt(2011, 8, 1)), "UTC+02:00")

    def test_tzname01(self):
        self.assertEqual(tz2.tzname(dt(2011, 1, 1)), "CET")

    def test_tzname02(self):
        self.assertEqual(tz2.tzname(dt(2011, 8, 1)), "CEST")


### datetime #################################################################

d1 = dt(2002, 1, 31)
d2 = dt(1956, 1, 31)
d3 = dt(2002, 3, 1, 12, 59, 59, 0, tz2)
d4 = dt(2002, 3, 2, 17, 6)
d5 = dt(2002, 1, 31)

hour = td(hours=1)
day = td(days=1)
week = td(weeks=1)


class TestDateTime(unittest.TestCase):
    def test_constructor01(self):
        d = dt(2002, 3, 1, 12, 0)
        year, month, day, hour, minute, second, nanosecond, tz = d.tuple()
        self.assertEqual(year, 2002)
        self.assertEqual(month, 3)
        self.assertEqual(day, 1)
        self.assertEqual(hour, 12)
        self.assertEqual(minute, 0)
        self.assertEqual(second, 0)
        self.assertEqual(nanosecond, 0)
        self.assertEqual(tz, None)

    def test_constructor02(self):
        year, month, day, hour, minute, second, nanosecond, tz = d3.tuple()
        self.assertEqual(year, 2002)
        self.assertEqual(month, 3)
        self.assertEqual(day, 1)
        self.assertEqual(hour, 12)
        self.assertEqual(minute, 59)
        self.assertEqual(second, 59)
        self.assertEqual(nanosecond, 0)
        self.assertEqual(tz, tz2)

    def test_constructor03(self):
        dt(dt.MINYEAR, 1, 1)

    def test_constructor04(self):
        dt(dt.MAXYEAR, 12, 31)

    def test_constructor05(self):
        self.assertRaises(ValueError, dt, dt.MINYEAR - 1, 1, 1)

    def test_constructor06(self):
        self.assertRaises(ValueError, dt, dt.MAXYEAR + 1, 1, 1)

    def test_constructor07(self):
        self.assertRaises(ValueError, dt, 2000, 0, 1)

    def test_constructor08(self):
        dt(2000, 2, 29)

    def test_constructor09(self):
        dt(2004, 2, 29)

    def test_constructor10(self):
        dt(2400, 2, 29)

    def test_constructor11(self):
        self.assertRaises(ValueError, dt, 2000, 2, 30)

    def test_constructor12(self):
        self.assertRaises(ValueError, dt, 2001, 2, 29)

    def test_constructor13(self):
        self.assertRaises(ValueError, dt, 2100, 2, 29)

    def test_constructor14(self):
        self.assertRaises(ValueError, dt, 1900, 2, 29)

    def test_constructor15(self):
        self.assertRaises(ValueError, dt, 2000, 1, 0)

    def test_constructor16(self):
        self.assertRaises(ValueError, dt, 2000, 1, 32)

    def test_constructor17(self):
        self.assertRaises(ValueError, dt, 2000, 1, 31, -1)

    def test_constructor18(self):
        self.assertRaises(ValueError, dt, 2000, 1, 31, 24)

    def test_constructor19(self):
        self.assertRaises(ValueError, dt, 2000, 1, 31, 23, -1)

    def test_constructor20(self):
        self.assertRaises(ValueError, dt, 2000, 1, 31, 23, 60)

    def test_constructor21(self):
        self.assertRaises(ValueError, dt, 2000, 1, 31, 23, 59, -1)

    def test_constructor22(self):
        self.assertRaises(ValueError, dt, 2000, 1, 31, 23, 59, 60)

    def test_computation01(self):
        d = d1 - d2
        self.assertEqual(d.total_seconds(), (46 * 365 + len(range(1956, 2002, 4))) * 24 * 60 * 60)

    def test_computation02(self):
        self.assertEqual(d4 + hour, dt(2002, 3, 2, 18, 6))

    def test_computation02(self):
        self.assertEqual(hour + d4, dt(2002, 3, 2, 18, 6))

    def test_computation03(self):
        self.assertEqual(d4 + 10 * hour, dt(2002, 3, 3, 3, 6))

    def test_computation04(self):
        self.assertEqual(d4 - hour, dt(2002, 3, 2, 16, 6))

    def test_computation05(self):
        self.assertEqual(-hour + d4, dt(2002, 3, 2, 16, 6))

    def test_computation06(self):
        self.assertEqual(d4 - hour, d4 + -hour)

    def test_computation07(self):
        self.assertEqual(d4 - 20 * hour, dt(2002, 3, 1, 21, 6))

    def test_computation08(self):
        self.assertEqual(d4 + day, dt(2002, 3, 3, 17, 6))

    def test_computation09(self):
        self.assertEqual(d4 - day, dt(2002, 3, 1, 17, 6))

    def test_computation10(self):
        self.assertEqual(d4 + week, dt(2002, 3, 9, 17, 6))

    def test_computation11(self):
        self.assertEqual(d4 - week, dt(2002, 2, 23, 17, 6))

    def test_computation12(self):
        self.assertEqual(d4 + 52 * week, dt(2003, 3, 1, 17, 6))

    def test_computation13(self):
        self.assertEqual(d4 - 52 * week, dt(2001, 3, 3, 17, 6))

    def test_computation14(self):
        self.assertEqual((d4 + week) - d4, week)

    def test_computation15(self):
        self.assertEqual((d4 + day) - d4, day)

    def test_computation16(self):
        self.assertEqual((d4 + hour) - d4, hour)

    def test_computation17(self):
        self.assertEqual(d4 - (d4 + week), -week)

    def test_computation18(self):
        self.assertEqual(d4 - (d4 + day), -day)

    def test_computation19(self):
        self.assertEqual(d4 - (d4 + hour), -hour)

    def test_computation20(self):
        self.assertEqual(d4 - (d4 - week), week)

    def test_computation21(self):
        self.assertEqual(d4 - (d4 - day), day)

    def test_computation22(self):
        self.assertEqual(d4 - (d4 - hour), hour)

    def test_computation23(self):
        self.assertEqual(d4 + (week + day + hour), dt(2002, 3, 10, 18, 6))

    def test_computation24(self):
        self.assertEqual(d4 + (week + day + hour), (((d4 + week) + day) + hour))

    def test_computation25(self):
        self.assertEqual(d4 - (week + day + hour), dt(2002, 2, 22, 16, 6))

    def test_computation26(self):
        self.assertEqual(d4 - (week + day + hour), (((d4 - week) - day) - hour))

    def test_compare01(self):
        self.assertEqual(d1, d5)

    def test_compare02(self):
        self.assertTrue(d1 <= d5)

    def test_compare03(self):
        self.assertTrue(d1 >= d5)

    def test_compare04(self):
        self.assertFalse(d1 != d5)

    def test_compare05(self):
        self.assertFalse(d1 < d5)

    def test_compare06(self):
        self.assertFalse(d1 > d5)

    def test_compare07(self):
        self.assertTrue(d2 < d5)

    def test_compare08(self):
        self.assertTrue(d5 > d2)

    def test_compare09(self):
        self.assertTrue(d2 <= d5)

    def test_compare10(self):
        self.assertTrue(d5 >= d2)

    def test_compare11(self):
        self.assertTrue(d2 != d5)

    def test_compare12(self):
        self.assertTrue(d5 != d2)

    def test_compare13(self):
        self.assertFalse(d2 == d5)

    def test_compare14(self):
        self.assertFalse(d5 == d2)

    def test_compare15(self):
        self.assertFalse(d2 > d5)

    def test_compare16(self):
        self.assertFalse(d5 < d2)

    def test_compare17(self):
        self.assertFalse(d2 >= d5)

    def test_compare18(self):
        self.assertFalse(d5 <= d2)

    def test_resolution01(self):
        self.assertIsInstance(td.min, td)

    def test_resolution02(self):
        self.assertIsInstance(td.max, td)

    def test_resolution03(self):
        self.assertIsInstance(td.resolution, td)

    def test_resolution04(self):
        self.assertTrue(td.max > td.min)

    def test_resolution04(self):
        self.assertEqual(td.resolution, td(nanoseconds=1))

    def test_astimezone01(self):
        self.assertEqual(d3.astimezone(tz.utc), dt(2002, 3, 1, 11, 59, 59, 0, tz.utc))

    def test_isoformat01(self):
        self.assertEqual(d3.isoformat(), "2002-03-01T12:59:59+01:00")

    def test_isoformat02(self):
        self.assertEqual(d3.isoformat("T"), "2002-03-01T12:59:59+01:00")

    def test_isoformat03(self):
        self.assertEqual(d3.isoformat(" "), "2002-03-01 12:59:59+01:00")

    def test_isoformat04(self):
        self.assertEqual(str(d3), "2002-03-01 12:59:59+01:00")

    def test_isoformat05(self):
        self.assertEqual(d3.dateisoformat(), "2002-03-01")

    def test_isoformat06(self):
        self.assertEqual(d3.timeisoformat(), "12:59:59")

    def test_fromisoformat01(self):
        self.assertEqual(fif("1975-08-10"), dt(1975, 8, 10))

    def test_fromisoformat02(self):
        self.assertEqual(fif("1975-08-10 23"), dt(1975, 8, 10, 23))

    def test_fromisoformat03(self):
        self.assertEqual(fif("1975-08-10 23:30"), dt(1975, 8, 10, 23, 30))

    def test_fromisoformat04(self):
        self.assertEqual(fif("1975-08-10 23:30:12"), dt(1975, 8, 10, 23, 30, 12))

    def test_fromisoformat05(self):
        self.assertEqual(str(fif("1975-08-10 23:30:12+01:00")), "1975-08-10 23:30:12+01:00")


if __name__ == "__main__":
    unittest.main()
