# example.py

import datetime, suntime, time

class Cet(datetime.timezone):
    def __init__(self):
        super().__init__(datetime.timedelta(hours=1), "CET")

    def dst(self, dt):
        return datetime.timedelta(hours=1) if self.isdst(dt) else datetime.timedelta(0)

    def tzname(self, dt):
        return 'CEST' if self.isdst(dt) else 'CET'

    def isdst(self, dt):
        if dt is None:
            return False
        year, month, day, hour, minute, second, tz = dt.tuple()
        if not 2000 <= year < 2100:
            raise ValueError
        if 3 < month < 10:
            return True
        if month == 3:
            beg = 31 - (5*year//4 + 4) % 7 # last Sunday of March
            if day < beg: return False
            if day > beg: return True
            return hour >= 3
        if month == 10:
            end = 31 - (5*year//4 + 1) % 7 # last Sunday of October
            if day < end: return True
            if day > end: return False
            return hour < 3
        return False

# initialization
CET = Cet()
Rome = suntime.Sundatetime(42.5966460, 12.4360233)
Rome.calc_sunrise_sunset(datetime.datetime(2000, 1, 1, tzinfo=CET))

# main loop (every minute or more)
now = datetime.datetime(*time.localtime()[:5], tzinfo=CET)
if (now.date() > Rome.sunset.date()):
    Rome.calc_sunrise_sunset(now)
print (now, Rome.is_daytime(now))


#######################################################################

# place: latitude    longitude
pl1 = ( 42.5966460,  12.4360233) # Rome
pl2 = ( 51.1627938,-122.9593616) # Vancouver
pl3 = (-33.9252192,  18.4240762) # CapeTown
pl4 = ( 55.1574890,  82.8547661) # Novosibirsk
pl5 = ( 78.6560170,  16.3447384) # Pyramiden
pl6 = pl5
pl7 = (-77.7817838, 166.4561470) # McMurdo
pl8 = pl7

# date: YY   MM  DD  sunrise  sunset
dt1 = (2000,  1,  1) # 7:37   16:49 - https://www.timeanddate.com/sun/italy/rome?month=1&year=2000
dt2 = (2014, 10,  3) # 7:15   18:46 - https://www.timeanddate.com/sun/canada/vancouver?month=10&year=2014
dt3 = (2016, 12, 21) # 5:32   19:57 - https://www.timeanddate.com/sun/south-africa/cape-town?month=12&year=2016
dt4 = (2021,  4, 24) # 6:04   20:50 - https://www.timeanddate.com/sun/russia/novosibirsk?month=4&year=2021
dt5 = (2040,  8, 25) #  up all day  - https://www.timeanddate.com/sun/@2729216?month=8&year=2033
dt6 = (2040,  8, 26) #        00:09
                     # 1:45   23:41 - https://www.timeanddate.com/sun/@2729216?month=8&year=2040
dt7 = (2033,  8, 10) # down all day - https://www.timeanddate.com/sun/antarctica/mcmurdo?month=8&year=2033
dt8 = (2033, 10, 21) # 3:00   24:13 - https://www.timeanddate.com/sun/antarctica/mcmurdo?month=10&year=2033

# timezone offsets and DSTs (in hours)
tz1 = ( 1, 0)
tz2 = (-8, 1)
tz3 = ( 2, 0)
tz4 = ( 0, 0) # wrong; it generates negative hour because actual timezone is (7, 0)
tz5 = ( 1, 1)
tz6 = ( 1, 1)
tz7 = (13,-1)
tz8 = (13, 0)


#######################################################################

# if `datetime` module is available
from suntime import Sundatetime
from datetime import datetime, timedelta, timezone

class Tz(timezone):
    def __init__(self, hours, dst=0):
        super().__init__(timedelta(hours=hours))
        self._dst = dst

    def dst(self, dt):
        return timedelta(hours=self._dst) if self.isdst(dt) else timedelta(0)

    def isdst(self, dt):
        return self._dst != 0

now = datetime(*dt1, tzinfo=Tz(*tz1))
sd1 = Sundatetime(*pl1)
sd1.calc_sunrise_sunset(now)
print('Rome:', now)
print('>', sd1.sunrise) # 2000-01-01 07:40:00+01:00
print('>', sd1.sunset ) # 2000-01-01 16:47:00+01:00

now = datetime(*dt2, tzinfo=Tz(*tz2))
sd2 = Sundatetime(*pl2)
sd2.calc_sunrise_sunset(now)
print('Vancouver:', now)
print('>', sd2.sunrise) # 2014-10-03 07:16:00-08:00
print('>', sd2.sunset ) # 2014-10-03 18:46:00-08:00

now = datetime(*dt3, tzinfo=Tz(*tz3))
sd3 = Sundatetime(*pl3)
sd3.calc_sunrise_sunset(now)
print('Cape Town:', now)
print('>', sd3.sunrise) # 2016-12-21 05:32:00+02:00
print('>', sd3.sunset ) # 2016-12-21 19:57:00+02:00

now = datetime(*dt4, tzinfo=Tz(*tz4))
sd4 = Sundatetime(*pl4)
sd4.calc_sunrise_sunset(now)
print('Novosibirsk:', now)
print('>', sd4.sunrise) # 2021-04-23 23:04:00+00:00
print('>', sd4.sunset ) # 2021-04-24 13:49:00+00:00

now = datetime(*dt5, tzinfo=Tz(*tz5))
sd5 = Sundatetime(*pl5)
sd5.calc_sunrise_sunset(now)
print('Pyramiden:', now)
print('>', sd5.sunrise) # 2040-08-24 12:57:00+02:00
print('>', sd5.sunset ) # 2040-08-26 12:57:00+02:00

now = datetime(*dt6, tzinfo=Tz(*tz6))
sd6 = Sundatetime(*pl6)
sd6.calc_sunrise_sunset(now)
print('Pyramiden:', now)
print('>', sd6.sunrise) # 2040-08-26 01:35:00+02:00
print('>', sd6.sunset ) # 2040-08-27 00:18:00+02:00

now = datetime(*dt7, tzinfo=Tz(*tz7))
sd7 = Sundatetime(*pl7)
sd7.calc_sunrise_sunset(now)
print('McMurdo:', now)
print('>', sd7.sunrise) # 2033-08-11 13:00:00+12:00
print('>', sd7.sunset ) # 2033-08-09 13:00:00+12:00

now = datetime(*dt8, tzinfo=Tz(*tz8))
sd8 = Sundatetime(*pl8)
sd8.calc_sunrise_sunset(now)
print('McMurdo:', now)
print('>', sd8.sunrise) # 2033-10-21 03:06:00+13:00
print('>', sd8.sunset ) # 2033-10-22 00:12:00+13:00


#######################################################################

from suntime import Suntime

st1 = Suntime(*pl1, timezone=tz1[0]*60)
st1.calc_sunrise_sunset(*dt1, dst=tz1[1]*60)
print('Rome:', dt1, tz1)
print('>', divmod(st1.sunrise, 60)) # (7, 40)
print('>', divmod(st1.sunset , 60)) # (16, 47)

st2 = Suntime(*pl2, timezone=tz2[0]*60)
st2.calc_sunrise_sunset(*dt2, dst=tz2[1]*60)
print('Vancouver:', dt2, tz2)
print('>', divmod(st2.sunrise, 60)) # (7, 16)
print('>', divmod(st2.sunset , 60)) # (18, 46)

st3 = Suntime(*pl3, timezone=tz3[0]*60)
st3.calc_sunrise_sunset(*dt3, dst=tz3[1]*60)
print('Cape Town:', dt3, tz3)
print('>', divmod(st3.sunrise, 60)) # (5, 32)
print('>', divmod(st3.sunset , 60)) # (19, 57)

st4 = Suntime(*pl4, timezone=tz4[0]*60)
st4.calc_sunrise_sunset(*dt4, dst=tz4[1]*60)
print('Novosibirsk:', dt4, tz4)
print('>', divmod(st4.sunrise, 60)) # (-1, 4)
print('>', divmod(st4.sunset , 60)) # (13, 49)

st5 = Suntime(*pl5, timezone=tz5[0]*60)
st5.calc_sunrise_sunset(*dt5, dst=tz5[1]*60)
print('Pyramiden:', dt5, tz5)
print('>', divmod(st5.sunrise, 60)) # (-12, 57)
print('>', divmod(st5.sunset , 60)) # (36, 57)

st6 = Suntime(*pl6, timezone=tz6[0]*60)
st6.calc_sunrise_sunset(*dt6, dst=tz6[1]*60)
print('Pyramiden:', dt6, tz6)
print('>', divmod(st6.sunrise, 60)) # (1, 35)
print('>', divmod(st6.sunset , 60)) # (24, 18)

st7 = Suntime(*pl7, timezone=tz7[0]*60)
st7.calc_sunrise_sunset(*dt7, dst=tz7[1]*60)
print('McMurdo:', dt7, tz7)
print('>', divmod(st7.sunrise, 60)) # (37, 0)
print('>', divmod(st7.sunset , 60)) # (-11, 0)

st8 = Suntime(*pl8, timezone=tz8[0]*60)
st8.calc_sunrise_sunset(*dt8, dst=tz8[1]*60)
print('McMurdo:', dt8, tz8)
print('>', divmod(st8.sunrise, 60)) # (3, 6)
print('>', divmod(st8.sunset , 60)) # (24, 12)
