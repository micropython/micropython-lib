# MicroPython aioble module
# MIT license; Copyright (c) 2021 Jim Mussared

from micropython import const
from collections import deque
import bluetooth
import asyncio

from .core import (
    ensure_active,
    ble,
    log_info,
    log_error,
    log_warn,
    register_irq_handler,
    GattError,
)
from .device import DeviceConnection, DeviceTimeout

_registered_characteristics = {}

_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)
_IRQ_GATTS_INDICATE_DONE = const(20)

_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)
_FLAG_INDICATE = const(0x0020)

_FLAG_READ_ENCRYPTED = const(0x0200)
_FLAG_READ_AUTHENTICATED = const(0x0400)
_FLAG_READ_AUTHORIZED = const(0x0800)
_FLAG_WRITE_ENCRYPTED = const(0x1000)
_FLAG_WRITE_AUTHENTICATED = const(0x2000)
_FLAG_WRITE_AUTHORIZED = const(0x4000)

_FLAG_WRITE_CAPTURE = const(0x10000)


_WRITE_CAPTURE_QUEUE_LIMIT = const(10)


def _server_irq(event, data):
    if event == _IRQ_GATTS_WRITE:
        conn_handle, attr_handle = data
        Characteristic._remote_write(conn_handle, attr_handle)
    elif event == _IRQ_GATTS_READ_REQUEST:
        conn_handle, attr_handle = data
        return Characteristic._remote_read(conn_handle, attr_handle)
    elif event == _IRQ_GATTS_INDICATE_DONE:
        conn_handle, value_handle, status = data
        Characteristic._indicate_done(conn_handle, value_handle, status)


def _server_shutdown():
    global _registered_characteristics
    _registered_characteristics = {}
    if hasattr(BaseCharacteristic, "_capture_task"):
        BaseCharacteristic._capture_task.cancel()
        del BaseCharacteristic._capture_queue
        del BaseCharacteristic._capture_write_event
        del BaseCharacteristic._capture_consumed_event
        del BaseCharacteristic._capture_task


register_irq_handler(_server_irq, _server_shutdown)


class Service:
    def __init__(self, uuid):
        self.uuid = uuid
        self.characteristics = []

    # Generate tuple for gatts_register_services.
    def _tuple(self):
        return (self.uuid, tuple(c._tuple() for c in self.characteristics))


class BaseCharacteristic:
    def _register(self, value_handle):
        self._value_handle = value_handle
        _registered_characteristics[value_handle] = self
        if self._initial is not None:
            self.write(self._initial)
            self._initial = None

    # Read value from local db.
    def read(self):
        if self._value_handle is None:
            return self._initial or b""
        else:
            return ble.gatts_read(self._value_handle)

    # Write value to local db, and optionally notify/indicate subscribers.
    def write(self, data, send_update=False):
        if self._value_handle is None:
            self._initial = data
        else:
            ble.gatts_write(self._value_handle, data, send_update)

    # When the a capture-enabled characteristic is created, create the
    # necessary events (if not already created).
    @staticmethod
    def _init_capture():
        if hasattr(BaseCharacteristic, "_capture_queue"):
            return

        BaseCharacteristic._capture_queue = deque((), _WRITE_CAPTURE_QUEUE_LIMIT)
        BaseCharacteristic._capture_write_event = asyncio.ThreadSafeFlag()
        BaseCharacteristic._capture_consumed_event = asyncio.ThreadSafeFlag()
        BaseCharacteristic._capture_task = asyncio.create_task(
            BaseCharacteristic._run_capture_task()
        )

    # Monitor the shared queue for incoming characteristic writes and forward
    # them sequentially to the individual characteristic events.
    @staticmethod
    async def _run_capture_task():
        write = BaseCharacteristic._capture_write_event
        consumed = BaseCharacteristic._capture_consumed_event
        q = BaseCharacteristic._capture_queue

        while True:
            if len(q):
                conn, data, characteristic = q.popleft()
                # Let the characteristic waiting in `written()` know that it
                # can proceed.
                characteristic._write_data = (conn, data)
                characteristic._write_event.set()
                # Wait for the characteristic to complete `written()` before
                # continuing.
                await consumed.wait()

            if not len(q):
                await write.wait()

    # Wait for a write on this characteristic. Returns the connection that did
    # the write, or a tuple of (connection, value) if capture is enabled for
    # this characteristics.
    async def written(self, timeout_ms=None):
        if not hasattr(self, "_write_event"):
            # Not a writable characteristic.
            return

        # If no write has been seen then we need to wait. If the event has
        # already been set this will clear the event and continue
        # immediately. In regular mode, this is set by the write IRQ
        # directly (in _remote_write). In capture mode, this is set when it's
        # our turn by _capture_task.
        with DeviceTimeout(None, timeout_ms):
            await self._write_event.wait()

        # Return the write data and clear the stored copy.
        # In default usage this will be just the connection handle.
        # In capture mode this will be a tuple of (connection_handle, received_data)
        data = self._write_data
        self._write_data = None

        if self.flags & _FLAG_WRITE_CAPTURE:
            # Notify the shared queue monitor that the event has been consumed
            # by the caller to `written()` and another characteristic can now
            # proceed.
            BaseCharacteristic._capture_consumed_event.set()

        return data

    def on_read(self, connection):
        return 0

    def _remote_write(conn_handle, value_handle):
        if characteristic := _registered_characteristics.get(value_handle, None):
            # If we've gone from empty to one item, then wake something
            # blocking on `await char.written()`.

            conn = DeviceConnection._connected.get(conn_handle, None)

            if characteristic.flags & _FLAG_WRITE_CAPTURE:
                # For capture, we append the connection and the written value
                # value to the shared queue along with the matching characteristic object.
                # The deque will enforce the max queue len.
                data = characteristic.read()
                BaseCharacteristic._capture_queue.append((conn, data, characteristic))
                BaseCharacteristic._capture_write_event.set()
            else:
                # Store the write connection handle to be later used to retrieve the data
                # then set event to handle in written() task.
                characteristic._write_data = conn
                characteristic._write_event.set()

    def _remote_read(conn_handle, value_handle):
        if characteristic := _registered_characteristics.get(value_handle, None):
            return characteristic.on_read(DeviceConnection._connected.get(conn_handle, None))


