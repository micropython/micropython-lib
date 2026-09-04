# zipfile

This library implements part of Python's `zipfile` module, namely allowing you
to open archives and read data out of them - as long as files are not compressed
with an unsupported compressor or encrypted.

One difference between CPython's `zipfile` implementation of `ZipFile` and this
module's is that the former does enumerate the files contained in an archive
when opening it, and this information is cached and still available even after
the archive has been closed via `ZipFile.close`.  To save memory, this
implementation neither performs any automatic enumeration on open, nor caches
the files list.  Attempting to interact with a `ZipFile` instance once it's been
closed will raise a `ValueError` exception.

## Installation

Use `mip` via `mpremote`:

```bash
> mpremote mip install zipfile
```

See [Package
management](https://docs.micropython.org/en/latest/reference/packages.html) for
more details on using `mip` and `mpremote`.
