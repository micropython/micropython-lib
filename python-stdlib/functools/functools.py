def partial(func, *args, **kwargs):
    def _partial(*more_args, **more_kwargs):
        kw = kwargs.copy()
        kw.update(more_kwargs)
        return func(*(args + more_args), **kw)

    return _partial


def update_wrapper(wrapper, wrapped, assigned=None, updated=None):
    # Dummy impl
    return wrapper


def wraps(wrapped, assigned=None, updated=None):
    # Dummy impl
    return lambda x: x


def reduce(function, iterable, initializer=None):
    it = iter(iterable)
    if initializer is None:
        value = next(it)
    else:
        value = initializer
    for element in it:
        value = function(value, element)
    return value


def lru_cache(*args, maxsize=128, **kwargs):
    def o(f):
        if maxsize == 0:
            return f
        values = {}
        order = []

        def i(*inner_args, **inner_kwargs):
            # dict isn't hashable and kwargs are pre-sorted by key.
            key = (inner_args, tuple(inner_kwargs.items()))
            if key in values:
                output = values[key]
                if maxsize:
                    order.remove(key)
            else:
                output = f(*inner_args, **inner_kwargs)
                if maxsize and len(order) == maxsize:
                    del values[order.pop()]
                values[key] = output
            if maxsize:
                order.insert(0, key)
            return output

        return i

    return o(args[0]) if args else o


def cache(*args):
    return lru_cache(*args, maxsize=None)
