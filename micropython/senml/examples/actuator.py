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


def do_actuate(record):
    """
    called when actuate_me receives a value.
    :return: None
    """
    print(record.value)


def generic_callback(record, **kwargs):
    """
    a generic callback, attached to the device. Called when a record is found that has not yet been registered
    in the pack. When this callback is called, the record will already be added to the pack.
    :param record: the newly found record.
    :return: None
    """
    print("found record: " + record.name)
    print("with value: " + str(record.value))


pack = SenmlPack("device_name", generic_callback)
actuate_me = SenmlRecord("actuator", callback=do_actuate)

pack.add(actuate_me)

json_data = '[{"bn": "device_name", "n":"actuator", "v": 10 }]'
print(json_data)
pack.from_json(json_data)

json_data = (
    '[{"bn": "device_name", "n":"actuator", "v": 20 }, {"n": "another_actuator", "vs": "a value"}]'
)
print(json_data)
pack.from_json(json_data)

print('[{"bn": "device_name", "n":"temp", "v": 20, "u": "Cel" }]')
# this represents the cbor json struct: [{-2: "device_name", 0: "temp", 1: "Cel", 2: 20}]
cbor_data = bytes.fromhex("81A4216B6465766963655F6E616D65006474656D70016343656C0214")
pack.from_cbor(cbor_data)
