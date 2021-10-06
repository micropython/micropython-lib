# suntime.py

__version__ = "1.0.0"

#--- Help Functions -------------------------------------------------#

from math import acos, asin, ceil, cos, degrees as deg, fmod as mod,\
                 sqrt, radians as rad, sin

# https://en.wikipedia.org/wiki/Sunrise_equation
# https://en.wikipedia.org/wiki/Julian_day
#  m = round((M - 14)/12)
#  JDN = round(1461*(Y + 4800 + m)/4)\
#      + round((367*(M - 2 - 12*m))/12)\
#      - round((3*(round((Y + 4900 + m)/100)))/4)\
#      + D - 32075
def equation (n, lat, lon, alt):
    #  n = ceil(Jd - 2451545.0 + 0.0008)
    assert(0 <= n < 36525) # days in 21st century
    Js = n - lon/360
    M = mod(357.5291 + 0.98560028*Js, 360)
    C = 1.9148*sin(rad(M)) + 0.0200*sin(rad(2*M)) + 0.0003*sin(rad(3*M))
    λ = mod(M + C + 180 + 102.9372, 360)
    Jt = 2451545.0 + Js + 0.0053*sin(rad(M)) - 0.0069*sin(rad(2*λ))
    sinδ = sin(rad(λ))*sin(rad(23.44))
    cosω0 = (sin(rad(-0.83 - 2.076*sqrt(alt)/60)) - sin(rad(lat))*sinδ)\
          / (cos(rad(lat))*cos(asin(sinδ)))
    if cosω0 <= -1.0:
        ω0 = 360
    elif cosω0 >= 1.0:
        ω0 = -360
    else:
        ω0 = deg(acos(cosω0))
    Jr = Jt - ω0/360
    Js = Jt + ω0/360
    return Jr, Js


#--- Suntime --------------------------------------------------------#

# 500 = 499 (non-leap years before 2000) + 1 (Jan 1st 2000)
def day2000(year, month, day):
    assert(2000 <= year < 2100)
    assert(1 <= month <= 12)
    assert(1 <= day <= 31)
    MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30)
    return (year - 2000)*365\
         + sum(MONTH_DAYS[:month - 1])\
         + (year if month >= 3 else year - 1)//4\
         + day\
         - 500

def jdate2time (Jd, n, tz=0):
    jtime = Jd - (2451545 + n)
    minutes = round(jtime*1440) + 720 + tz
    return minutes

class Suntime:
    def __init__(self, latitude, longitude, altitude=0, timezone=0):
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.timezone = timezone
        self.sunrise = None
        self.sunset = None

    def calc_sunrise_sunset(self, year, month, day, dst=0):
        n = day2000(year, month, day)
        Jr, Js = equation(n, self.latitude, self.longitude, self.altitude)
        tz = self.timezone + dst
        self.sunrise = jdate2time(Jr, n, tz)
        self.sunset  = jdate2time(Js, n, tz)

    def is_daytime (self, minutes):
        if self.sunrise is None or self.sunset is None:
            return None
        if not 0 <= minutes < 1440:
            return None
        return self.sunrise <= minutes < self.sunset

    def is_nighttime (self, minutes):
        daytime = self.is_daytime(minutes)
        if daytime is None:
            return None
        return not daytime

    def is_sunrise (self, minutes):
        return self.is_daytime(minutes) and minutes == self.sunrise

    def is_sunset (self, minutes):
        return self.is_nighttime(minutes) and minutes == self.sunset


#--- Sundatetime ----------------------------------------------------#

import datetime as dt

def jdate2datetime(Jd, date):
    days = date.toordinal()
    n = days - dt.datetime(2000, 1, 1).toordinal()
    dt_ = dt.datetime(0, 0, days, minute=jdate2time(Jd, n), tzinfo=dt.timezone.utc)
    if date.tzinfo:
        dt_ = dt_.astimezone(date.tzinfo)
    return dt_

class Sundatetime:
    def __init__(self, latitude, longitude, altitude=0):
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.sunrise = None
        self.sunset = None

    def calc_sunrise_sunset(self, date):
        n = date.toordinal() - dt.datetime(2000, 1, 1).toordinal()
        Jr, Js = equation(n, self.latitude, self.longitude, self.altitude)
        self.sunrise = jdate2datetime(Jr, date)
        self.sunset  = jdate2datetime(Js, date)

    def is_daytime (self, now):
        if self.sunrise is None or self.sunset is None:
            return None
        if self.sunrise >= self.sunset:
            return None
        return self.sunrise <= now < self.sunset

    def is_nighttime (self, now):
        daytime = self.is_daytime(now)
        if daytime is None:
            return None
        return not daytime

    def is_sunrise (self, now):
        return self.is_daytime(now) and self.sunrise == now

    def is_sunset (self, now):
        return self.is_nighttime(now) and self.sunset == now
