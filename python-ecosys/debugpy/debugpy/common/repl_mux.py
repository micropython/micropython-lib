"""Framing that lets the DAP channel share the REPL's one byte stream.

For a board with a single UART and no network, the stream carrying the REPL is
the only way in. `mpremote mount` already puts a second protocol on that stream
by marking its exchanges with `0x18`, and this reuses the marker and the code
namespace so one demux point can eventually serve both: codes 1..13 belong to
mount's filesystem RPC and are never emitted here.

The wire is the same in both directions:

    0x18 0x18                       one literal 0x18 in the plain byte stream
    0x18 <code> <lo> <hi> <payload> a framed message of `lo | hi << 8` bytes
    anything else                   plain bytes - program stdout one way,
                                    program stdin the other

`Demux` is the reader for that wire and is used unmodified at both ends, so
"the program's output reaches the terminal" and "a program calling `input()`
gets what the user typed" are the same code path, tested once. The length is
explicit rather than reusing the DAP message's own `Content-Length` header so
that a reader never inspects a payload to find where it ends: the only content
assumption on the wire is about `0x18`, and escaping removes that one.

Inbound bytes are credited (`CMD_DAP_ACK`), because the receive path this rides
on is a fixed ring that discards the tail of a packet when it overflows rather
than exerting back-pressure - the device drains it only when something polls,
and a target sitting in `time.sleep()` polls nothing. A sender that respects
the credit cannot overrun a receiver that has stopped listening; it blocks
instead, which is recoverable.
"""

import errno
import io
import select

# `mp_stream_p_t` request numbers, as `io.IOBase` hands them to `ioctl`.
_IOCTL_POLL = 3
_IOCTL_GET_FILENO = 10

# What both façades answer to `MP_STREAM_GET_FILENO`: a negative return from a
# Python `ioctl` is `MP_STREAM_ERROR` with this as its errno. Neither of them
# is a file, and saying so matters rather than being pedantry - a port built
# with `MICROPY_PY_SELECT_POSIX_OPTIMISATIONS` (the unix one) asks every object
# registered with `select.poll` for a descriptor and, when it gets a number,
# polls *that* and never calls the object's own `ioctl` again. A façade that
# answered 0 would have the poller watching stdin while the demux that actually
# holds the bytes was never pumped.
_NOT_A_FILE = -errno.EINVAL

MARKER = 0x18

# Shared with `mpremote`'s `fs_hook_cmds`, which owns 1..13.
CMD_DAP = 14
CMD_DAP_ACK = 15
# The DAP channel is over. Sent because the streams this rides on have no EOF
# of their own - an idle USB CDC interface and one nobody is holding both read
# as no bytes - so without it a host would wait out a finished session. Only
# the device sends it: a host that goes away drops DTR, which the device reads
# through `isconnected()`, and a client that merely detaches is the DAP
# protocol's own business.
CMD_DAP_EOF = 16

# Wire bytes a sender may have outstanding before the peer credits them. The
# smallest receive ring in the ports this runs on is 256 bytes
# (`MICROPY_HW_USB_CDC_RX_DATA_SIZE`), so this leaves room for a partly-drained
# one. Both ends must agree: `mpremote`'s copy is checked against this.
RX_CREDIT = 192

# Bytes of payload per frame. Bounds the reader's per-frame buffer, and is
# capped so that one whole frame always fits inside the credit window: a frame
# bigger than `RX_CREDIT` could never be sent at all, since the sender would
# wait for credit that only its own unsent bytes could earn. A DAP message
# longer than this is split across frames.
MAX_PAYLOAD = 128

# Consumed bytes a receiver may leave uncredited before it sends an ack. Small
# enough that a sender at the credit limit is released within one exchange,
# large enough that a steady stream does not ack every frame. A receiver that
# has drained everything acks regardless, so a sender is never left waiting on
# a threshold that will not be reached.
ACK_THRESHOLD = 64

# Outbound bytes queued before the DAP side reports itself unwritable. Reached
# only when the peer has stopped reading; the DAP layer then retries, which is
# back-pressure, where growing without limit would be a slow memory error on a
# device that has a few tens of kilobytes to spend.
MAX_OUTBOX = 4096

