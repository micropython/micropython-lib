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


from senml import *

import time


class Coordinates(SenmlRecord):
    def __init__(self, name, **kwargs):
        """overriding the init function so we can initiate the 3 senml records that will represent lat,lon, alt"""
        self._lat = SenmlRecord(
            "lattitude", unit=SenmlUnits.SENML_UNIT_DEGREES_LATITUDE
        )  # create these befor calling base constructor so that all can be init correctly from constructor
        self._lon = SenmlRecord("longitude", unit=SenmlUnits.SENML_UNIT_DEGREES_LONGITUDE)
        self._alt = SenmlRecord("altitude", unit=SenmlUnits.SENML_UNIT_METER)
        super(Coordinates, self).__init__(
            name, **kwargs
        )  # need to call base init, to make certain all is ok.

    def _check_value_type(self, value):
        """overriding the check on value type to make certain that only an array with 3 values is assigned: lat,lon/alt"""
        if value is not None:
            if not isinstance(value, list):
                raise Exception("invalid data type: array with 3 elements expected lat, lon, alt")

    def _build_rec_dict(self, naming_map, appendTo):
        """
        override the rendering of the senml data objects. These will be converted to json or cbor
        :param naming_map: {dictionary} a map that determines the field names, these are different for json vs cbor
        :param appendTo: {list} the result list
        :return: None
        """
        self._lat._build_rec_dict(naming_map, appendTo)
        self._lon._build_rec_dict(naming_map, appendTo)
        self._alt._build_rec_dict(naming_map, appendTo)

    @SenmlRecord.value.setter
    def value(self, value):
        """set the current value.
        this is overridden so we can pass on the values to the internal objects. It's also stored in the parent
        so that a 'get-value' still returns the array.
        """
        self._value = (
            value  # micropython doesn't support calling setter of parent property, do it manually
        )
        if value:
            self._lat.value = value[0]
            self._lon.value = value[1]
            self._alt.value = value[2]
        else:
            self._lat.value = None
            self._lon.value = None
            self._alt.value = None

    @SenmlRecord.time.setter
    def time(self, value):
        """set the time stamp.
        this is overridden so we can pass on the values to the internal objects.
        """
        self._check_number_type(
            value, "time"
        )  # micropython doesn't support calling setter of parent property, do it manually
        self._time = value
        self._lat.time = value
        self._lon.time = value
        self._alt.time = value

    @SenmlRecord.update_time.setter
    def update_time(self, value):
        """set the time stamp.
        this is overridden so we can pass on the values to the internal objects.
        """
        self._check_number_type(
            value, "update_time"
        )  # micropython doesn't support calling setter of parent property, do it manually
        self._update_time = value
        self._lat.update_time = value
        self._lon.update_time = value
        self._alt.update_time = value

    @SenmlRecord._parent.setter
    def _parent(self, value):
        """set the time stamp.
        this is overridden so we can pass on the values to the internal objects.
        This is needed so that the child objects can correctly take base time (optionally also base-sum, base-value) into account
        """
        self.__parent = (
            value  # micropython doesn't support calling setter of parent property, do it manually
        )
        self._lat._parent = value
        self._lon._parent = value
        self._alt._parent = value


pack = SenmlPack("device_name")
loc = Coordinates("location")
loc2 = Coordinates("location", value=[52.0259, 5.4775, 230])
pack.add(loc)
pack.add(loc2)

print(loc._parent.name)

loc.value = [51.0259, 4.4775, 10]
print(pack.to_json())

pack.base_time = time.time()  # set a base time
time.sleep(2)
loc.time = time.time()  # all child objects will receive the time value
print(pack.to_json())
