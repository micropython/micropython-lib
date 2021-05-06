
## Uefi Porting Status

Only a subset of `micropython-lib` has been ported to run under UEFI. In most cases; these ports were tested work under a customized version of micropython:
[Micropython for Uefi](https://github.com/Zitt/edk2-staging/tree/pushMicroPythonV1.12/MicroPythonPkg)

Both micropython and micropython-lib are under heavy development at the moment; so expect there to be issues.

Here's a table of the known functional ports of micropython-lib:
| library | Status  | Notes
|--|--|--|
| [fnmatch](https://github.com/Zitt/micropython-lib/tree/master/fnmatch) | functional | no tests
| [configparser](https://github.com/Zitt/micropython-lib/tree/master/configparser) | functional | no tests
| [glob](https://github.com/Zitt/micropython-lib/tree/master/glob) | functional | no tests
| [os](https://github.com/Zitt/micropython-lib/tree/master/os) | functional | no tests
| [os.path](https://github.com/Zitt/micropython-lib/tree/master/os) | functional | os.path moved into os