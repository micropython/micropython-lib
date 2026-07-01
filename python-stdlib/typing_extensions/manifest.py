metadata(version="1.0.0", description="Backport of typing_extensions for MicroPython.")


# default to opt_level 3 for minimal firmware size
options.defaults(opt_level=3)

module("typing_extensions.py", opt=options.opt_level)
package("typing_extensions")

require("typing")
