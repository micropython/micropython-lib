# functools

# Testing

## Install docker

See https://docs.docker.com/engine/install/

## Build test environment

```
docker build -t micropython-unittest .
```

## Run tests

All test files are designed to execute their own tests either as 
assert statements or as a call to unittest.

```
for i in test_*.py; do docker run -v .:/code -ti --rm micropython-unittest micropython $i; done
```

# License

Some files are distributed under the Python Software Foundation license.
These files reference the Python Software Foundation license at the top of the file.

