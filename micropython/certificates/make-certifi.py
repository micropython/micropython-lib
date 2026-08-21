#!/usr/bin/env python3


import ca_bundle_mp
import os
import sys

_DEFAULTS = [b"ISRG Root X1", b"DigiCert Global Root CA"]


def create_bundles():
    ca_group = {"default": ""}
    cacerts = ca_bundle_mp.CACERTS[1:].split(b"\n\n")
    for ca in cacerts:
        name, ca_cert = ca.split(b":")
        name = name.decode().split()[0].lower()
        if name == "internet":
            name = "isrg"
        if name not in ca_group:
            ca_group[name] = ca_cert.decode()
        else:
            ca_group[name] += f"\n{ca_cert.decode()}"

        if ca_cert.splitlines()[0] in _DEFAULTS:
            ca_group["default"] += f"\n{ca_cert.decode()}"

    return ca_group


if __name__ == "__main__":
    try:
        version = sys.argv[1]
    except Exception:
        version = "0.0.1"
    description = "CA certificates bundle."
    groups = create_bundles()
    certifi_path = os.path.join(os.getcwd(), os.path.join("certifi", "certifi"))
    with open(os.path.join(os.path.dirname(certifi_path), "manifest.py"), "w") as _manifest:
        data = f"""
metadata(description='{description}', version='{version}')
package("certifi", files=("__init__.py", "default.py"), base_path=".", opt=3)
"""
        _manifest.write(data)
    for name, certs in groups.items():
        path = os.path.join(os.getcwd(), f"certifi-{name}")
        desc = f"{name} CA certificates."
        if not os.path.exists(path):
            os.mkdir(path)

        print(f"{name}\n**********\n{certs}")
        with open(os.path.join(certifi_path, f"{name}.py"), "w") as certpy:
            certpy.write("CACERTS = b'''\n")
            certpy.write(certs)
            certpy.write("\n'''")
            certpy.write("\n")

        with open(os.path.join(path, f"{name}.crt"), "w") as certfile:
            certfile.write(certs)

        with open(os.path.join(path, "manifest.py"), "w") as manifestfile:
            data = f"""
metadata(description='{desc}', version='{version}')

require("certifi")

package("certifi", files=("{name}.py",),
base_path="../certifi", opt=3)"""

            manifestfile.write(data)
            manifestfile.write("\n")
