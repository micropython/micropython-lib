metadata(
    version="0.1.0",
    description="Common networking packages for all network-capable deployments of MicroPython.",
)

require("mip")
require("ntptime")
require("requests")
require("webrepl")
require("urllib.urequest")

# Provide urequests (which just forwards to requests) for backwards
# compatibility.
require("urequests")