# Milliseconds a stalled console write waits for room before giving up and
# leaving the rest queued.
_STALL_MS = 100


def frame(code, payload):
    """One framed message: marker, code, two-byte length, payload."""
    n = len(payload)
    return bytes((MARKER, code, n & 0xFF, (n >> 8) & 0xFF)) + bytes(payload)


def _consume(buf, n):
    """Drop the first `n` bytes of `buf`, in place.

    `del buf[:n]` is the obvious spelling and raises on a MicroPython
    bytearray, which implements slice assignment but not slice deletion.
    Emptying it outright is the common case - a reader almost always takes
    everything queued - and is the one path here that allocates nothing.
    """
    if n >= len(buf):
        buf[:] = b""
    else:
        buf[:] = buf[n:]


def escape(data):
    """Plain bytes with the marker doubled, so a reader never mistakes one.

    A program that prints `0x18` is the case this exists for; it costs one
    extra byte per occurrence and nothing at all for output that has none.
    """
    data = bytes(data)
    if data.find(bytes((MARKER,))) < 0:
        return data
    return data.replace(bytes((MARKER,)), bytes((MARKER, MARKER)))


class Demux:
    """Reads the wire above into plain bytes and framed payload.

    `plain` and `dap` are drained by the caller; `credited` accumulates what
    the peer has reported consuming. `unknown_code` records the first code
    this reader has no handler for, which on a single-UART link means the two
    ends disagree about the protocol - worth reporting rather than skipping,
    since every later byte is then suspect.

    Feeding is incremental: a marker, a length or a payload split across two
    reads resumes where it left off, which is the normal case on a stream that
    delivers whatever a USB packet happened to contain.
    """

    _PLAIN, _CODE, _LEN0, _LEN1, _BODY = 0, 1, 2, 3, 4

    def __init__(self):
        self.plain = bytearray()
        self.dap = bytearray()
        self.credited = 0
        self.eof = False
        self.unknown_code = None
        self._state = self._PLAIN
        self._code = 0
        self._need = 0
        self._body = bytearray()

    def feed(self, data):
        data = bytes(data)
        i = 0
        end = len(data)
        while i < end:
            if self._state == self._PLAIN:
                # Copy up to the next marker in one go: plain bytes are the
                # bulk of the traffic in the stdout direction and scanning
                # them one at a time is the whole cost of the layer.
                j = data.find(bytes((MARKER,)), i)
                if j < 0:
                    self.plain += data[i:]
                    return
                self.plain += data[i:j]
                i = j + 1
                self._state = self._CODE
                continue

            c = data[i]
            i += 1
            if self._state == self._CODE:
                if c == MARKER:
                    self.plain.append(MARKER)  # escaped literal
                    self._state = self._PLAIN
                else:
                    self._code = c
                    self._state = self._LEN0
            elif self._state == self._LEN0:
                self._need = c
                self._state = self._LEN1
            elif self._state == self._LEN1:
                self._need |= c << 8
                self._body = bytearray()
                self._state = self._BODY if self._need else self._PLAIN
                if not self._need:
                    self._deliver()
            else:  # _BODY
                self._body.append(c)
                if len(self._body) == self._need:
                    self._deliver()
                    self._state = self._PLAIN

    def _deliver(self):
        if self._code == CMD_DAP:
            self.dap += self._body
        elif self._code == CMD_DAP_ACK:
            if len(self._body) >= 2:
                self.credited += self._body[0] | (self._body[1] << 8)
        elif self._code == CMD_DAP_EOF:
            self.eof = True
        elif self.unknown_code is None:
            self.unknown_code = self._code

    def take_plain(self, n):
        out = bytes(self.plain[:n])
        _consume(self.plain, len(out))
        return out

    def take_dap(self, n):
        out = bytes(self.dap[:n])
        _consume(self.dap, len(out))
        return out


