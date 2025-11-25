# collections.abc
# minimal support for runtime typing
# type: ignore
try:
    from typing import __Ignore as ABC, __getattr__ as __getattr__
except:
    pass