import sys
import os
from multiprocessing import Process, Pipe, Connection

def f(conn):
    conn.send([42, None, 'hello'])
    conn.send([42, 42, 42])
    conn.close()

if __name__ == '__main__':
    parent_conn, child_conn = Pipe(False)
    print(parent_conn, child_conn)
    p = Process(target=f, args=(child_conn,))
    # Extension: need to call this for uPy
    p.register_pipe(parent_conn, child_conn)
    p.start()
    print(parent_conn.recv())
    print(parent_conn.recv())
    p.join()
