# MicroPython lora module
# MIT license; Copyright (c) 2023 Angus Gratton

from .modem import RxPacket  # noqa: F401

ok = False  # Flag if at least one modem driver package is installed

# Various lora "sub-packages"

try:
    from .sx126x import *  # noqa: F401

    ok = True
except ImportError as e:
    if "no module named 'lora." not in str(e):
        raise

try:
    from .sx127x import *  # noqa: F401

    ok = True
except ImportError as e:
    if "no module named 'lora." not in str(e):
        raise

try:
    from .stm32wl5 import *  # noqa: F401

    ok = True
except ImportError as e:
    if "no module named 'lora." not in str(e):
        raise


if not ok:
    raise ImportError(
        "Incomplete lora installation. Need at least one of lora-sync, lora-async and one of lora-sx126x, lora-sx127x"
    )

del ok
