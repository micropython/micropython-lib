#!/usr/bin/env python3


import sys
import re
import csv


def add_with_filter(crts_path, filter_path):
    filter_set = set()
    name_owner = {}
    with open(filter_path, "r", encoding="utf-8") as f:
        csv_reader = csv.reader(f, delimiter=",")

        # Skip header
        next(csv_reader)
        for row in csv_reader:
            filter_set.add(row[1])
            name_owner[row[1]] = row[0]

    crt_str = []
    with open(crts_path, "r", encoding="utf-8") as f:
        crt_str = f.read()

        # Split all certs into a list of (name, certificate string) tuples
        pem_crts = re.findall(
            r"(^.+?)\n(=+\n[\s\S]+?END CERTIFICATE-----\n)", crt_str, re.MULTILINE
        )

        filtered_crts = ""
        filtered_crts = "CACERTS = b'''"
        for name, crt in pem_crts:
            if name in filter_set:
                filtered_crts += f"\n{name_owner[name]}:{name}\n"
                filtered_crts += crt

        filtered_crts += "'''"

    return filtered_crts


if __name__ == "__main__":
    # print(sys.argv)
    cert_path, filt_path = sys.argv[1:3]
    cert_bundle = add_with_filter(cert_path, filt_path)
    with open("ca_bundle_mp.py", "w") as cafile:
        cafile.write(cert_bundle)
    print(cert_bundle)
