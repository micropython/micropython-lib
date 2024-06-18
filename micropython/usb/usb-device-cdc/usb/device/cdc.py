# MicroPython USB CDC module
# MIT license; Copyright (c) 2022 Martin Fischer, 2023-2024 Angus Gratton
import io
import time
import errno
import machine
import struct
from micropython import const

from .core import Interface, Buffer, split_bmRequestType

_EP_IN_FLAG = const(1 << 7)

# Control transfer stages
_STAGE_IDLE = const(0)
_STAGE_SETUP = const(1)
_STAGE_DATA = const(2)
_STAGE_ACK = const(3)

# Request types
_REQ_TYPE_STANDARD = const(0x0)
_REQ_TYPE_CLASS = const(0x1)
_REQ_TYPE_VENDOR = const(0x2)
_REQ_TYPE_RESERVED = const(0x3)

_DEV_CLASS_MISC = const(0xEF)
_CS_DESC_TYPE = const(0x24)  # CS Interface type communication descriptor

# CDC control interface definitions
_INTERFACE_CLASS_CDC = const(2)
_INTERFACE_SUBCLASS_CDC = const(2)  # Abstract Control Mode
_PROTOCOL_NONE = const(0)  # no protocol

# CDC descriptor subtype
# see also CDC120.pdf, table 13
_CDC_FUNC_DESC_HEADER = const(0)
_CDC_FUNC_DESC_CALL_MANAGEMENT = const(1)
_CDC_FUNC_DESC_ABSTRACT_CONTROL = const(2)
_CDC_FUNC_DESC_UNION = const(6)

# CDC class requests, table 13, PSTN subclass
_SET_LINE_CODING_REQ = const(0x20)
_GET_LINE_CODING_REQ = const(0x21)
_SET_CONTROL_LINE_STATE = const(0x22)
_SEND_BREAK_REQ = const(0x23)

_LINE_CODING_STOP_BIT_1 = const(0)
_LINE_CODING_STOP_BIT_1_5 = const(1)
_LINE_CODING_STOP_BIT_2 = const(2)

_LINE_CODING_PARITY_NONE = const(0)
_LINE_CODING_PARITY_ODD = const(1)
_LINE_CODING_PARITY_EVEN = const(2)
_LINE_CODING_PARITY_MARK = const(3)
_LINE_CODING_PARITY_SPACE = const(4)

_LINE_STATE_DTR = const(1)
_LINE_STATE_RTS = const(2)

_PARITY_BITS_REPR = "NOEMS"
_STOP_BITS_REPR = ("1", "1.5", "2")

# Other definitions
_CDC_VERSION = const(0x0120)  # release number in binary-coded decimal

# Number of endpoints in each interface
_CDC_CONTROL_EP_NUM = const(1)
_CDC_DATA_EP_NUM = const(2)

# CDC data interface definitions
_CDC_ITF_DATA_CLASS = const(0xA)
_CDC_ITF_DATA_SUBCLASS = const(0)
_CDC_ITF_DATA_PROT = const(0)  # no protocol

# Length of the bulk transfer endpoints. Maybe should be configurable?
_BULK_EP_LEN = const(64)

# MicroPython error constants (negated as IOBase.ioctl uses negative return values for error codes)
# these must match values in py/mperrno.h
_MP_EINVAL = const(-22)
_MP_ETIMEDOUT = const(-110)

# MicroPython stream ioctl requests, same as py/stream.h
_MP_STREAM_FLUSH = const(1)
_MP_STREAM_POLL = const(3)

# MicroPython ioctl poll values, same as py/stream.h
_MP_STREAM_POLL_WR = const(0x04)
_MP_STREAM_POLL_RD = const(0x01)
_MP_STREAM_POLL_HUP = const(0x10)


