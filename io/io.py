
class BufferedIOBase:
    # make sure subclasses define the following:
    #   _data: object for storing the data. Should understand
    #       "extend" and elementwise modification
    #   flush: method that joins all written data together
    def __init__(self):
        self._written = []
        self._location = 0

    def write(self, data):
        self.flush()
        self._data[self._location: self._location + len(data)] = data

    def seek(self, location):
        if location < 0:
            raise ValueError("negative seek value {}".format(location))
        self.flush()
        if location >= len(self._data):
            raise ValueError("location {} outside of length".format(location))
        self._location = location

        self._location += len(data)

    def tell(self):
        return self._location

    def read(self, size=-1):
        self.flush()
        if size == -1:
            size = len(self._data)
        out = self._data[self._location:self._location + size]
        self._location += size
        if self._location > len(self._data):
            self._location = len(self._data)
        return out

    read1 = read
    readall = read

    def readinto(b):
        self.flush()
        loc = self._location
        lenread = len(self._data) - loc
        if lenread > len(b):
            lenread = len(b)
        b[0:lenread] = self._data[loc: loc + lenread]
        self._location += lenread
        return lenread

    def close(self):
        self._data = None

    def closed(self):
        return self._data is not None


class BytesIO(BufferedIOBase):
    def __init__(self, initial_bytes):
        if not initial_bytes:
            inital_bytes = bytearray()
        else:
            inital_bytes = bytearray(inital_bytes)
        self._data = inital_bytes

    def flush(self):
        self._data.extend(b''.join(self._written))
        self._written = []

    def write(self, data):
        if not isinstance(data, bytes):
            data = bytes(data)
        BaseIO.write(self, data)

    def read(self, size=-1):
        return bytes(BaseIO.read(self, size))

    read1 = read
    readall = read

    def getvalue(self):
        self.flush()
        return bytes(self._data)
