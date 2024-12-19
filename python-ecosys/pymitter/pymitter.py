# coding: utf-8

"""
Python port of the extended Node.js EventEmitter 2 approach providing namespaces, wildcards and TTL.
"""

__author__ = "Marcel Rieger"
__author_email__ = "github.riga@icloud.com"
__copyright__ = "Copyright 2014-2022, Marcel Rieger"
__credits__ = ["Marcel Rieger"]
__contact__ = "https://github.com/riga/pymitter"
__license__ = "BSD-3-Clause"
__status__ = "Development"
__version__ = "0.3.2"
__all__ = ["EventEmitter", "Listener"]


import time


class EventEmitter(object):
    """
    The EventEmitter class, ported from Node.js EventEmitter 2.

    When *wildcard* is *True*, wildcards in event names are taken into account. When *new_listener*
    is *True*, a ``"new_listener"`` event is emitted every time a new listener is registered with
    arguments ``(func, event=None)``. *max_listeners* configures the maximum number of event
    listeners. A negative numbers means that this number is unlimited. Event names have namespace
    support with each namspace being separated by a *delimiter* which defaults to ``"."``.
    """

    CB_KEY = "__callbacks"
    WC_CHAR = "*"

    def __init__(self, wildcard=False, new_listener=False, max_listeners=-1, delimiter="."):
        super(EventEmitter, self).__init__()

        self.wildcard = wildcard
        self.delimiter = delimiter
        self.new_listener = new_listener
        self.max_listeners = max_listeners

        self._tree = self._new_branch()

    @classmethod
    def _new_branch(cls):
        """
        Returns a new branch. Essentially, a branch is just a dictionary with a special item
        *CB_KEY* that holds registered functions. All other items are used to build a tree
        structure.
        """
        return {cls.CB_KEY: []}

    def _find_branch(self, event):
        """
        Returns a branch of the tree structure that matches *event*. Wildcards are not applied.
        """
        parts = event.split(self.delimiter)

        if self.CB_KEY in parts:
            return None

        branch = self._tree
        for p in parts:
            if p not in branch:
                return None
            branch = branch[p]

        return branch

    @classmethod
    def _remove_listener(cls, branch, func):
        """
        Removes a listener given by its function *func* from a *branch*.
        """
        listeners = branch[cls.CB_KEY]

        indexes = [i for i, l in enumerate(listeners) if l.func == func]

        for i in indexes[::-1]:
            listeners.pop(i)

    def on(self, event, func=None, ttl=-1):
        """
        Registers a function to an event. *ttl* defines the times to listen. Negative values mean
        infinity. When *func* is *None*, decorator usage is assumed. Returns the function.
        """
        def on(func):
            if not callable(func):
                return func

            parts = event.split(self.delimiter)
            if self.CB_KEY in parts:
                return func

            branch = self._tree
            for p in parts:
                branch = branch.setdefault(p, self._new_branch())

            listeners = branch[self.CB_KEY]
            if 0 <= self.max_listeners <= len(listeners):
                return func

            listener = Listener(func, event, ttl)
            listeners.append(listener)

            if self.new_listener:
                self.emit("new_listener", func, event)

            return func

        return on(func) if func else on

    def once(self, event, func=None):
        """
        Registers a function to an event that is called once. When *func* is *None*, decorator usage
        is assumed. Returns the function.
        """
        return self.on(event, func=func, ttl=1)

    def on_any(self, func=None, ttl=-1):
        """
        Registers a function that is called every time an event is emitted. *ttl* defines the times
        to listen. Negative values mean infinity. When *func* is *None*, decorator usage is assumed.
        Returns the function.
        """
        def on_any(func):
            if not callable(func):
                return func

            listeners = self._tree[self.CB_KEY]
            if 0 <= self.max_listeners <= len(listeners):
                return func

            listener = Listener(func, None, ttl)
            listeners.append(listener)

            if self.new_listener:
                self.emit("new_listener", func)

            return func

        return on_any(func) if func else on_any

    def off(self, event, func=None):
        """
        Removes a function that is registered to an event. When *func* is *None*, decorator usage is
        assumed. Returns the function.
        """
        def off(func):
            branch = self._find_branch(event)
            if branch is None:
                return func

            self._remove_listener(branch, func)

            return func

        return off(func) if func else off

    def off_any(self, func=None):
        """
        Removes a function that was registered via :py:meth:`on_any`. When *func* is *None*,
        decorator usage is assumed. Returns the function.
        """
        def off_any(func):
            self._remove_listener(self._tree, func)

            return func

        return off_any(func) if func else off_any

    def off_all(self):
        """
        Removes all registered functions.
        """
        self._tree = self._new_branch()

    def listeners(self, event):
        """
        Returns all functions that are registered to an event. Wildcards are not applied.
        """
        branch = self._find_branch(event)
        if branch is None:
            return []

        return [listener.func for listener in branch[self.CB_KEY]]

    def listeners_any(self):
        """
        Returns all functions that were registered using :py:meth:`on_any`.
        """
        return [listener.func for listener in self._tree[self.CB_KEY]]

    def listeners_all(self):
        """
        Returns all registered functions.
        """
        listeners = list(self._tree[self.CB_KEY])

        branches = list(self._tree.values())
        for b in branches:
            if not isinstance(b, dict):
                continue

            branches.extend(b.values())

            listeners.extend(b[self.CB_KEY])

        return [listener.func for listener in listeners]

    def emit(self, event, *args, **kwargs):
        """
        Emits an *event*. All functions of events that match *event* are invoked with *args* and
        *kwargs* in the exact order of their registration. Wildcards might be applied.
        """
        parts = event.split(self.delimiter)

        if self.CB_KEY in parts:
            return

        listeners = list(self._tree[self.CB_KEY])
        branches = [self._tree]

        for p in parts:
            _branches = []
            for branch in branches:
                for k, b in branch.items():
                    if k == self.CB_KEY:
                        continue
                    if k == p:
                        _branches.append(b)
                    elif self.wildcard and self.WC_CHAR in (p, k):
                        _branches.append(b)
            branches = _branches

        for b in branches:
            listeners.extend(b[self.CB_KEY])

        # sort listeners by registration time
        listeners = sorted(listeners, key=lambda listener: listener.time)

        # call listeners in the order of their registration time
        for listener in sorted(listeners, key=lambda listener: listener.time):
            listener(*args, **kwargs)

        # remove listeners whose ttl value is 0
        for listener in listeners:
            if listener.ttl == 0:
                self.off(listener.event, func=listener.func)


class Listener(object):
    """
    A simple event listener class that wraps a function *func* for a specific *event* and that keeps
    track of the times to listen left.
    """

    def __init__(self, func, event, ttl):
        super(Listener, self).__init__()

        self.func = func
        self.event = event
        self.ttl = ttl

        # store the registration time
        self.time = time.time()

    def __call__(self, *args, **kwargs):
        """
        Invokes the wrapped function when ttl is non-zero, decreases the ttl value when positive and
        returns whether it reached zero or not.
        """
        if self.ttl != 0:
            self.func(*args, **kwargs)

        if self.ttl > 0:
            self.ttl -= 1

        return self.ttl == 0
