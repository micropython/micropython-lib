import os
import sys

sep = "/"
altsep = "\\"
if (sys.platform == 'uefi') and (sys.implementation.name == 'micropython'):
 sep = '\\'
 altsep = '/'
 import _re as re
else: import ure as re

def _fspath(s):
    if isinstance( s, (str, bytes) ): return s
    raise TypeError( '%s is unknown type' % s )

def _get_bothseps(path):
    if isinstance(path, bytes):
        return b'\\/'
    else:
        return '\\/'

def isabs(s):
    """Test whether a path is absolute"""
    s = _fspath(s)
    # Paths beginning with \\?\ are always absolute, but do not
    # necessarily contain a drive.
    if isinstance(s, bytes):
        if s.replace(b'/', b'\\').startswith(b'\\\\?\\'):
            return True
    else:
        if s.replace('/', '\\').startswith('\\\\?\\'):
            return True
    drv, s = splitdrive(s)
    if (len(s) < 1): return False
    return (len(s) > 0) and (s[0] in _get_bothseps(s))

def normcase(s):
    return s

def normpath(s):
    return s

def abspath(s):
    s = _fspath(s)
    (drv, s) = splitdrive(s)
    if not isabs(s):
     return join(os.getcwd(), s)
    elif ((s[0] != sep) and \
          (s[0] != altsep) ):
        return join(os.getcwd(), s)
    if drv and s: return join( drv, s )
    return s

def join(*args):
    ret = ''
    if type(args[0]) is bytes: ret = b''
    for idx,marg in enumerate(args):
     if not marg: continue
     if ret.endswith(sep) or ret.endswith(altsep) or \
        marg.startswith(sep) or marg.startswith(altsep) :
      if (ret.endswith(sep) or ret.endswith(altsep)) and \
         (marg.startswith(sep) or marg.startswith(altsep) ):
       ret += marg[1:]
      else: ret += marg
     elif type(marg) is bytes:
      ret += marg + b'/'
     else:
      ret += marg + sep

    return ret

def split(path):
    if path == "":
        return ("", "")
    r = path.rsplit(sep, 1)
    if len(r) == 1:
        return ("", path)
    head = r[0] #.rstrip("/")
    if not head:
        head = sep
    return (head, r[1])

def splitdrive(path):
    if (sys.platform == 'uefi') and (sys.implementation.name == 'micropython'):
     fsre = re.compile('^([Ff][Ss]\d+\:){0,1}([\\|\/]{0,1}.*)$')
     fsre2 = re.compile('^(\\\\\:HD\d+[a-z]\d+\:){0,1}([\\|\/]{0,1}.*)$', re.I)
     match = fsre.match(path)
     match2 = fsre2.match(path)
     if match:
      retary = []
      for i in match.groups(): retary.append(i)
      return (retary[0], sep.join(retary[1:]))
     elif match2:
      retary = []
      for i in match2.groups(): retary.append(i)
      return (retary[0], sep.join(retary[1:]))
     else:
      return ('', path )
    else:
     raise NotImplementedError("splitdrive() only implemented for uefi in micropython")

def normpath(path):
    def _startswithList(path, prefix):
     if isinstance(prefix, list) or \
        isinstance(prefix, tuple) :
      retbool = False
      for pfx in prefix:
       retbool |= path.startswith(pfx)
       if retbool: return retbool
      return retbool

     return path.startswith(prefix)

    prefix = ''
    global sep, altsep
    (lsep, laltsep) = (sep, altsep)
    #borrowed from ntpath implementation
    path = _fspath(path)
    if isinstance(path, bytes):
        lsep = b'\\'
        laltsep = b'/'
        curdir = b'.'
        pardir = b'..'
        special_prefixes = (b'\\\\.\\', b'\\\\?\\')
    else:
        curdir = '.'
        pardir = '..'
        special_prefixes = ('\\\\.\\', '\\\\?\\')

    if _startswithList(path, special_prefixes):
        # in the case of paths with these prefixes:
        # \\.\ -> device names
        # \\?\ -> literal paths
        # do not do any normalization, but return the path
        # unchanged apart from the call to os.fspath()
        return path

    path = path.replace(laltsep, lsep)
    prefix, path = splitdrive(path)

    # collapse initial backslashes
    if path.startswith(lsep):
        prefix += lsep
        path = path.lstrip(lsep)

    comps = path.split(lsep)
    i = 0
    while i < len(comps):
        if not comps[i] or comps[i] == curdir:
            del comps[i]
        elif comps[i] == pardir:
            if i > 0 and comps[i-1] != pardir:
                del comps[i-1:i+1]
                i -= 1
            elif i == 0 and prefix.endswith(lsep):
                del comps[i]
            else:
                i += 1
        else:
            i += 1
    # If the path is now empty, substitute '.'
    if not prefix and not comps:
        comps.append(curdir)

    #print( "normpath() returning: %s" % prefix + lsep.join(comps) )

    return prefix + lsep.join(comps)


def dirname(path):
    return split(path)[0]

def basename(path):
    return split(path)[1]

def exists(path):
 try:
    return os.access(path, os.F_OK)
 except OSError as e:
    if 'ENOENT' in str(e):
     print(e)
     return False

    raise e

# TODO
lexists = exists

def isdir(path):
    from stat import S_ISDIR as s_isdir
    import uos
    try:
        rstat = uos.stat(path)
        mode = None
        if not rstat:
         return False #path not exist?
        else:
         mode = rstat.st_mode
        if not mode:
         mode = os.stat(path)[0]
        return s_isdir(mode)
    except OSError:
        return False


def expanduser(s):
    if s == "~" or s.startswith("~/"):
        h = os.getenv("HOME")
        return h + s[1:]
    if s[0] == "~":
        # Sorry folks, follow conventions
        return "/home/" + s[1:]
    return s
