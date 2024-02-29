# This module should be imported from REPL, not run from command line.
import binascii
import hashlib
import network
import os
import socket
import sys
import websocket
import io

listen_s = None
client_s = None

DEBUG = 0

_DEFAULT_STATIC_HOST = const("https://felix.dogcraft.de/webrepl/")
_WELCOME_PROMPT = const("\r\nWebREPL connected\r\n>>> ")
static_host = _DEFAULT_STATIC_HOST
webrepl_pass = None

class WebreplWrapper(io.IOBase):
    def __init__(self, sock):
        self.sock = sock
        self.sock.ioctl(9, 2)
        if webrepl_pass is not None:
            self.pw = bytearray(16)
            self.pwPos = 0
            self.sock.write("Password: ")
        else:
            self.pw = None
            self.sock.write(_WELCOME_PROMPT);

    def readinto(self, buf):
        if self.pw is not None:
            buf = bytearray(1)
            while True:
                l = self.sock.readinto(buf)
                if l is None:
                    continue
                if l <= 0:
                    return l
                if buf[0] == 10 or buf[0] == 13:
                    print("Authenticating with:")
                    print(self.pw[0:self.pwPos])
                    if bytes(self.pw[0:self.pwPos]) == webrepl_pass:
                        self.pw = None
                        del self.pwPos
                        self.sock.write(_WELCOME_PROMPT)
                        break
                    else:
                        print(bytes(self.pw[0:self.pwPos]))
                        print(webrepl_pass)
                        self.sock.write("\r\nAccess denied\r\n")
                        return 0
                else:
                    if self.pwPos < len(self.pw):
                        self.pw[self.pwPos] = buf[0]
                        self.pwPos = self.pwPos + 1
        return self.sock.readinto(buf)

    def write(self, buf):
        if self.pw is not None:
            return len(buf)
        return self.sock.write(buf)

    def ioctl(self, kind, arg):
        if kind == 4:
            self.sock.close()
            return 0
        return -1

    def close(self):
        self.sock.close()

def server_handshake(cl):
    req = cl.makefile("rwb", 0)
    # Skip HTTP GET line.
    l = req.readline()
    if DEBUG:
        sys.stdout.write(repr(l))

    webkey = None
    upgrade = False
    websocket = False

    while True:
        l = req.readline()
        if not l:
            # EOF in headers.
            return False
        if l == b"\r\n":
            break
        if DEBUG:
            sys.stdout.write(l)
        h, v = [x.strip() for x in l.split(b":", 1)]
        if DEBUG:
            print((h, v))
        if h == b"Sec-WebSocket-Key":
            webkey = v
        elif h == b"Connection" and b"Upgrade" in v:
            upgrade = True
        elif h == b"Upgrade" and v == b"websocket":
            websocket = True

    if not (upgrade and websocket and webkey):
        return False

    if DEBUG:
        print("Sec-WebSocket-Key:", webkey, len(webkey))

    d = hashlib.sha1(webkey)
    d.update(b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11")
    respkey = d.digest()
    respkey = binascii.b2a_base64(respkey)[:-1]
    if DEBUG:
        print("respkey:", respkey)

    cl.send(
        b"""\
HTTP/1.1 101 Switching Protocols\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Accept: """
    )
    cl.send(respkey)
    cl.send("\r\n\r\n")

    return True


def send_html(cl):
    cl.send(
        b"""\
HTTP/1.0 200 OK\r
\r
<base href=\""""
    )
    cl.send(static_host)
    cl.send(
        b"""\"></base>\r
<script src="webreplv2_content.js"></script>\r
"""
    )
    cl.close()


def setup_conn(port, accept_handler):
    global listen_s
    listen_s = socket.socket()
    listen_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    ai = socket.getaddrinfo("0.0.0.0", port)
    addr = ai[0][4]

    listen_s.bind(addr)
    listen_s.listen(1)
    if accept_handler:
        listen_s.setsockopt(socket.SOL_SOCKET, 20, accept_handler)
    for i in (network.AP_IF, network.STA_IF):
        iface = network.WLAN(i)
        if iface.active():
            print("WebREPL server started on http://%s:%d/" % (iface.ifconfig()[0], port))
    return listen_s


def accept_conn(listen_sock):
    global client_s
    cl, remote_addr = listen_sock.accept()

    if not server_handshake(cl):
        send_html(cl)
        return False

    prev = os.dupterm(None)
    os.dupterm(prev)
    if prev:
        print("\nConcurrent WebREPL connection from", remote_addr, "rejected")
        cl.close()
        return False
    print("\nWebREPL connection from:", remote_addr)
    client_s = cl

    ws = websocket.websocket(cl, True)
    ws = WebreplWrapper(ws)
    cl.setblocking(False)
    # notify REPL on socket incoming data (ESP32/ESP8266-only)
    if hasattr(os, "dupterm_notify"):
        cl.setsockopt(socket.SOL_SOCKET, 20, os.dupterm_notify)
    os.dupterm(ws)

    return True


def stop():
    global listen_s, client_s
    os.dupterm(None)
    if client_s:
        client_s.close()
    if listen_s:
        listen_s.close()


def start(port=8266, password=None, accept_handler=accept_conn):
    global static_host, webrepl_pass
    stop()
    webrepl_pass = password
    if password is None:
        try:
            import webrepl_cfg

            webrepl_pass = webrepl_cfg.PASS
            if hasattr(webrepl_cfg, "BASE"):
                static_host = webrepl_cfg.BASE
        except:
            print("WebREPL is not configured, run 'import webrepl_setup'")

    if webrepl_pass is not None:
        webrepl_pass = webrepl_pass.encode()

    s = setup_conn(port, accept_handler)

    if accept_handler is None:
        print("Starting webrepl in foreground mode")
        # Run accept_conn to serve HTML until we get a websocket connection.
        while not accept_conn(s):
            pass
    elif password is None:
        print("Started webrepl in normal mode")
    else:
        print("Started webrepl in manual override mode")


def start_foreground(port=8266, password=None):
    start(port, password, None)
