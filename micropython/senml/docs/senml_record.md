
# senml_record Module


## senml_record.SenmlRecord Objects


represents a single value in a senml pack object 

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
__init__(self, name, **kwargs)
``` 

create a new senml record

_parameters:_

- `kwargs:`  optional parameters:
    - value: the value to store in the record
    - time: the timestamp to use (when was the value measured)
    - name: the name of hte record
    - unit: unit value
    - sum: sum value
    - update_time: max time before sensor will provide an updated reading
    - callback: a callback function taht will be called when actuator data has been found. Expects no params 

### do_actuate 

```Python
do_actuate(self, raw, naming_map)
``` 

called when a raw senml record was found for this object. Stores the data and if there is a callback, calls it.

_parameters:_

- `raw:` raw senml object


_returns_: None 

### sum 



### time 

get the time at which the measurement for the record was taken.


_returns_: a unix time stamp. This is the absolute value, not adjusted to the base time of the pack. 

### update_time 

get the time at which the next measurement is expected to be taken for this record.


_returns_: a unix time stamp. This is the absolute value, not adjusted to the base time of the pack. 

### value 

get the value currently assigned to the object 
