# coding: utf-8


import unittest

from pymitter import EventEmitter


class AllTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(AllTestCase, self).__init__(*args, **kwargs)

        self.ee1 = EventEmitter()
        self.ee2 = EventEmitter(wildcard=True)
        self.ee3 = EventEmitter(wildcard=True, delimiter=":")
        self.ee4 = EventEmitter(new_listener=True)
        self.ee5 = EventEmitter(max_listeners=1)

    def test_1_callback_usage(self):
        stack = []

        def handler(arg):
            stack.append("1_callback_usage_" + arg)

        self.ee1.on("1_callback_usage", handler)

        self.ee1.emit("1_callback_usage", "foo")
        self.assertTrue(stack[-1] == "1_callback_usage_foo")

    def test_1_decorator_usage(self):
        stack = []

        @self.ee1.on("1_decorator_usage")
        def handler(arg):
            stack.append("1_decorator_usage_" + arg)

        self.ee1.emit("1_decorator_usage", "bar")
        self.assertTrue(stack[-1] == "1_decorator_usage_bar")

    def test_1_ttl_on(self):
        stack = []

        @self.ee1.on("1_ttl_on", ttl=1)
        def handler(arg):
            stack.append("1_ttl_on_" + arg)

        self.ee1.emit("1_ttl_on", "foo")
        self.assertTrue(stack[-1] == "1_ttl_on_foo")

        self.ee1.emit("1_ttl_on", "bar")
        self.assertTrue(stack[-1] == "1_ttl_on_foo")

    def test_1_ttl_once(self):
        stack = []

        @self.ee1.once("1_ttl_once")
        def handler(arg):
            stack.append("1_ttl_once_" + arg)

        self.ee1.emit("1_ttl_once", "foo")
        self.assertTrue(stack[-1] == "1_ttl_once_foo")

        self.ee1.emit("1_ttl_once", "bar")
        self.assertTrue(stack[-1] == "1_ttl_once_foo")

    def test_2_on_all(self):
        stack = []

        @self.ee2.on("2_on_all.*")
        def handler():
            stack.append("2_on_all")

        self.ee2.emit("2_on_all.foo")
        self.assertTrue(stack[-1] == "2_on_all")

    def test_2_emit_all(self):
        stack = []

        @self.ee2.on("2_emit_all.foo")
        def handler():
            stack.append("2_emit_all.foo")

        self.ee2.emit("2_emit_all.*")
        self.assertTrue(stack[-1] == "2_emit_all.foo")

    def test_3_delimiter(self):
        stack = []

        @self.ee3.on("3_delimiter:*")
        def handler():
            stack.append("3_delimiter")

        self.ee3.emit("3_delimiter:foo")
        self.assertTrue(stack[-1] == "3_delimiter")

    def test_4_new(self):
        stack = []

        @self.ee4.on("new_listener")
        def handler(func, event=None):
            stack.append((func, event))

        def newhandler():
            pass

        self.ee4.on("4_new", newhandler)

        self.assertTrue(stack[-1] == (newhandler, "4_new"))

    def test_5_max(self):
        stack = []

        @self.ee5.on("5_max")
        def handler1():
            stack.append("5_max_1")

        @self.ee5.on("5_max")
        def handler2():
            stack.append("5_max_2")

        self.ee5.emit("5_max")
        self.assertTrue(stack[-1] == "5_max_1")


if __name__ == "__main__":
    unittest.main()
