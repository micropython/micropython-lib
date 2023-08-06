## urequests compatibility

The MicroPython version of
[requests](https://requests.readthedocs.io/en/latest/) was previously called
`urequests` and a lot of existing code depends on being able to still
import the module by that name.

This package provides a wrapper to allow this. Prefer to install and use the
`requests` package instead.
