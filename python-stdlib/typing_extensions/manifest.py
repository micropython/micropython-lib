metadata(version="1.26.1")


# default to opt_level 3 for minimal firmware size
options.defaults(opt_level=3)

module("typing_extensions.py", opt=options.opt_level)

require("typing")
package("typing_extensions")
