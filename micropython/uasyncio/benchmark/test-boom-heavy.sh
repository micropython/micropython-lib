#!/bin/sh
#
# This in one-shot scripts to test "heavy load" uasyncio HTTP server using
# Boom tool https://github.com/tarekziade/boom .
#
# Note that this script doesn't test performance, but rather test functional
# correctness of uasyncio server implementation, while serving large amounts
# of data (guaranteedly more than a socket buffer). Thus, this script should
# not be used for benchmarking.
#

if [ ! -d .venv-boom ]; then
    virtualenv .venv-boom
    . .venv-boom/bin/activate
    # PyPI currently has 0.8 which is too old
    #pip install boom
    pip install git+https://github.com/tarekziade/boom
else
    . .venv-boom/bin/activate
fi


micropython -X heapsize=300000000 -O test_http_server_heavy.py &
sleep 1

PYTHONPATH=. boom -n1000 -c30 http://localhost:8081 --post-hook=boom_uasyncio.validate

kill %1
