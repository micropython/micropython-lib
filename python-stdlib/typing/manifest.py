# type: ignore

metadata(version="1.26.1", description="Typing module for MicroPython.")

# default to opt_level 3 for minimal firmware size
options.defaults(opt_level=3)

module("typing.py", opt=options.opt_level)
