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


from senml.senml_record import SenmlRecord
from senml.senml_base import SenmlBase
import json
import cbor2


class SenmlPackIterator:
    """an iterator to walk over all records in a pack"""

    def __init__(self, list):
        self._list = list
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._index < len(self._list):
            res = self._list[self._index]
            self._index += 1
            return res
        else:
            raise StopIteration


class SenmlPack(SenmlBase):
    """
    represents a sneml pack object. This can contain multiple records but also other (child) pack objects.
    When the pack object only contains records, it represents the data of a device.
    If the pack object has child pack objects, then it represents a gateway
    """

    json_mappings = {
        "bn": "bn",
        "bt": "bt",
        "bu": "bu",
        "bv": "bv",
        "bs": "bs",
        "n": "n",
        "u": "u",
        "v": "v",
        "vs": "vs",
        "vb": "vb",
        "vd": "vd",
        "s": "s",
        "t": "t",
        "ut": "ut",
    }

    def __init__(self, name, callback=None):
        """
        initialize the object
        :param name: {string} the name of the pack
        """
        self._data = []
        self.name = name
        self._base_value = None
        self._base_time = None
        self._base_sum = None
        self.base_unit = None
        self._parent = None  # a pack can also be the child of another pack.
        self.actuate = callback  # actuate callback function

    def __iter__(self):
        return SenmlPackIterator(self._data)

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

    @property
    def base_value(self):
        """
        the base value of the pack.
        :return: a number
        """
        return self._base_value

    @base_value.setter
    def base_value(self, value):
        """
        set the base value.
        :param value: only number allowed
        :return:
        """
        self._check_value_type(value, "base_value")
        self._base_value = value

    @property
    def base_sum(self):
        """
        the base sum of the pack.
        :return: a number
        """
        return self._base_sum

    @base_sum.setter
    def base_sum(self, value):
        """
        set the base value.
        :param value: only number allowed
        :return:
        """
        self._check_value_type(value, "base_sum")
        self._base_sum = value

    @property
    def base_time(self):
        return self._base_time

    @base_time.setter
    def base_time(self, value):
        self._check_value_type(value, "base_time")
        self._base_time = value

    def _check_value_type(self, value, field_name):
        """
        checks if the type of value is allowed for senml
        :return: None, raisee exception if not ok.
        """
        if value is not None:
            if not (isinstance(value, int) or isinstance(value, float)):
                raise Exception("invalid type for " + field_name + ", only numbers allowed")

    def from_json(self, data):
        """
        parse a json string and convert it to a senml pack structure
        :param data: a string containing json data.
        :return: None, will r
        """
        records = json.loads(data)  # load the raw senml data
        self._process_incomming_data(records, SenmlPack.json_mappings)

    def _process_incomming_data(self, records, naming_map):
        """
        generic processor for incomming data (actuators.
        :param records: the list of raw senml data, parsed from a json or cbor structure
        :param naming_map: translates cbor to json field names (when needed).
        :return: None
        """
        cur_pack_el = self
        new_pack = False
        for item in records:
            if naming_map["bn"] in item:  # ref to a pack element, either this or a child pack.
                if item[naming_map["bn"]] != self.name:
                    pack_el = [x for x in self._data if x.name == item[naming_map["bn"]]]
                else:
                    pack_el = [self]
                if len(pack_el) > 0:
                    cur_pack_el = pack_el[0]
                    new_pack = False
                else:
                    device = SenmlPack(item[naming_map["bn"]])
                    self._data.append(device)
                    cur_pack_el = device
                    new_pack = True

                if (
                    naming_map["bv"] in item
                ):  # need to copy the base value assigned to the pack element so we can do proper conversion for actuators.
                    cur_pack_el.base_value = item[naming_map["bv"]]

                rec_el = [x for x in cur_pack_el._data if x.name == item[naming_map["n"]]]
                if len(rec_el) > 0:
                    rec_el[0].do_actuate(item, naming_map)
                elif new_pack:
                    self.do_actuate(item, naming_map, cur_pack_el)
                else:
                    cur_pack_el.do_actuate(item, naming_map)
            else:
                rec_el = [x for x in self._data if x.name == item[naming_map["n"]]]
                if len(rec_el) > 0:
                    rec_el[0].do_actuate(item, naming_map)
                elif new_pack:
                    self.do_actuate(item, naming_map, cur_pack_el)
                else:
                    cur_pack_el.do_actuate(item, naming_map)

    def do_actuate(self, raw, naming_map, device=None):
        """
        called while parsing incoming data for a record that is not yet part of this pack object.
        adds a new record and raises the actuate callback of the pack with the newly created record as argument
        :param naming_map:
        :param device: optional: if the device was not found
        :param raw: the raw record definition, as found in the json structure. this still has invalid labels.
        :return: None
        """
        rec = SenmlRecord(raw[naming_map["n"]])
        if device:
            device.add(rec)
            rec._from_raw(raw, naming_map)
            if self.actuate:
                self.actuate(rec, device=device)
        else:
            self.add(rec)
            rec._from_raw(raw, naming_map)
            if self.actuate:
                self.actuate(rec, device=None)

    def to_json(self):
        """
        render the content of this object to a string.
        :return: a string representing the senml pack object
        """
        converted = []
        self._build_rec_dict(SenmlPack.json_mappings, converted)
        return json.dumps(converted)

    def _build_rec_dict(self, naming_map, appendTo):
        """
        converts the object to a senml object with the proper naming in place.
        This can be recursive: a pack can contain other packs.
        :param naming_map: a dictionary used to pick the correct field names for either senml json or senml cbor
        :return:
        """
        internalList = []
        for item in self._data:
            item._build_rec_dict(naming_map, internalList)
        if len(internalList) > 0:
            first_rec = internalList[0]
        else:
            first_rec = {}
            internalList.append(first_rec)

        if self.name:
            first_rec[naming_map["bn"]] = self.name
        if self.base_value:
            first_rec[naming_map["bv"]] = self.base_value
        if self.base_unit:
            first_rec[naming_map["bu"]] = self.base_unit
        if self.base_sum:
            first_rec[naming_map["bs"]] = self.base_sum
        if self.base_time:
            first_rec[naming_map["bt"]] = self.base_time
        appendTo.extend(internalList)

    def from_cbor(self, data):
        """
        parse a cbor data byte array to a senml pack structure.
        :param data: a byte array.
        :return: None
        """
        records = cbor2.loads(data)  # load the raw senml data
        naming_map = {
            "bn": -2,
            "bt": -3,
            "bu": -4,
            "bv": -5,
            "bs": -16,
            "n": 0,
            "u": 1,
            "v": 2,
            "vs": 3,
            "vb": 4,
            "vd": 8,
            "s": 5,
            "t": 6,
            "ut": 7,
        }
        self._process_incomming_data(records, naming_map)

    def to_cbor(self):
        """
        render the content of this object to a cbor byte array
        :return: a byte array
        """
        naming_map = {
            "bn": -2,
            "bt": -3,
            "bu": -4,
            "bv": -5,
            "bs": -16,
            "n": 0,
            "u": 1,
            "v": 2,
            "vs": 3,
            "vb": 4,
            "vd": 8,
            "s": 5,
            "t": 6,
            "ut": 7,
        }
        converted = []
        self._build_rec_dict(naming_map, converted)
        return cbor2.dumps(converted)

    def add(self, item):
        """
        adds the item to the list of records
        :param item: {SenmlRecord} the item that needs to be added to the pack
        :return: None
        """
        if not (isinstance(item, SenmlBase)):
            raise Exception("invalid type of param, SenmlRecord or SenmlPack expected")
        if item._parent is not None:
            raise Exception("item is already part of a pack")

        self._data.append(item)
        item._parent = self

    def remove(self, item):
        """
        removes the item from the list of records
        :param item: {SenmlRecord} the item that needs to be removed
        :return: None
        """
        if not (isinstance(item, SenmlBase)):
            raise Exception("invalid type of param, SenmlRecord or SenmlPack expected")
        if not item._parent == self:
            raise Exception("item is not part of this pack")

        self._data.remove(item)
        item._parent = None

    def clear(self):
        """
        clear the list of the pack
        :return: None
        """
        for item in self._data:
            item._parent = None
        self._data = []