class CDCInterface(io.IOBase, Interface):
    # USB CDC serial device class, designed to resemble machine.UART
    # with some additional methods.
    #
    # Relies on multiple inheritance so it can be an io.IOBase for stream
    # functions and also a Interface (actually an Interface Association
    # Descriptor holding two interfaces.)
    def __init__(self, **kwargs):
        # io.IOBase has no __init__()
        Interface.__init__(self)

        # Callbacks for particular control changes initiated by the host
        self.break_cb = None  # Host sent a "break" condition
        self.line_state_cb = None
        self.line_coding_cb = None

        self._line_state = 0  # DTR & RTS
        # Set a default line coding of 115200/8N1
        self._line_coding = bytearray(b"\x00\xc2\x01\x00\x00\x00\x08")

        self._wb = ()  # Optional write Buffer (IN endpoint), set by CDC.init()
        self._rb = ()  # Optional read Buffer (OUT endpoint), set by CDC.init()
        self._timeout = 1000  # set from CDC.init() as well

        # one control interface endpoint, two data interface endpoints
        self.ep_c_in = self.ep_d_in = self.ep_d_out = None

        self._c_itf = None  # Number of control interface, data interface is one more

        self.init(**kwargs)

    def init(
        self, baudrate=9600, bits=8, parity="N", stop=1, timeout=None, txbuf=256, rxbuf=256, flow=0
    ):
        # Configure the CDC serial port. Note that many of these settings like
        # baudrate, bits, parity, stop don't change the USB-CDC device behavior
        # at all, only the "line coding" as communicated from/to the USB host.

        # Store initial line coding parameters in the USB CDC binary format
        # (there is nothing implemented to further change these from Python
        # code, the USB host sets them.)
        struct.pack_into(
            "<LBBB",
            self._line_coding,
            0,
            baudrate,
            _STOP_BITS_REPR.index(str(stop)),
            _PARITY_BITS_REPR.index(parity),
            bits,
        )

        if flow != 0:
            raise NotImplementedError  # UART flow control currently not supported

        if not (txbuf and rxbuf >= _BULK_EP_LEN):
            raise ValueError  # Buffer sizes are required, rxbuf must be at least one EP

        self._timeout = timeout
        self._wb = Buffer(txbuf)
        self._rb = Buffer(rxbuf)

    ###
    ### Line State & Line Coding State property getters
    ###

    @property
    def rts(self):
        return bool(self._line_state & _LINE_STATE_RTS)

    @property
    def dtr(self):
        return bool(self._line_state & _LINE_STATE_DTR)

    # Line Coding Representation
    # Byte 0-3   Byte 4      Byte 5       Byte 6
    # dwDTERate  bCharFormat bParityType  bDataBits

    @property
    def baudrate(self):
        return struct.unpack("<LBBB", self._line_coding)[0]

    @property
    def stop_bits(self):
        return _STOP_BITS_REPR[self._line_coding[4]]

    @property
    def parity(self):
        return _PARITY_BITS_REPR[self._line_coding[5]]

    @property
    def data_bits(self):
        return self._line_coding[6]

    def __repr__(self):
        return f"{self.baudrate}/{self.data_bits}{self.parity}{self.stop_bits} rts={self.rts} dtr={self.dtr}"

    ###
    ### Set callbacks for operations initiated by the host
    ###

    def set_break_cb(self, cb):
        self.break_cb = cb

    def set_line_state_cb(self, cb):
        self.line_state_cb = cb

    def set_line_coding_cb(self, cb):
        self.line_coding_cb = cb

    ###
    ### USB Interface Implementation
    ###

    def desc_cfg(self, desc, itf_num, ep_num, strs):
        # CDC needs a Interface Association Descriptor (IAD) wrapping two interfaces: Control & Data interfaces
        desc.interface_assoc(itf_num, 2, _INTERFACE_CLASS_CDC, _INTERFACE_SUBCLASS_CDC)

        # Now add the Control interface descriptor
        self._c_itf = itf_num
        desc.interface(itf_num, _CDC_CONTROL_EP_NUM, _INTERFACE_CLASS_CDC, _INTERFACE_SUBCLASS_CDC)

        # Append the CDC class-specific interface descriptor
        # see CDC120-track, p20
        desc.pack(
            "<BBBH",
            5,  # bFunctionLength
            _CS_DESC_TYPE,  # bDescriptorType
            _CDC_FUNC_DESC_HEADER,  # bDescriptorSubtype
            _CDC_VERSION,  # cdc version
        )

        # CDC-PSTN table3 "Call Management"
        # set to No
        desc.pack(
            "<BBBBB",
            5,  # bFunctionLength
            _CS_DESC_TYPE,  # bDescriptorType
            _CDC_FUNC_DESC_CALL_MANAGEMENT,  # bDescriptorSubtype
            0,  # bmCapabilities - XXX no call managment so far
            itf_num + 1,  # bDataInterface - interface 1
        )

        # CDC-PSTN table4 "Abstract Control"
        # set to support line_coding and send_break
        desc.pack(
            "<BBBB",
            4,  # bFunctionLength
            _CS_DESC_TYPE,  # bDescriptorType
            _CDC_FUNC_DESC_ABSTRACT_CONTROL,  # bDescriptorSubtype
            0x6,  # bmCapabilities D1, D2
        )

        # CDC-PSTN "Union"
        # set control interface / data interface number
        desc.pack(
            "<BBBBB",
            5,  # bFunctionLength
            _CS_DESC_TYPE,  # bDescriptorType
            _CDC_FUNC_DESC_UNION,  # bDescriptorSubtype
            itf_num,  # bControlInterface
            itf_num + 1,  # bSubordinateInterface0 (data class itf number)
        )

        # Single control IN endpoint (currently unused in this implementation)
        self.ep_c_in = ep_num | _EP_IN_FLAG
        desc.endpoint(self.ep_c_in, "interrupt", 8, 16)

        # Now add the data interface
        desc.interface(
            itf_num + 1,
            _CDC_DATA_EP_NUM,
            _CDC_ITF_DATA_CLASS,
            _CDC_ITF_DATA_SUBCLASS,
            _CDC_ITF_DATA_PROT,
        )

        # Two data endpoints, bulk OUT and IN
        self.ep_d_out = ep_num + 1
        self.ep_d_in = (ep_num + 1) | _EP_IN_FLAG
        desc.endpoint(self.ep_d_out, "bulk", _BULK_EP_LEN, 0)
        desc.endpoint(self.ep_d_in, "bulk", _BULK_EP_LEN, 0)

    def num_itfs(self):
        return 2

    def num_eps(self):
        return 2  # total after masking out _EP_IN_FLAG

    def on_open(self):
        super().on_open()
        # kick off any transfers that may have queued while the device was not open
        self._rd_xfer()
        self._wr_xfer()

    def on_interface_control_xfer(self, stage, request):
        # Handle class-specific interface control transfers
        bmRequestType, bRequest, wValue, wIndex, wLength = struct.unpack("BBHHH", request)
        recipient, req_type, req_dir = split_bmRequestType(bmRequestType)

        if wIndex != self._c_itf:
            return False  # Only for the control interface (may be redundant check?)

        if req_type != _REQ_TYPE_CLASS:
            return False  # Unsupported request type

        if stage == _STAGE_SETUP:
            if bRequest in (_SET_LINE_CODING_REQ, _GET_LINE_CODING_REQ):
                return self._line_coding  # Buffer to read or write

            # Continue on other supported requests, stall otherwise
            return bRequest in (_SET_CONTROL_LINE_STATE, _SEND_BREAK_REQ)

        if stage == _STAGE_ACK:
            if bRequest == _SET_LINE_CODING_REQ:
                if self.line_coding_cb:
                    self.line_coding_cb(self._line_coding)
            elif bRequest == _SET_CONTROL_LINE_STATE:
                self._line_state = wValue
                if self.line_state_cb:
                    self.line_state_cb(wValue)
            elif bRequest == _SEND_BREAK_REQ:
                if self.break_cb:
                    self.break_cb(wValue)

        return True  # allow DATA/ACK stages to complete normally

    def _wr_xfer(self):
        # Submit a new data IN transfer from the _wb buffer, if needed
        if self.is_open() and not self.xfer_pending(self.ep_d_in) and self._wb.readable():
            self.submit_xfer(self.ep_d_in, self._wb.pend_read(), self._wr_cb)

    def _wr_cb(self, ep, res, num_bytes):
        # Whenever a data IN transfer ends
        if res == 0:
            self._wb.finish_read(num_bytes)
        self._wr_xfer()

    def _rd_xfer(self):
        # Keep an active data OUT transfer to read data from the host,
        # whenever the receive buffer has room for new data
        if (
            self.is_open()
            and not self.xfer_pending(self.ep_d_out)
            and self._rb.writable() >= _BULK_EP_LEN
        ):
            # Can only submit up to the endpoint length per transaction, otherwise we won't
            # get any transfer callback until the full transaction completes.
            self.submit_xfer(self.ep_d_out, self._rb.pend_write(_BULK_EP_LEN), self._rd_cb)

    def _rd_cb(self, ep, res, num_bytes):
        # Whenever a data OUT transfer ends
        if res == 0:
            self._rb.finish_write(num_bytes)
        self._rd_xfer()

    ###
    ### io.IOBase stream implementation
    ###

    def write(self, buf):
        # use a memoryview to track how much of 'buf' we've written so far
        # (unfortunately, this means a 1 block allocation for each write, but it's otherwise allocation free.)
        start = time.ticks_ms()
        mv = memoryview(buf)
        while True:
            # Keep pushing buf into _wb into it's all gone
            nbytes = self._wb.write(mv)
            self._wr_xfer()  # make sure a transfer is running from _wb

            if nbytes == len(mv):
                return len(buf)  # Success

            mv = mv[nbytes:]

            # check for timeout
            if time.ticks_diff(time.ticks_ms(), start) >= self._timeout:
                return len(buf) - len(mv)

            machine.idle()

    def read(self, size):
        start = time.ticks_ms()

        # Allocate a suitable buffer to read into
        if size >= 0:
            b = bytearray(size)
        else:
            # for size == -1, return however many bytes are ready
            b = bytearray(self._rb.readable())

        n = self._readinto(b, start)
        if not n:
            return None
        if n < len(b):
            return b[:n]
        return b

    def readinto(self, b):
        return self._readinto(b, time.ticks_ms())

    def _readinto(self, b, start):
        if len(b) == 0:
            return 0

        n = 0
        m = memoryview(b)
        while n < len(b):
            # copy out of the read buffer if there is anything available
            if self._rb.readable():
                n += self._rb.readinto(m if n == 0 else m[n:])
                self._rd_xfer()  # if _rd was previously full, no transfer will be running
                if n == len(b):
                    break  # Done, exit before we call machine.idle()

            if time.ticks_diff(time.ticks_ms(), start) >= self._timeout:
                break  # Timed out

            machine.idle()

        return n or None

    def ioctl(self, req, arg):
        if req == _MP_STREAM_POLL:
            return (
                (_MP_STREAM_POLL_WR if (arg & _MP_STREAM_POLL_WR) and self._wb.writable() else 0)
                | (_MP_STREAM_POLL_RD if (arg & _MP_STREAM_POLL_RD) and self._rb.readable() else 0)
                |
                # using the USB level "open" (i.e. connected to host) for !HUP, not !DTR (port is open)
                (_MP_STREAM_POLL_HUP if (arg & _MP_STREAM_POLL_HUP) and not self.is_open() else 0)
            )
        elif req == _MP_STREAM_FLUSH:
            start = time.ticks_ms()
            # Wait until write buffer contains no bytes for the lower TinyUSB layer to "read"
            while self._wb.readable():
                if not self.is_open():
                    return _MP_EINVAL
                if time.ticks_diff(time.ticks_ms(), start) > self._timeout:
                    return _MP_ETIMEDOUT
                machine.idle()
            return 0

        return _MP_EINVAL

    def flush(self):
        # a C implementation of this exists in stream.c, but it's not in io.IOBase
        # and can't immediately be called from here (AFAIK)
        r = self.ioctl(_MP_STREAM_FLUSH, 0)
        if r:
            raise OSError(r)