class ReplMux:
    """Owns the REPL stream and hands out the two façades that share it.

    `console` goes wherever the runtime's stdout is diverted - a `dupterm`
    slot on the ports where that reaches every byte - and `dap` is handed to
    `debugpy.listen_stream()`. They are separate objects because the bytes
    arriving at a `write()` are the only thing that distinguishes program
    output from a DAP frame, so one object could not tell them apart.

    Everything either façade emits is appended to one outbound buffer in whole
    frames and flushed from there, so a partial write to the underlying port
    can never interleave two messages: the port sees frames in the order they
    were produced, or it sees a prefix of that order.
    """

    def __init__(self, port=None):
        self._port = None
        self._poller = None
        self._write_poller = None
        self._out = bytearray()
        self._demux = Demux()
        self._consumed = 0  # payload bytes taken from `dap` since the last ack
        self._byte = bytearray(1)
        self.console = _PlainSide(self)
        self.dap = _DapSide(self)
        if port is not None:
            self.attach(port)

    def attach(self, port):
        """Take `port` as the real stream.

        Separate from `__init__` because on a port where the diversion is a
        `dupterm` slot, the object being displaced *is* the real stream, and
        it is only known once the swap has happened.
        """
        self._port = port
        self._poller = select.poll()
        self._poller.register(port, select.POLLIN)
        self._write_poller = select.poll()
        self._write_poller.register(port, select.POLLOUT)
        # The DAP façade inherits whatever the real stream has instead of EOF.
        # A USB CDC interface has none - an idle one and one nobody is holding
        # both read as no bytes - but it does have `isconnected()`, the DTR
        # line the host raises on open and the kernel drops when the last
        # opener goes, which is how a session notices its host disappeared.
        self.dap.isconnected = getattr(port, "isconnected", None)

    # -- outbound ---------------------------------------------------------

    def _emit(self, data):
        """Queue whole frames and push what the port will take. Never raises.

        An exception out of the console façade's `write()` would deactivate the
        stdout diversion it sits in, which on a single-stream board silently
        removes the console and the debug channel at once, so nothing here is
        allowed to escape. A short write is not a failure: what did not go out
        stays queued and leaves with the next call.
        """
        self._out += data
        self._flush()

    def _flush(self, timeout_ms=0):
        while self._out:
            if self._port is None:
                return False
            if not self._write_poller.poll(timeout_ms):
                return False
            try:
                n = self._port.write(self._out)
            except OSError:
                return False  # EAGAIN, or the port has gone; either way, later
            if not n:
                return False
            _consume(self._out, n)
        return True

    # -- inbound ----------------------------------------------------------

    def pump(self, timeout_ms=0):
        """Move whatever the port has into the demux, and credit it.

        Read one byte at a time behind a fresh zero-timeout poll, for the
        reason `StreamTransport.recv` gives: a bulk `readinto` on a stream
        whose read genuinely blocks (a plain file, as against a CDC driver
        that always returns immediately) would wait for bytes that may never
        come, because the request is looped internally until the buffer fills.

        Credit is counted here rather than where a payload is handed on,
        because what the credit protects is the receive ring, and a byte read
        out of it has already freed its place there whatever happens to it
        next. Counting it later would credit a frame's overhead once per
        partial read of it, which over-reports and defeats the limit.
        """
        if self._port is None:
            return False
        if not self._poller.poll(timeout_ms):
            self._send_ack(force=True)
            return False
        got = False
        while True:
            try:
                r = self._port.readinto(self._byte)
            except OSError:
                break
            if not r:
                break
            self._demux.feed(self._byte)
            self._consumed += r
            got = True
            if self._consumed >= ACK_THRESHOLD:
                self._send_ack()  # mid-burst, so a long one does not stall the peer
            if not self._poller.poll(0):
                break
        self._send_ack(force=True)
        return got

    def _send_ack(self, force=False):
        """Tell the peer how much of its traffic has left this end's buffer.

        Credit is what stops a sender overrunning a receive ring that drops
        the tail of a packet on overflow. It is reported in wire bytes, the
        unit the ring holds, so the sender does not have to model framing.
        """
        if self._consumed and (force or self._consumed >= ACK_THRESHOLD):
            n = self._consumed
            self._consumed = 0
            self._emit(frame(CMD_DAP_ACK, bytes((n & 0xFF, (n >> 8) & 0xFF))))

    @property
    def unknown_code(self):
        return self._demux.unknown_code

    def detach(self):
        """Push out what is queued and give the real stream back.

        Returns the port so the caller can put it where it found it. The flush
        is bounded rather than unconditional: a peer that has stopped reading
        must not be able to keep the stream split forever, and by this point
        whatever is still queued is the tail of a session that is over.
        """
        if self._port is not None:
            # Last framed message on the channel, and the peer's only notice
            # that the session ended rather than went quiet.
            self._emit(frame(CMD_DAP_EOF, b""))
        self._flush(_STALL_MS)
        port = self._port
        self._port = None
        self._poller = None
        self._write_poller = None
        self.dap.isconnected = None
        return port

    def close(self):
        self.detach()


