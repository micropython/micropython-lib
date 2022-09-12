# This directory contains all aioble code, but the manifest itself just
# forwards to the component manifests, which themselves reference the actual
# code.
# This allows (for development purposes) all the files to live in the one
# directory.

metadata(version="0.1.0")

# Default installation gives you core, peripheral, and server.
require("aioble-peripheral")
require("aioble-server")
