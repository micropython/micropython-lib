# type: ignore[all]

metadata(
    version="1.26.1",
    description="Limited runtime typing support for MicroPython.",
)

options.defaults(opt_level=3, extensions=False)

# Primary typing related modules
require("__future__", opt_level=options.opt_level)
require("typing", opt_level=options.opt_level)
require("abc", opt_level=options.opt_level)

# # Optional typing modules
if options.extensions:
    require("typing_extensions", opt_level=options.opt_level)
    require("collections-abc", opt_level=options.opt_level)
