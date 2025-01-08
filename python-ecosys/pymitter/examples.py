# coding: utf-8

# python imports
import os
import sys
from pymitter import EventEmitter


# create an EventEmitter instance
ee = EventEmitter(wildcard=True, new_listener=True, max_listeners=-1)


@ee.on("new_listener")
def on_new(func, event=None):
    print("added listener", event, func)


@ee.on("foo")
def handler_foo1(arg):
    print("foo handler 1 called with", arg)


@ee.on("foo")
def handler_foo2(arg):
    print("foo handler 2 called with", arg)


@ee.on("foo.*", ttl=1)
def handler_fooall(arg):
    print("foo.* handler called with", arg)


@ee.on("foo.bar")
def handler_foobar(arg):
    print("foo.bar handler called with", arg)


@ee.on_any()
def handler_any(*args, **kwargs):
    print("called every time")


print("emit foo")
ee.emit("foo", "test")
print(10 * "-")

print("emit foo.bar")
ee.emit("foo.bar", "test")
print(10 * "-")

print("emit foo.*")
ee.emit("foo.*", "test")
print(10 * "-")
