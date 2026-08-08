"""Socket-shaped adapter for running the DAP channel over a stream, not a socket."""

import select


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
    """

    def __init__(self, reader, writer=None):
        self._reader = reader
        self._writer = writer if writer is not None else reader
        self._timeout = None  # seconds, or None = block forever
        self._eof = False
        self._poller = select.poll()
        self._poller.register(self._reader, select.POLLIN)
        self._write_poller = select.poll()
        self._write_poller.register(self._writer, select.POLLOUT)
        self._buf = bytearray()  # grown to the largest `n` seen, reused across recv() calls

    def settimeout(self, seconds):
        self._timeout = seconds

    def recv(self, n):
        if self._eof:
            return b""
        timeout_ms = None if self._timeout is None else max(0, int(self._timeout * 1000))
        if not self._poller.poll(timeout_ms):
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
        if not self._write_poller.poll(timeout_ms):
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
