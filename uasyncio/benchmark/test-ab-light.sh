#!/bin/sh
#
# This in one-shot scripts to test "light load" uasyncio HTTP server using
# Apache Bench (ab).
#

#python3.4.2 test_http_server_light.py &
#micropython -O test_http_server_light.py &

#python3.4.2 test_http_server_medium.py &
micropython -O -X heapsize=200wK test_http_server_medium.py &

sleep 1

ab -n10000 -c100 http://localhost:8081/

kill %1
