metadata(version="0.9.0")

module("unittest.py")

if options.discover:
    module("unittest_discover.py")
    require("argparse", unix_ffi=True)
    require("fnmatch")
