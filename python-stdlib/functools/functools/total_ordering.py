"""total_ordering

This code was extracted from the CPython v3.7.17 implementation of Lib/functools.py

Written by Nick Coghlan <ncoghlan at gmail.com>,
Raymond Hettinger <python at rcn.com>,
and Łukasz Langa <lukasz at langa.pl>.
  Copyright (C) 2006-2013 Python Software Foundation.
See C source code for _functools credits/copyright

This code is distributed under the Python Software License.
"""


################################################################################
### total_ordering class decorator
################################################################################

# The total ordering functions all invoke the root magic method directly
# rather than using the corresponding operator.  This avoids possible
# infinite recursion that could occur when the operator dispatch logic
# detects a NotImplemented result and then calls a reflected method.

def _gt_from_lt(self, other, NotImplemented=NotImplemented):
    'Return a > b.  Computed by @total_ordering from (not a < b) and (a != b).'
    op_result = self.__lt__(other)
    if op_result is NotImplemented:
        return op_result
    return not op_result and self != other

def _le_from_lt(self, other, NotImplemented=NotImplemented):
    'Return a <= b.  Computed by @total_ordering from (a < b) or (a == b).'
    op_result = self.__lt__(other)
    return op_result or self == other

def _ge_from_lt(self, other, NotImplemented=NotImplemented):
    'Return a >= b.  Computed by @total_ordering from (not a < b).'
    op_result = self.__lt__(other)
    if op_result is NotImplemented:
        return op_result
    return not op_result

def _ge_from_le(self, other, NotImplemented=NotImplemented):
    'Return a >= b.  Computed by @total_ordering from (not a <= b) or (a == b).'
    op_result = self.__le__(other)
    if op_result is NotImplemented:
        return op_result
    return not op_result or self == other

def _lt_from_le(self, other, NotImplemented=NotImplemented):
    'Return a < b.  Computed by @total_ordering from (a <= b) and (a != b).'
    op_result = self.__le__(other)
    if op_result is NotImplemented:
        return op_result
    return op_result and self != other

def _gt_from_le(self, other, NotImplemented=NotImplemented):
    'Return a > b.  Computed by @total_ordering from (not a <= b).'
    op_result = self.__le__(other)
    if op_result is NotImplemented:
        return op_result
    return not op_result

def _lt_from_gt(self, other, NotImplemented=NotImplemented):
    'Return a < b.  Computed by @total_ordering from (not a > b) and (a != b).'
    op_result = self.__gt__(other)
    if op_result is NotImplemented:
        return op_result
    return not op_result and self != other

def _ge_from_gt(self, other, NotImplemented=NotImplemented):
    'Return a >= b.  Computed by @total_ordering from (a > b) or (a == b).'
    op_result = self.__gt__(other)
    return op_result or self == other

def _le_from_gt(self, other, NotImplemented=NotImplemented):
    'Return a <= b.  Computed by @total_ordering from (not a > b).'
    op_result = self.__gt__(other)
    if op_result is NotImplemented:
        return op_result
    return not op_result

def _le_from_ge(self, other, NotImplemented=NotImplemented):
    'Return a <= b.  Computed by @total_ordering from (not a >= b) or (a == b).'
    op_result = self.__ge__(other)
    if op_result is NotImplemented:
        return op_result
    return not op_result or self == other

def _gt_from_ge(self, other, NotImplemented=NotImplemented):
    'Return a > b.  Computed by @total_ordering from (a >= b) and (a != b).'
    op_result = self.__ge__(other)
    if op_result is NotImplemented:
        return op_result
    return op_result and self != other

def _lt_from_ge(self, other, NotImplemented=NotImplemented):
    'Return a < b.  Computed by @total_ordering from (not a >= b).'
    op_result = self.__ge__(other)
    if op_result is NotImplemented:
        return op_result
    return not op_result

_convert = {
    '__lt__': [('__gt__', _gt_from_lt),
               ('__le__', _le_from_lt),
               ('__ge__', _ge_from_lt)],
    '__le__': [('__ge__', _ge_from_le),
               ('__lt__', _lt_from_le),
               ('__gt__', _gt_from_le)],
    '__gt__': [('__lt__', _lt_from_gt),
               ('__ge__', _ge_from_gt),
               ('__le__', _le_from_gt)],
    '__ge__': [('__le__', _le_from_ge),
               ('__gt__', _gt_from_ge),
               ('__lt__', _lt_from_ge)]
}

def total_ordering(cls):
    """Class decorator that fills in missing ordering methods"""
    # Find user-defined comparisons (not those inherited from object).
    roots = {op for op in _convert if getattr(cls, op, None) is not getattr(object, op, None)}
    if not roots:
        raise ValueError('must define at least one ordering operation: < > <= >=')
    root = max(roots)       # prefer __lt__ to __le__ to __gt__ to __ge__
    for opname, opfunc in _convert[root]:
        if opname not in roots:
# function objects have no attributes in micropython
#            opfunc.__name__ = opname
            setattr(cls, opname, opfunc)
    return cls


