metadata(
    version="0.2.0",
    description="Common networking packages for all network-capable deployments of MicroPython.",
)

require("mip")
require("ntptime")
require("ssl")
require("requests")
require("webrepl")

# Provide urequests (which just forwards to requests) for backwards
# compatibility.
require("urequests")
