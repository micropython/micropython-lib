#
# upip - Package manager for MicroPython
#
# Copyright (c) 2015-2018 Paul Sokolovsky
#
# Licensed under the MIT license.
#
import sys
import gc
import re
import uos as os
import uerrno as errno
import ujson as json
import uzlib
import upip_utarfile as tarfile
gc.collect()


debug = False
install_path = None
cleanup_files = []
gzdict_sz = 16 + 15
name_regex = re.compile(r'^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])(.*)$', re.I)

file_buf = bytearray(512)

class NotFoundError(Exception):
    pass

class NoVersionError(Exception):
    pass


def op_split(path):
    if path == "":
        return ("", "")
    r = path.rsplit("/", 1)
    if len(r) == 1:
        return ("", path)
    head = r[0]
    if not head:
        head = "/"
    return (head, r[1])

def op_basename(path):
    return op_split(path)[1]

# Expects *file* name
def _makedirs(name, mode=0o777):
    ret = False
    s = ""
    comps = name.rstrip("/").split("/")[:-1]
    if comps[0] == "":
        s = "/"
    for c in comps:
        if s and s[-1] != "/":
            s += "/"
        s += c
        try:
            os.mkdir(s)
            ret = True
        except OSError as e:
            if e.args[0] != errno.EEXIST and e.args[0] != errno.EISDIR:
                raise
            ret = False
    return ret


def save_file(fname, subf):
    global file_buf
    with open(fname, "wb") as outf:
        while True:
            sz = subf.readinto(file_buf)
            if not sz:
                break
            outf.write(file_buf, sz)

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
        for p in ("setup.", "PKG-INFO", "README"):
                #print(fname, p)
                if fname.startswith(p) or ".egg-info" in fname:
                    if fname.endswith("/requires.txt"):
                        meta["deps"] = f.extractfile(info).read()
                    save = False
                    if debug:
                        print("Skipping", fname)
                    break

        if save:
            outfname = prefix + fname
            if info.type != tarfile.DIRTYPE:
                if debug:
                    print("Extracting " + outfname)
                _makedirs(outfname)
                subf = f.extractfile(info)
                save_file(outfname, subf)
    return meta

def expandhome(s):
    if "~/" in s:
        h = os.getenv("HOME")
        s = s.replace("~/", h + "/")
    return s

import ussl
import usocket
warn_ussl = True
def url_open(url):
    global warn_ussl

    if debug:
        print(url)

    proto, _, host, urlpath = url.split('/', 3)
    try:
        ai = usocket.getaddrinfo(host, 443, 0, usocket.SOCK_STREAM)
    except OSError as e:
        fatal("Unable to resolve %s (no Internet?)" % host, e)
    #print("Address infos:", ai)
    ai = ai[0]

    s = usocket.socket(ai[0], ai[1], ai[2])
    try:
        #print("Connect address:", addr)
        s.connect(ai[-1])

        if proto == "https:":
            s = ussl.wrap_socket(s, server_hostname=host)
            if warn_ussl:
                print("Warning: %s SSL certificate is not validated" % host)
                warn_ussl = False

        # MicroPython rawsocket module supports file interface directly
        s.write("GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n" % (urlpath, host))
        l = s.readline()
        protover, status, msg = l.split(None, 2)
        if status != b"200":
            if status == b"404" or status == b"301":
                raise NotFoundError("Package not found")
            raise ValueError(status)
        while 1:
            l = s.readline()
            if not l:
                raise ValueError("Unexpected EOF in HTTP headers")
            if l == b'\r\n':
                break
    except Exception as e:
        s.close()
        raise e

    return s


def get_pkg_metadata(name):
    f = url_open("https://pypi.org/pypi/%s/json" % name)
    try:
        return json.load(f)
    finally:
        f.close()


def fatal(msg, exc=None):
    print("Error:", msg)
    if exc and debug:
        raise exc
    sys.exit(1)

def install_pkg(pkg, install_path, data):
    ver = pkg.get('version', data["info"]["version"]) # defaults to latest

    packages = data["releases"][ver]
    del data
    gc.collect()
    assert len(packages) == 1
    package_url = packages[0]["url"]
    print("Installing %s %s from %s" % (pkg['name'], ver, package_url))
    package_fname = op_basename(package_url)
    f1 = url_open(package_url)
    try:
        f2 = uzlib.DecompIO(f1, gzdict_sz)
        f3 = tarfile.TarFile(fileobj=f2)
        meta = install_tar(f3, install_path)
    finally:
        f1.close()
    del f3
    del f2
    gc.collect()
    return meta

def install(to_install, install_path=None):
    # Calculate gzip dictionary size to use
    global gzdict_sz
    sz = gc.mem_free() + gc.mem_alloc()
    if sz <= 65536:
        gzdict_sz = 16 + 12

    if install_path is None:
        install_path = get_install_path()
    if install_path[-1] != "/":
        install_path += "/"
    if not isinstance(to_install, list):
        to_install = [to_install]
    print("Installing to: " + install_path)
    # sets would be perfect here, but don't depend on them
    installed = []
    try:
        while to_install:
            if debug:
                print("Queue:", to_install)
            pkg_spec = to_install.pop(0)
            if pkg_spec in installed:
                continue
            pkg, data = parse_version(pkg_spec)
            meta = install_pkg(pkg, install_path, data)
            installed.append(pkg_spec)
            if debug:
                print(meta)
            deps = meta.get("deps", "").rstrip()
            if deps:
                deps = deps.decode("utf-8").split("\n")
                to_install.extend(deps)
    except Exception as e:
        print("Error installing '{}': {}, packages may be partially installed".format(
                pkg_spec, e),
            file=sys.stderr)

