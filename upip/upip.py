import sys
import os
import os.path
import errno
import gzip
try:
    import utarfile as tarfile
except ImportError:
    import tarfile
try:
    import ujson as json
except ImportError:
    import json


DEFAULT_MICROPYPATH = "~/.micropython/lib:/usr/lib/micropython"

def save_file(fname, subf):
    outf = open(fname, "wb")
    while True:
        buf = subf.read(1024)
        if not buf:
            break
        outf.write(buf)
    outf.close()

def install_tar(f, prefix):
    meta = {}
    for info in f:
        #print(info)
        fname = info.name
        try:
            fname = fname[fname.index("/") + 1:]
        except ValueError:
            fname = ""

        save = True
        for p in ("setup.", "PKG-INFO"):
                #print(fname, p)
                if fname.startswith(p) or ".egg-info" in fname:
                    if fname.endswith("/requires.txt"):
                        meta["deps"] = f.extractfile(info).read()
                    save = False
                    print("Skipping", fname)
                    break

        if save:
            outfname = prefix + fname
            if info.type == tarfile.DIRTYPE:
                try:
                    os.makedirs(outfname)
                    print("Created " + outfname)
                except OSError as e:
                    if e.args[0] != errno.EEXIST:
                        raise
            else:
                print("Extracting " + outfname)
                subf = f.extractfile(info)
                save_file(outfname, subf)
    return meta

def expandhome(s):
    h = os.getenv("HOME")
    s = s.replace("~/", h + "/")
    return s

def download(url, local_name):
    os.system("wget -q %s -O %s" % (url, local_name))

def get_pkg_metadata(name):
    download("https://pypi.python.org/pypi/%s/json" % name, "pkg.json")
    with open("pkg.json") as f:
        s = f.read()
    return json.loads(s)


def fatal(msg):
    print(msg)
    sys.exit(1)

def gzdecompress(package_fname):
    f = open(package_fname, "rb")
    zipdata = f.read()
    data = gzip.decompress(zipdata)
    return data

def gzdecompress_(package_fname):
    os.system("gzip -d -c %s > ungz" % package_fname)
    with open("ungz", "rb") as f:
        return f.read()

def install_pkg(pkg_spec, install_path):
    data = get_pkg_metadata(pkg_spec)

    latest_ver = data["info"]["version"]
    print("Installing %s %s" % (pkg_spec, latest_ver))
    packages = data["releases"][latest_ver]
    assert len(packages) == 1
    package_url = packages[0]["url"]
    package_fname = os.path.basename(package_url)
    print(package_url)
    download(package_url, package_fname)

    data = gzdecompress(package_fname)

    f = open("pkg.tar", "wb")
    f.write(data)
    f.close()

    f = tarfile.TarFile("pkg.tar")
    return install_tar(f, install_path)

def main():
    install_path = None

    if sys.argv[1] != "install":
        fatal("Only 'install' command supported")

    to_install = []

    i = 2
    while i < len(sys.argv) and sys.argv[i][0] == "-":
        opt = sys.argv[i][1]
        i += 1
        if opt == "p":
            install_path = sys.argv[i]
            i += 1
        elif opt == "r":
            list_file = sys.argv[i]
            i += 1
            with open(list_file) as f:
                while True:
                    l = f.readline()
                    if not l:
                        break
                    to_install.append(l.rstrip())
        else:
            fatal("Unknown/unsupported option: " + opt)

    if install_path is None:
        install_path = DEFAULT_MICROPYPATH

    install_path = install_path.split(":", 1)[0]

    install_path = expandhome(install_path)

    if install_path[-1] != "/":
        install_path += "/"

    print("Installing to: " + install_path)

    to_install.extend(sys.argv[i:])
    # sets would be perfect here, but don't depend on them
    installed = []
    while to_install:
        print("Queue:", to_install)
        pkg_spec = to_install.pop(0)
        if pkg_spec in installed:
            continue
        meta = install_pkg(pkg_spec, install_path)
        installed.append(pkg_spec)
        print(meta)
        deps = meta.get("deps", "").rstrip()
        if deps:
            deps = deps.decode("utf-8").split("\n")
            to_install.extend(deps)


main()
