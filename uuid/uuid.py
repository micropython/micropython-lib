'''Implements just enough of UUID so that uuid4().hex will produce
   something usable.
'''

import os


class UUID:

    def __init__(self, bytes=None):
        if bytes is None:
            raise TypeError('Must provide bytes argument')
        if len(bytes) != 16:
            raise ValueError('bytes must be a 16-char string')
        self._int = int.from_bytes(bytes, 'big')

    def __str__(self):
        hex = '%032x' % self._int
        return '%s-%s-%s-%s-%s' % (
               hex[:8], hex[8:12], hex[12:16], hex[16:20], hex[20:])

    @property
    def hex(self):
        return '%032x' % self._int


def uuid4():
    '''Generates a random UUID.'''
    return UUID(bytes=os.urandom(16))
