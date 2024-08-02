# This directory contains all aioble code, but the manifest itself just
# forwards to the component manifests, which themselves reference the actual
# code. This allows (for development purposes) all the files to live in the
# one directory.

metadata(version="0.6.0")

# Default installation gives you everything. Install the individual
# components (or a combination of them) if you want a more minimal install.
require("aioble-peripheral")
require("aioble-server")
require("aioble-central")
require("aioble-client")
require("aioble-l2cap")
require("aioble-security")
