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
    print("for known device: ")
    print(record.value)


def device_callback(record, **kwargs):
    """
    a generic callback, attached to the device. Called when a record is found that has not yet been registered
    in the pack. When this callback is called, the record will already be added to the pack.
    :param kwargs: optional extra parameters
    :param record: the newly found record.
    :return: None
    """
    print("found record: " + record.name)
    print("with value: " + record.value)


def gateway_callback(record, **kwargs):
    """
    a generic callback, attached to the device. Called when a record is found that has not yet been registered
    in the pack. When this callback is called, the record will already be added to the pack.
    :param record: the newly found record.
    :param kwargs: optional extra parameters (device can be found here)
    :return: None
    """
    if "device" in kwargs and kwargs["device"] is not None:
        print("for device: " + kwargs["device"].name)
    else:
        print("for gateway: ")
    print("found record: " + record.name)
    print("with value: " + str(record.value))


gateway = SenmlPack("gateway_name", gateway_callback)
device = SenmlPack("device_name", device_callback)
actuate_me = SenmlRecord("actuator", callback=do_actuate)

gateway.add(device)
device.add(actuate_me)
gateway.from_json(
    '[{"bn": "gateway_name", "n":"temp", "v": 22},{"n": "gateway_actuator", "vb": true}, {"bn": "device_name", "n":"actuator", "v": 20 }, {"n": "another_actuator", "vs": "a value"}, {"bn": "device_2", "n":"temp", "v": 20 }, {"n": "actuator2", "vs": "value2"}]'
)
