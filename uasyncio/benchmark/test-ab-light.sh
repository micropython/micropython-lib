#!/bin/sh
#
# This in one-shot scripts to test "light load" uasyncio HTTP server using
# Apache Bench (ab).
#

micropython -O test_http_server_light.py &
sleep 1

ab -n10000 -c100 http://localhost:8081/

kill %1
