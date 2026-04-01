import _weakref
import micropython


class _weakref_entry:
    def __init__(self, parent, obj):
        self.parent = parent

        if not hasattr(obj, "__dict__") and not hasattr(obj, "__weakref__"):
            raise TypeError("cannot create weak reference to '{}' object".format(type(obj).__name__))
        
        # linked list ensures this will always be part of the same cyclic isolate as the original object
        self.next = obj
        try:
            getattr(obj, "__weakref__").next = self
        except (KeyError, AttributeError):
            setattr(obj, "__weakref__", self)

    def __del__(self):
        p = self.parent
        p(None)
        if p.__callback__ is not None:
            micropython.schedule(p.__callback__, p)

class ref(_weakref.ref):
    def __init__(self, obj, callback=None):
        super().__init__(obj)
        self.__callback__ = callback
        _weakref_entry(self, obj)

class finalize:
    def __init__(self, obj, func, *args, **kwargs):
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._ref = ref(obj, self)

    @property
    def alive(self):
        return self._ref() is not None
    
    def peek(self):
        obj = self._ref()
        if obj is not None:
            return (obj, self._func, self._args, self._kwargs)
    
    def detach(self):
        ret = self.peek()
        self._ref(None)
        return ret
    
    def __call__(self, r=None):
        return self._func(*self._args, **self._kwargs)

