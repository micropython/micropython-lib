# typing_extensions.py
# type: ignore
import typing

# snarky way to alias typing_extensions to typing as import * won't work
import sys
sys.modules["typing_extensions"] = sys.modules["typing"]
del sys
