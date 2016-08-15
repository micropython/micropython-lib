umqtt.robust
============

umqtt is a simple MQTT client for MicroPython. (Note that it uses some
MicroPython shortcuts and doesn't work with CPython). It consists of
two submodules: umqtt.simple and umqtt.robust. umqtt.robust is built
on top of umqtt.simple and adds auto-reconnect facilities for some of
networking errors.
