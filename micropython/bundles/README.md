These are "meta packages" designed to make it easy to provide defined
bundles of related packages.

For example, all deployments of MicroPython with networking support
(WiFi/Ethernet) should add `require("bundle-networking")` to their
`manifest.py` to ensure that the the standard set of networking packages
(including HTTP requests, WebREPL, NTP, package management) are included.
