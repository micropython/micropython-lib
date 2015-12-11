def upip_import(mod, sub=None):
    try:
        mod_ = mod
        if sub:
            mod_ += "_" + sub
        return __import__("upip_" + mod_)
    except ImportError:
        m = __import__(mod)
        if sub:
            return getattr(m, sub)
        return m

sys = upip_import("sys")
import uos as os

errno = upip_import("errno")
gzip = upip_import("gzip")
try:
    tarfile = upip_import("utarfile")
except ImportError:
    tarfile = upip_import("tarfile")
try:
    json = upip_import("ujson")
except ImportError:
    json = upip_import("json")


DEFAULT_MICROPYPATH = "~/.micropython/lib:/usr/lib/micropython"

debug = False
cleanup_files = [".pkg.tar"]

class NotFoundError(Exception):
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

def _makedirs(name, mode=0o777):
    ret = False
    s = ""
    for c in name.rstrip("/").split("/"):
        s += c + "/"
        try:
            os.mkdir(s)
            ret = True
        except OSError as e:
            if e.args[0] != errno.EEXIST and e.args[0] != errno.EISDIR:
                raise
            ret = False
    return ret


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
            if info.type == tarfile.DIRTYPE:
                if _makedirs(outfname):
                    print("Created " + outfname)
            else:
                if debug:
                    print("Extracting " + outfname)
                subf = f.extractfile(info)
                save_file(outfname, subf)
    return meta

def expandhome(s):
    h = os.getenv("HOME")
    s = s.replace("~/", h + "/")
    return s

try:
    import ussl
    import usocket
    def download(url, local_name):
        proto, _, host, urlpath = url.split('/', 3)
        ai = usocket.getaddrinfo(host, 443)
        #print("Address infos:", ai)
        addr = ai[0][4]

        s = usocket.socket()
        #print("Connect address:", addr)
        s.connect(addr)

        if proto == "https:":
            s = ussl.wrap_socket(s)

        # MicroPython rawsocket module supports file interface directly
        s.write("GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n" % (urlpath, host))
        l = s.readline()
        protover, status, msg = l.split(None, 2)
        if status != b"200":
            raise OSError()
        while 1:
            l = s.readline()
            if not l:
                raise OSError()
            if l == b'\r\n':
                break
        with open(local_name, "wb") as f:
            while 1:
                l = s.read(1024)
                if not l:
                    break
                f.write(l)

except ImportError:

    def download(url, local_name):
        if debug:
            print("wget -q %s -O %s" % (url, local_name))
        rc = os.system("wget -q %s -O %s" % (url, local_name))
        if local_name not in cleanup_files:
            cleanup_files.append(local_name)
        if rc == 8 * 256:
            raise NotFoundError


def get_pkg_metadata(name):
    download("https://pypi.python.org/pypi/%s/json" % name, ".pkg.json")
    with open(".pkg.json") as f:
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
    packages = data["releases"][latest_ver]
    assert len(packages) == 1
    package_url = packages[0]["url"]
    print("Installing %s %s from %s" % (pkg_spec, latest_ver, package_url))
    package_fname = op_basename(package_url)
    download(package_url, package_fname)

    data = gzdecompress(package_fname)

    f = open(".pkg.tar", "wb")
    f.write(data)
    f.close()

    f = tarfile.TarFile(".pkg.tar")
    return install_tar(f, install_path)

def cleanup():
    for fname in cleanup_files:
        try:
            os.unlink(fname)
        except OSError:
            print("Warning: Cannot delete " + fname)

def help():
    print("upip - Simple PyPI package manager for MicroPython")
    print("Usage: micropython -m upip install <package>... | -r <requirements.txt>")
    print("""\
Note: only MicroPython packages (usually, micropython-*) are supported for
installation, upip does not support arbitrary code in setup.py.""")
    sys.exit(1)

def main():
    global debug
    install_path = None

    if len(sys.argv) < 2 or sys.argv[1] == "-h" or sys.argv[1] == "--help":
        help()

    if sys.argv[1] != "install":
        fatal("Only 'install' command supported")

    to_install = []

    i = 2
    while i < len(sys.argv) and sys.argv[i][0] == "-":
        opt = sys.argv[i]
        i += 1
        if opt == "-h" or opt == "--help":
            help()
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
                    to_install.append(l.rstrip())
        elif opt == "--debug":
            debug = True
        else:
            fatal("Unknown/unsupported option: " + opt)

    if install_path is None:
        install_path = os.getenv("MICROPYPATH") or DEFAULT_MICROPYPATH

    install_path = install_path.split(":", 1)[0]

    install_path = expandhome(install_path)

    if install_path[-1] != "/":
        install_path += "/"

    print("Installing to: " + install_path)

    to_install.extend(sys.argv[i:])
    if not to_install:
        help()

    # sets would be perfect here, but don't depend on them
    installed = []
    try:
        while to_install:
            if debug:
                print("Queue:", to_install)
            pkg_spec = to_install.pop(0)
            if pkg_spec in installed:
                continue
            meta = install_pkg(pkg_spec, install_path)
            installed.append(pkg_spec)
            if debug:
                print(meta)
            deps = meta.get("deps", "").rstrip()
            if deps:
                deps = deps.decode("utf-8").split("\n")
                to_install.extend(deps)
    except NotFoundError:
        print("Error: cannot find '%s' package (or server error), packages may be partially installed" \
            % pkg_spec, file=sys.stderr)

    if not debug:
        cleanup()

main()
