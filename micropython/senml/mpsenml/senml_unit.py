"""
The MIT License (MIT)

Copyright (c) 2023 Arduino SA
Copyright (c) 2018 KPN (Jan Bogaerts)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""


def enum(**enums):
    return type("Enum", (), enums)


SenmlUnits = enum(
    SENML_UNIT_METER="m",
    SENML_UNIT_KILOGRAM="kg",
    SENML_UNIT_GRAM="g",
    SENML_UNIT_SECOND="s",
    SENML_UNIT_AMPERE="A",
    SENML_UNIT_KELVIN="K",
    SENML_UNIT_CANDELA="cd",
    SENML_UNIT_MOLE="mol",
    SENML_UNIT_HERTZ="Hz",
    SENML_UNIT_RADIAN="rad",
    SENML_UNIT_STERADIAN="sr",
    SENML_UNIT_NEWTON="N",
    SENML_UNIT_PASCAL="Pa",
    SENML_UNIT_JOULE="J",
    SENML_UNIT_WATT="W",
    SENML_UNIT_COULOMB="C",
    SENML_UNIT_VOLT="V",
    SENML_UNIT_FARAD="F",
    SENML_UNIT_OHM="Ohm",
    SENML_UNIT_SIEMENS="S",
    SENML_UNIT_WEBER="Wb",
    SENML_UNIT_TESLA="T",
    SENML_UNIT_HENRY="H",
    SENML_UNIT_DEGREES_CELSIUS="Cel",
    SENML_UNIT_LUMEN="lm",
    SENML_UNIT_LUX="lx",
    SENML_UNIT_BECQUEREL="Bq",
    SENML_UNIT_GRAY="Gy",
    SENML_UNIT_SIEVERT="Sv",
    SENML_UNIT_KATAL="kat",
    SENML_UNIT_SQUARE_METER="m2",
    SENML_UNIT_CUBIC_METER="m3",
    SENML_UNIT_LITER="l",
    SENML_UNIT_VELOCITY="m/s",
    SENML_UNIT_ACCELERATION="m/s2",
    SENML_UNIT_CUBIC_METER_PER_SECOND="m3/s",
    SENML_UNIT_LITER_PER_SECOND="l/s",
    SENML_UNIT_WATT_PER_SQUARE_METER="W/m2",
    SENML_UNIT_CANDELA_PER_SQUARE_METER="cd/m2",
    SENML_UNIT_BIT="bit",
    SENML_UNIT_BIT_PER_SECOND="bit/s",
    SENML_UNIT_DEGREES_LATITUDE="lat",
    SENML_UNIT_DEGREES_LONGITUDE="lon",
    SENML_UNIT_PH="pH",
    SENML_UNIT_DECIBEL="db",
    SENML_UNIT_DECIBEL_RELATIVE_TO_1_W="dBW",
    SENML_UNIT_BEL="Bspl",
    SENML_UNIT_COUNTER="count",
    SENML_UNIT_RATIO="//",
    SENML_UNIT_RELATIVE_HUMIDITY="%RH",
    SENML_UNIT_PERCENTAGE_REMAINING_BATTERY_LEVEL="%EL",
    SENML_UNIT_SECONDS_REMAINING_BATTERY_LEVEL="EL",
    SENML_UNIT_EVENT_RATE_PER_SECOND="1/s",
    SENML_UNIT_EVENT_RATE_PER_MINUTE="1/min",
    SENML_UNIT_BPM="beat/min",
    SENML_UNIT_BEATS="beats",
    SENML_UNIT_SIEMENS_PER_METER="S/m",
)
