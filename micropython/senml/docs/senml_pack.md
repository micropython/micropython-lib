
# senml_pack Module


## senml_pack.SenmlPack Objects


represents a senml pack object. This can contain multiple records but also other (child) pack objects.
When the pack object only contains records, it represents the data of a device.
If the pack object has child pack objects, then it represents a gateway 

### __enter__ 

```Python
__enter__(self)
``` 

for supporting the 'with' statement


_returns_: self 

### __exit__ 

```Python
__exit__(self, exc_type, exc_val, exc_tb)
``` 

when destroyed in a 'with' statement, make certain that the item is removed from the parent list.


_returns_: None 

### __init__ 

```Python
__init__(self, name, callback=None)
``` 

initialize the object

_parameters:_

- `name:` {string} the name of the pack 

### __iter__ 

```Python
__iter__(self)
``` 



### add 

```Python
adds the item to the list of records
``` 


_parameters:_

- `item:` {SenmlRecord} the item that needs to be added to the pack


_returns_: None 

### base_sum 

the base sum of the pack.


_returns_: a number 

### base_time 

Get the base time assigned to this pack object.
While rendering, this value will be subtracted from the value of the records.


_returns_: unix time stamp representing the base time 

### base_value 

the base value of the pack. The value of the records will be subtracted by this value during rendering.
While parsing, this value is added to the value of the records.


_returns_: a number 

### clear 

```Python
clear(self)
``` 
clear the list of the pack



_returns_: None 

### do_actuate 

```Python
do_actuate(self, raw, naming_map, device=None)
``` 

called while parsing incoming data for a record that is not yet part of this pack object.
adds a new record and raises the actuate callback of the pack with the newly created record as argument

_parameters:_

- naming_map:
- `device:` optional: if the device was not found
- `raw:` the raw record definition, as found in the json structure. this still has invalid labels.


_returns_: None 

### from_cbor 

```Python
from_cbor(self, data)
``` 

parse a cbor data byte array to a senml pack structure.

_parameters:_

- `data:` a byte array.


_returns_: None 

### from_json 

```Python
from_json(self, data)
``` 

parse a json string and convert it to a senml pack structure

_parameters:_

- `data:` a string containing json data.


_returns_: None, will call the appropriate callback functions. 



### remove 

```Python
remove(self, item)
``` 
removes the item from the pack


_parameters:_

- `item:` {SenmlRecord} the item that needs to be removed


_returns_: None 

### to_cbor 

```Python
to_cbor(self)
``` 

render the content of this object to a cbor byte array


_returns_: a byte array 

### to_json 

```Python
to_json(self)
``` 

render the content of this object to a string.


_returns_: a string representing the senml pack object 

## senml_pack.SenmlPackIterator Objects


an iterator to walk over all records in a pack 

### __init__ 

```Python
__init__(self, list)
``` 



### __iter__ 

```Python
__iter__(self)
``` 



### __next__ 

```Python
__next__(self)
``` 