def get_install_path():
    global install_path
    if install_path is None:
        # sys.path[0] is current module's path
        install_path = sys.path[1]
    install_path = expandhome(install_path)
    return install_path

def cleanup():
    for fname in cleanup_files:
        try:
            os.unlink(fname)
        except OSError:
            print("Warning: Cannot delete " + fname)

def parse_version(string):
    """
        Parse Version

        This function takes a string and gets all versioning infromation for
        pypi according to PEP508 and PEP440

        Written by: Stephan Kashkarov 2019
    """

    pkg = {}
    pkg['name'], versioning = re.match(name_regex, string).groups()
    data = get_pkg_metadata(pkg['name'])

    # Removes "Extra" arguments
    if ";" in versioning:
        versioning = versioning.split(";")[0].split(",")

    # split version parameters ie "<=3.2.3, > 2.7.1, !=3.0.1" -> [('<=', [3, 2, 3]), ('>', [2, 7, 1]), ('!=', [3, 0, 1])]
    # Does not support letters in the version name (i.e. 1.2.5rc3)
    parameters = []
    index = 0
    while len(versioning):
        index = versioning.find(',')
        if index != -1:
            substr = versioning[:index]
            versioning = versioning[index + 1:]
        else:
            substr = versioning
            versioning = ""
        while substr[index - 1] not in ['=', '>', '<']:
            index -= 1
        operation = substr[:index].strip()
        version = [int(x) if x != "*" else "*" for x in substr[index:].strip().split('.')]  # "3.0.1" -> [3, 0, 1] && "4.2.*" -> [4, 2, "*"]
        parameters.append((operation, version))

    versions = [[int(y) for y in x.split(".")] for x in data["releases"].keys()] # makes list of versions in ver_list format

    # reduces list using operators
    while parameters:
        operator, version = parameters.pop(0)
        if operator == "==":
            # Check wildcard
            if "*" in versions:
                parameters.append((">=", version[:-1])) # queues wildcard
                continue

            # direct version
            elif version in versions:
                pkg['version'] = version
                return pkg, data
        
        # removes wildcards
        version.pop()

        if operator == ">":
            versions = filter(versions, lambda x: ver_list_cmp(version, x) > 0)

        elif operator == ">=":
            versions = filter(versions, lambda x: ver_list_cmp(version, x) >= 0)

        elif operator == "<":
            versions = filter(versions, lambda x: ver_list_cmp(version, x) < 0)

        elif operator == "<=":
            versions = filter(versions, lambda x: ver_list_cmp(version, x) <= 0)

        # Arbitrary operator
        elif operator == "~=":
            parameters.extend([("<=", version[:-1]), (">=", version)])
            continue

    # returns max suitable operator
    pkg['version'] = max(versions)
    return pkg, data

def ver_list_cmp(list1, list2):
    """
        version list compaire

        This function takes two version lists (i.e [3,2,7]) and
        returns -1 if list zero is larger and 1 list one is larger
        otherwise the function will return 0

        Written by: Stephan Kashkarov 2019
    """

    # ensures verion lengths are equivelent
    if len(list1) != len(list2):
        if len(list1) > len(list2):
            list2.append(0)
            list1 = list1[:len(list2)]
        else:
            list1.append(0)
            list2 = list2[:len(list1)]

    # checks versions iteratatively
    for x, y in zip(list1, list2):
        if x > y:
            return -1
        elif y > x:
            return 1

    return 0

def help():
    print("""\
upip - Simple PyPI package manager for MicroPython
Usage: micropython -m upip install [-p <path>] <package>... | -r <requirements.txt>
import upip; upip.install(package_or_list, [<path>])

If <path> is not given, packages will be installed into sys.path[1]
(can be set from MICROPYPATH environment variable, if current system
supports that).""")
    print("Current value of sys.path[1]:", sys.path[1])
    print("""\

Note: only MicroPython packages (usually, named micropython-*) are supported
for installation, upip does not support arbitrary code in setup.py.
""")

def main():
    global debug
    global install_path
    install_path = None

    if len(sys.argv) < 2 or sys.argv[1] == "-h" or sys.argv[1] == "--help":
        help()
        return

    if sys.argv[1] not in ["install"]:
        fatal("Only 'install' command supported")

    to_install = []

    i = 2
    while i < len(sys.argv) and sys.argv[i][0] == "-":
        opt = sys.argv[i]
        i += 1
        if opt == "-h" or opt == "--help":
            help()
            return
        elif opt == "-p":
            install_path = sys.argv[i]
            i += 1
        elif opt == "-r":
            list_file = sys.argv[i]
            i += 1
            with open(list_file) as f:
                while True:
                    l = f.readline()
                    if not l:
                        break
                    if l[0] == "#":
                        continue
                    to_install.append(l.rstrip())
        elif opt == "--debug":
            debug = True
        else:
            fatal("Unknown/unsupported option: " + opt)

    to_install.extend(sys.argv[i:])
    if not to_install:
        help()
        return

    install(to_install)

    if not debug:
        cleanup()


if __name__ == "__main__":
    main()
