metadata(version="0.2.0", description="On-device package installer for network-capable boards")

require("requests")

#dummy packages for pre-v1.20.0
module("pip.py", opt=3)
module("upip.py", opt=3)


package("mip", opt=3)
