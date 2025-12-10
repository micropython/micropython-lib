# enum.py

_Err = "no such attribute: "


class int_value(int):
    @property
    def value(self) -> int:
        return self

    def __call__(self) -> int:
        return self


class str_value(str):
    @property
    def value(self) -> str:
        return self

    def __call__(self) -> str:
        return self


class bool_value(bool):
    @property
    def value(self) -> bool:
        return self

    def __call__(self) -> bool:
        return self


class float_value(float):
    @property
    def value(self) -> float:
        return self

    def __call__(self) -> float:
        return self


def get_class_value(value):
    if type(value) is int:
        return int_value(value)
    elif type(value) is bool:
        return bool_value(value)
    elif type(value) is float:
        return float_value(value)
    elif type(value) is str:
        return str_value(value)
    else:
        return value


def enum(**kw_args):  # `**kw_args` kept backwards compatible as in the Internet examples
    return Enum(kw_args)


class Enum(dict):
    def __init__(self, arg=None):  # `arg` is dict() compatible
        super().__init__()
        self._arg = None
        if not arg is None:
            self.append(arg)
        self._is_enums_from_class = False
        self._get_enums_from_class()

    def _update(self, key, value):
        self.update({key: get_class_value(value)})

    def append(self, arg=None, **kw_args):
        if len(kw_args):
            for key, value in kw_args.items():
                self._update(key, value)
        if type(arg) == type(dict()):
            for key, value in arg.items():
                self._update(key, value)
        else:
            self._arg = arg  # for __str__()
        return self

    def __repr__(self):
        d = self.copy()
        try:
            d.pop("_arg")
        except:
            pass
        return str(d)

    def __str__(self):
        value = None
        try:
            value = self._arg
        except:
            pass
        if not value is None:
            if self.is_value(value):
                self._arg = None
                return value
            raise ValueError(_Err + f"{value}")
        return self.__qualname__ + "(" + self.__repr__() + ")"

    def is_value(self, value):
        if value in self.values():
            return True
        return False

    def key_from_value(self, value):
        for key in self:
            if self.get(key) == value:
                return self.__qualname__ + "." + key
        raise ValueError(_Err + f"{value}")

    def __call__(self, value):
        if self.is_value(value):
            return value
        raise ValueError(_Err + f"{value}")

    def __getattr__(self, key):
        try:
            if key in self:
                return self[key]
            else:
                raise KeyError(_Err + f"{key}")
        except:
            raise KeyError(_Err + f"{key}")

    def __setattr__(self, key, value):
        if key == "_arg":
            self[key] = value
            return
        try:
            self[key] = get_class_value(value)
        except:
            raise KeyError(_Err + f"{key}")

    def __delattr__(self, key):
        try:
            if key in self:
                del self[key]
            else:
                raise KeyError(_Err + f"{key}")
        except:
            raise KeyError(_Err + f"{key}")

    def __len__(self):
        return len(tuple(self.keys()))

    def __dir__(self):
        return dir(Enum)

    def _get_enums_from_class(self):
        ## Class XX(Enum):
        ##     X1 = 1
        ##     X2 = 2

        if not self._is_enums_from_class:
            keys = dir(eval(self.__qualname__))

            def try_remove(item):
                try:
                    keys.remove(item)
                except:
                    pass

            for item in dir(dict):
                try_remove(item)

            _list = [
                "__init__",
                "__class__init__",
                "__call__",
                "__Errases__",
                "__module__",
                "__qualname__",
                "__len__",
                "__lt__",
                "__le__",
                "__eq__",
                "__ne__",
                "__gt__",
                "__ge__",
                "__dir__",
                "__delattr__",
                "__getattr__",
                "__setattr__",
                "__str__",
                "__repr__",
                "_get_enums_from_class",
                "_arg",
                "_update",
                "is_value",
                "key_from_value",
                "append",
            ]
            for item in _list:
                try_remove(item)
            module = ""
            if self.__module__ != "__main__":
                module = self.__module__ + "."
            for key in keys:
                try:
                    value = eval(f"{module}{self.__qualname__}.{key}")
                except:
                    value = eval(f"{self.__qualname__}.{key}")
                self._update(key, value)
            keys.clear()
            del keys
            self._is_enums_from_class = True  # 1 !!!
            self.pop("_is_enums_from_class")  # 2 !!!
        return self
