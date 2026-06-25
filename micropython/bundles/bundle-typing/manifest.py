# type: ignore[all]
# Bundle to simplify including typing support in MicroPython projects.
# This is not a full implementation of the typing module, but balances
# functionality with code size, while ignoring type hints at runtime
# to save resources.
# Usage:
# require("bundle-typing")
# require("bundle-typing", extensions=True)

metadata(
    version="1.0.0",
    description="Limited runtime typing support for MicroPython.",
)

options.defaults(opt_level=3, extensions=False)

# Primary typing related modules
require("__future__", opt_level=options.opt_level)
require("typing", opt_level=options.opt_level)
require("typing_extensions", opt_level=options.opt_level)

# Optional typing modules
if options.extensions:
    require("collections", opt_level=options.opt_level)
    require("collections-abc", opt_level=options.opt_level)
    require("abc", opt_level=options.opt_level)