class _PlainSide(io.IOBase):
    """The program's own stdout and stdin, escaped onto the shared stream.

    `io.IOBase` rather than a plain class because both places this object goes
    demand the native stream protocol: `os.dupterm` raises `OSError: stream
    operation not supported` without it, and `select.poll().register()` needs
    the `ioctl`.
    """

    def __init__(self, mux):
        self._mux = mux

    def write(self, buf):
        n = len(buf)
        mux = self._mux
        mux._emit(escape(buf))
        if len(mux._out) > MAX_OUTBOX:
            # Program output is never dropped, so a peer that has stopped
            # reading slows the program down instead. Bounded: one flush
            # attempt, not a wait for the whole queue to leave.
            mux._flush(_STALL_MS)
        return n  # every byte was accepted; delivery is the outbound queue's job

    def readinto(self, buf, nbytes=None):
        mux = self._mux
        mux.pump()
        want = len(buf) if nbytes is None else min(nbytes, len(buf))
        data = mux._demux.take_plain(want)
        buf[: len(data)] = data
        return len(data)

    def ioctl(self, op, arg):
        if op == _IOCTL_POLL:
            mux = self._mux
            mux.pump()
            ret = 0
            if arg & 1 and mux._demux.plain:  # MP_STREAM_POLL_RD
                ret |= 1
            if arg & 4:  # MP_STREAM_POLL_WR - the outbound queue always accepts
                ret |= 4
            return ret
        if op == _IOCTL_GET_FILENO:
            return _NOT_A_FILE
        return 0


class _DapSide(io.IOBase):
    """The DAP channel, framed onto the shared stream.

    Handed to `debugpy.listen_stream()`, which registers it with `select.poll`
    for both directions and calls `poll()` fresh on every `recv`/`send`. That
    makes `ioctl` the place the inbound side is pumped: it runs on every wait
    the DAP layer does, which under `settrace` is at every trace event.
    """

    def __init__(self, mux):
        self._mux = mux
        # Set by `ReplMux.attach` to the real stream's own liveness test, or
        # left None where it has none. An instance attribute rather than a
        # method so that `getattr(stream, "isconnected", None)` - what the
        # boot script asks - can answer "this stream cannot tell you".
        self.isconnected = None

    def write(self, buf):
        mux = self._mux
        data = bytes(buf)
        for i in range(0, len(data), MAX_PAYLOAD):
            mux._emit(frame(CMD_DAP, data[i : i + MAX_PAYLOAD]))
        return len(data)

    def readinto(self, buf, nbytes=None):
        mux = self._mux
        mux.pump()
        want = len(buf) if nbytes is None else min(nbytes, len(buf))
        data = mux._demux.take_dap(want)
        buf[: len(data)] = data
        return len(data)

    def ioctl(self, op, arg):
        if op == _IOCTL_POLL:
            mux = self._mux
            mux.pump()
            ret = 0
            if arg & 1 and mux._demux.dap:  # MP_STREAM_POLL_RD
                ret |= 1
            if arg & 4 and len(mux._out) <= MAX_OUTBOX:  # MP_STREAM_POLL_WR
                ret |= 4
            return ret
        if op == _IOCTL_GET_FILENO:
            return _NOT_A_FILE
        return 0
