metadata(
    version="0.1.0", description="On-device PyPI package installer for network-capable boards"
)

require("shutil")
require("utarfile")
require("urequests")

package("upip", opt=3)