class Characteristic(BaseCharacteristic):
    def __init__(
        self,
        service,
        uuid,
        read=False,
        write=False,
        write_no_response=False,
        notify=False,
        indicate=False,
        initial=None,
        capture=False,
    ):
        service.characteristics.append(self)
        self.descriptors = []

        flags = 0
        if read:
            flags |= _FLAG_READ
        if write or write_no_response:
            flags |= (_FLAG_WRITE if write else 0) | (
                _FLAG_WRITE_NO_RESPONSE if write_no_response else 0
            )
            if capture:
                # Capture means that we keep track of all writes, and capture
                # their values (and connection) in a queue. Otherwise we just
                # track the connection of the most recent write.
                flags |= _FLAG_WRITE_CAPTURE
                BaseCharacteristic._init_capture()

            # Set when this characteristic has a value waiting in self._write_data.
            self._write_event = asyncio.ThreadSafeFlag()
            # The connection of the most recent write, or a tuple of
            # (connection, data) if capture is enabled.
            self._write_data = None
        if notify:
            flags |= _FLAG_NOTIFY
        if indicate:
            flags |= _FLAG_INDICATE
            # TODO: This should probably be a dict of connection to (ev, status).
            # Right now we just support a single indication at a time.
            self._indicate_connection = None
            self._indicate_event = asyncio.ThreadSafeFlag()
            self._indicate_status = None

        self.uuid = uuid
        self.flags = flags
        self._value_handle = None
        self._initial = initial

    # Generate tuple for gatts_register_services.
    def _tuple(self):
        if self.descriptors:
            return (self.uuid, self.flags, tuple(d._tuple() for d in self.descriptors))
        else:
            # Workaround: v1.19 and below can't handle an empty descriptor tuple.
            return (self.uuid, self.flags)

    def notify(self, connection, data=None):
        if not (self.flags & _FLAG_NOTIFY):
            raise ValueError("Not supported")
        ble.gatts_notify(connection._conn_handle, self._value_handle, data)

    async def indicate(self, connection, data=None, timeout_ms=1000):
        if not (self.flags & _FLAG_INDICATE):
            raise ValueError("Not supported")
        if self._indicate_connection is not None:
            raise ValueError("In progress")
        if not connection.is_connected():
            raise ValueError("Not connected")

        self._indicate_connection = connection
        self._indicate_status = None

        try:
            with connection.timeout(timeout_ms):
                ble.gatts_indicate(connection._conn_handle, self._value_handle, data)
                await self._indicate_event.wait()
                if self._indicate_status != 0:
                    raise GattError(self._indicate_status)
        finally:
            self._indicate_connection = None

    def _indicate_done(conn_handle, value_handle, status):
        if characteristic := _registered_characteristics.get(value_handle, None):
            if connection := DeviceConnection._connected.get(conn_handle, None):
                if not characteristic._indicate_connection:
                    # Timeout.
                    return
                # See TODO in __init__ to support multiple concurrent indications.
                assert connection == characteristic._indicate_connection
                characteristic._indicate_status = status
                characteristic._indicate_event.set()


class BufferedCharacteristic(Characteristic):
    def __init__(self, *args, max_len=20, append=False, **kwargs):
        super().__init__(*args, **kwargs)
        self._max_len = max_len
        self._append = append

    def _register(self, value_handle):
        super()._register(value_handle)
        ble.gatts_set_buffer(value_handle, self._max_len, self._append)


class Descriptor(BaseCharacteristic):
    def __init__(self, characteristic, uuid, read=False, write=False, initial=None):
        characteristic.descriptors.append(self)

        flags = 0
        if read:
            flags |= _FLAG_READ
        if write:
            flags |= _FLAG_WRITE
            self._write_event = asyncio.ThreadSafeFlag()
            self._write_data = None

        self.uuid = uuid
        self.flags = flags
        self._value_handle = None
        self._initial = initial

    # Generate tuple for gatts_register_services.
    def _tuple(self):
        return (self.uuid, self.flags)


# Turn the Service/Characteristic/Descriptor classes into a registration tuple
# and then extract their value handles.
def register_services(*services):
    ensure_active()
    _registered_characteristics.clear()
    handles = ble.gatts_register_services(tuple(s._tuple() for s in services))
    for i in range(len(services)):
        service_handles = handles[i]
        service = services[i]
        n = 0
        for characteristic in service.characteristics:
            characteristic._register(service_handles[n])
            n += 1
            for descriptor in characteristic.descriptors:
                descriptor._register(service_handles[n])
                n += 1
