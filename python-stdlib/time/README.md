# time

This library _extends_ the built-in [MicroPython `time`
module](https://docs.micropython.org/en/latest/library/time.html#module-time) to
include
[`time.strftime()`](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior).

`strftime()` is omitted from the built-in `time` module to conserve space.

## Installation

Use `mip` via `mpremote`:

```bash
> mpremote mip install time
```

See [Package management](https://docs.micropython.org/en/latest/reference/packages.html) for more details on using `mip` and `mpremote`.

## Common uses

`strftime()` is used when using a loggging [Formatter
Object](https://docs.python.org/3/library/logging.html#formatter-objects) that
employs
[`asctime`](https://docs.python.org/3/library/logging.html#formatter-objects).

For example:

```python
logging.Formatter('%(asctime)s | %(name)s | %(levelname)s - %(message)s')
```

The expected output might look like:

```text
Tue Feb 17 09:42:58 2009 | MAIN | INFO - test
```

But if this `time` extension library isn't installed, `asctime` will always be
`None`:


```text
None | MAIN | INFO - test
```
