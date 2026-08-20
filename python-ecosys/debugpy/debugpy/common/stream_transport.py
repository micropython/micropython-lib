"""Socket-shaped adapter for running the DAP channel over a stream, not a socket."""

import select

# How long a wait that was asked to block forever may sit inside one poll
# before the liveness check runs again. The line `is_connected` reads is not
# something a poll can wait on, so a blocking wait would otherwise never
# notice the host letting go. A bound on how quickly that is noticed, not a
# timeout: a wait carrying a real one is still governed by it.
_LIVENESS_SLICE_MS = 100


class StreamTransport:
    """Presents a reader/writer stream pair as a socket to `JsonMessageChannel`.

    For boards with a dedicated CDC interface for DAP (no shared REPL/stdout
    byte stream to demux) - the interface `messaging.py` and `debug_session.py`
    need is exactly `recv`/`send`/`settimeout`/`close`, so this wraps the
    stream to present that shape rather than changing anything downstream of
    `self.sock`.

    `recv` raises `OSError(11)` (EAGAIN) when no data has arrived within the
    current timeout, matching a non-blocking socket, and returns `b""` once
    the stream is at EOF. `send` writes once and reports how much went out,
    also matching a socket, raising EAGAIN only when nothing could be
    written; driving a whole frame out is `messaging.py`'s `_send_all`, the
    one place that knows where the frame boundary is. `settimeout` is mutated
    repeatedly at runtime by `public_api.py`/`debug_session.py` and governs
    both directions, matching a real socket; `poll(ms)` is called fresh on
    every `recv`/`send` rather than cached, so each change takes effect
    immediately.

    `is_connected`, when the runtime has something to offer, is a callable
    reporting whether the host still holds the other end - see `_peer_gone`.
    """

    def __init__(self, reader, writer=None, is_connected=None):
        self._reader = reader
        self._writer = writer if writer is not None else reader
        self._timeout = None  # seconds, or None = block forever
        self._eof = False
        self._is_connected = is_connected
        self._had_traffic = False
        self._was_held = is_connected is not None and bool(is_connected())
        self._poller = select.poll()
        self._poller.register(self._reader, select.POLLIN)
        self._write_poller = select.poll()
        self._write_poller.register(self._writer, select.POLLOUT)
        self._buf = bytearray()  # grown to the largest `n` seen, reused across recv() calls

    def settimeout(self, seconds):
        self._timeout = seconds

    def _peer_gone(self):
        """Has the host held this channel and then let go of it?

        A USB CDC interface never reaches EOF. An idle one and one whose host
        has vanished read identically - no bytes - so a session stopped at a
        breakpoint would wait for a `continue` that cannot come, and the board
        would need a power cycle. `is_connected` is whatever the runtime has
        instead: on stm32 it is `pyb.USB_VCP.isconnected()`, the interface's
        DTR line, raised by the host when it opens the port and dropped by the
        kernel when the last opener goes away.

        It counts only once the channel has been held, because the line goes
        up and down for reasons that are not a session ending: a host may open
        an idle interface briefly just to check that it can. Down on its own
        therefore says nothing; down after the channel was held is the peer
        leaving. Held means either of two things, and which one applies is
        decided by whether anyone was on the far end when the channel was
        made:

        - Nobody was, so the channel has to earn the signal - a byte has to
          cross it. This is the dedicated-DAP-interface case: nothing holds
          that interface between `listen_stream()` and the client's first
          connect, so its line being down at any point before then is the
          ordinary state and not a peer.
        - Somebody was, recorded at construction as `_was_held`. This is the
          case where DAP shares the stream the host is already using to drive
          the board: that hold predates the channel, so nothing but the host
          leaving can drop it, and waiting for traffic would mean a client
          that never sends anything holds the stream forever.
        """
        if self._is_connected is None or not (self._had_traffic or self._was_held):
            return False
        return not self._is_connected()

    def _wait(self, poller, timeout_ms):
        """Poll for readiness, giving up early once the peer has gone.

        Returns whatever `poll` returned, which is falsy both when the wait
        timed out and when the peer left; callers separate the two with
        `_peer_gone()`. A wait asked to block forever is served in slices so
        that check gets to run - see `_LIVENESS_SLICE_MS`.
        """
        if timeout_ms is not None:
            return poller.poll(timeout_ms)
        while True:
            ready = poller.poll(_LIVENESS_SLICE_MS)
            if ready or self._peer_gone():
                return ready

    def recv(self, n):
        if self._eof:
            return b""
        if self._peer_gone():
            self._eof = True
            return b""
        timeout_ms = None if self._timeout is None else max(0, int(self._timeout * 1000))
        if not self._wait(self._poller, timeout_ms):
            if self._peer_gone():
                self._eof = True
                return b""
            raise OSError(11)  # EAGAIN: no data within the timeout

        # `.read()`/`.readinto()` loop internally until the buffer is full
        # (py/stream.c's mp_stream_rw) - on a stream backed by a genuinely
        # blocking read (a plain POSIX file, as opposed to a UART/CDC driver
        # that always returns immediately), a second internal call would
        # block waiting for bytes that may never come. Reading one byte at a
        # time, re-checking readiness with a zero-timeout poll before every
        # further byte, never makes a read the poller hasn't already
        # confirmed data for.
        if len(self._buf) < n:
            self._buf = bytearray(n)
        mv = memoryview(self._buf)
        got = 0
        while got < n:
            r = self._reader.readinto(mv[got : got + 1])
            if r is None:
                break  # raced the poll result - not actually ready
            if not r:
                self._eof = True
                break
            got += r
            if got < n and not self._poller.poll(0):
                break

        if got == 0:
            if self._eof:
                return b""
            raise OSError(11)
        self._had_traffic = True
        return bytes(mv[:got])

    def send(self, data):
        # A short write is normal, not exceptional: a CDC interface takes at
        # most its transmit buffer per call (1024 bytes on stm32) and reports
        # the count, exactly as a socket reports a short send. Reporting that
        # count is what lets the caller resume from the right offset - a
        # whole-buffer contract would have to raise once the timeout expired
        # mid-frame, throwing away the count of what had already gone out, and
        # the retry would then re-send that prefix and desynchronise the
        # Content-Length framing it was meant to protect.
        timeout_ms = None if self._timeout is None else max(0, int(self._timeout * 1000))
        if not self._wait(self._write_poller, timeout_ms):
            raise OSError(11)  # EAGAIN: no room within the timeout
        # `write()` answers a non-blocking stream that took nothing with None
        # rather than 0, so both are treated as "came back not ready after
        # all" - the poll above can only promise room at the moment it ran.
        written = self._writer.write(memoryview(data))
        if not written:
            raise OSError(11)
        return written

    def close(self):
        try:
            self._reader.close()
        except OSError:
            pass
        if self._writer is not self._reader:
            try:
                self._writer.close()
            except OSError:
                pass
