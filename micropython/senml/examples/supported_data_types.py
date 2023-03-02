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

pack = SenmlPack("device_name")

double_val = SenmlRecord("double", value=23.5)
int_val = SenmlRecord("int", value=23)
bool_val = SenmlRecord("bool", value=True)
str_val = SenmlRecord("str val", value="test")
bytes_val = SenmlRecord("bytes", value=bytearray(b"00 1e 05 ff"))

# invalid value
try:
    invalid = SenmlRecord("invalid", value={"a": 1})
except Exception as error:
    print(error)


pack.add(double_val)
pack.add(int_val)
pack.add(bool_val)
pack.add(str_val)
pack.add(bytes_val)

while True:
    print(pack.to_json())
    time.sleep(1)
