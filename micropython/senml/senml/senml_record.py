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


import binascii
from senml.senml_base import SenmlBase


class SenmlRecord(SenmlBase):
    """represents a single value in a senml pack object"""

    def __init__(self, name, **kwargs):
        """
        create a new senml record
        :param kwargs:  optional parameters:
            - value: the value to store in the record
            - time: the timestamp to use (when was the value measured)
            - name: the name of hte record
            - unit: unit value
            - sum: sum value
            - update_time: max time before sensor will provide an updated reading
            - callback: a callback function taht will be called when actuator data has been found. Expects no params
        """
        self.__parent = None  # using double __ cause it's a field for an internal property
        self._unit = None  # declare and init internal fields
        self._value = None
        self._time = None
        self._sum = None
        self._update_time = None

        self._parent = None  # internal reference to the parent object
        self.name = name
        self.unit = kwargs.get("unit", None)
        self.value = kwargs.get("value", None)
        self.time = kwargs.get("time", None)
        self.sum = kwargs.get("sum", None)
        self.update_time = kwargs.get("update_time", None)
        self.actuate = kwargs.get("callback", None)  # actuate callback function

    def __enter__(self):
        """
        for supporting the 'with' statement
        :return: self
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        when destroyed in a 'with' statement, make certain that the item is removed from the parent list.
        :return: None
        """
        if self._parent:
            self._parent.remove(self)

    def _check_value_type(self, value):
        """
        checks if the type of value is allowed for senml
        :return: None, raisee exception if not ok.
        """
        if value is not None:
            if not (
                isinstance(value, bool)
                or isinstance(value, int)
                or isinstance(value, float)
                or isinstance(value, bytearray)
                or isinstance(value, str)
            ):
                raise Exception(
                    "invalid type for value, only numbers, strings, boolean and byte arrays allowed"
                )

    def _check_number_type(self, value, field_name):
        """
        checks if the type of value is allowed for senml
        :return: None, raisee exception if not ok.
        """
        if value is not None:
            if not (isinstance(value, int) or isinstance(value, float)):
                raise Exception("invalid type for " + field_name + ", only numbers allowed")

    @property
    def value(self):
        """get the value currently assigned to the object"""
        return self._value

    @value.setter
    def value(self, value):
        """set the current value. Will not automatically update the time stamp. This has to be done seperatly for more
        finegrained control
        Note: when the value is a float, you can control rounding in the rendered output by using the function
        round() while assigning the value. ex: record.value = round(12.2 / 1.5423, 2)
        """
        self._check_value_type(value)
        self._value = value

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, value):
        self._check_number_type(value, "time")
        self._time = value

    @property
    def update_time(self):
        return self._update_time

    @update_time.setter
    def update_time(self, value):
        self._check_number_type(value, "update_time")
        self._update_time = value

    @property
    def sum(self):
        return self._sum

    @sum.setter
    def sum(self, value):
        self._check_number_type(value, "sum")
        self._sum = value

    @property
    def _parent(self):
        """
        the parent pack object for this record. This is a property so that inheriters can override and do custom
        actions when the parent is set (like passing it on to their children
        :return:
        """
        return self.__parent

    @_parent.setter
    def _parent(self, value):
        """
        the parent pack object for this record. This is a property so that inheriters can override and do custom
        actions when the parent is set (like passing it on to their children
        :return:
        """
        self.__parent = value

    def _build_rec_dict(self, naming_map, appendTo):
        """
        converts the object to a dictionary that can be rendered to senml.
        :param naming_map: a dictionary that maps the field names to senml json or senml cbor. keys are in the
        form 'n', 'v',...  values for 'n' are either 'n' or 0 (number is for cbor)
        :return: a senml dictionary representation of the record
        """
        result = {}

        if self.name:
            result[naming_map["n"]] = self.name

        if self._sum:
            if self._parent and self._parent.base_sum:
                result[naming_map["s"]] = self._sum - self._parent.base_sum
            else:
                result[naming_map["s"]] = self._sum
        elif isinstance(self._value, bool):
            result[naming_map["vb"]] = self._value
        elif isinstance(self._value, int) or isinstance(self._value, float):
            if self._parent and self._parent.base_value:
                result[naming_map["v"]] = self._value - self._parent.base_value
            else:
                result[naming_map["v"]] = self._value
        elif isinstance(self._value, str):
            result[naming_map["vs"]] = self._value
        elif isinstance(self._value, bytearray):
            if (
                naming_map["vd"] == "vd"
            ):  # neeed to make a distinction between json (needs base64) and cbor (needs binary)
                result[naming_map["vd"]] = binascii.b2a_base64(self._value, newline=False).decode(
                    "utf8"
                )
            else:
                result[naming_map["vd"]] = self._value
        else:
            raise Exception("sum or value of type bootl, number, string or byte-array is required")

        if self._time:
            if self._parent and self._parent.base_time:
                result[naming_map["t"]] = self._time - self._parent.base_time
            else:
                result[naming_map["t"]] = self._time

        if self.unit:
            result[naming_map["u"]] = self.unit

        if self._update_time:
            if self._parent and self._parent.base_time:
                result[naming_map["ut"]] = self._update_time - self._parent.base_time
            else:
                result[naming_map["ut"]] = self._update_time

        appendTo.append(result)

    def _from_raw(self, raw, naming_map):
        """
        extracts te data from the raw record. Used during parsing of incoming data.
        :param raw: a raw senml record which still contains the original field names
        :param naming_map: used to map cbor names to json field names
        :return:
        """
        if naming_map["v"] in raw:
            val = raw[naming_map["v"]]
            if self._parent and self._parent.base_value:
                val += self._parent.base_value
        elif naming_map["vs"] in raw:
            val = raw[naming_map["vs"]]
        elif naming_map["vb"] in raw:
            val = raw[naming_map["vb"]]
        elif naming_map["vd"] in raw:
            val = binascii.a2b_base64(raw[naming_map["vb"]])
        else:
            val = None
        self.value = val

    def do_actuate(self, raw, naming_map):
        """
        called when a raw senml record was found for this object. Stores the data and if there is a callback, calls it.
        :param raw: raw senml object
        :return: None
        """
        self._from_raw(raw, naming_map)
        if self.actuate:
            self.actuate(self)
