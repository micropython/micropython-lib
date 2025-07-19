# MicroPython Library runtime USB device implementation
#
# These contain the classes and utilities that are needed to
# implement a USB device, not any complete USB drivers.
#
# MIT license; Copyright (c) 2022-2024 Angus Gratton
from micropython import const
import machine
import struct

try:
    from _thread import get_ident
except ImportError:

    def get_ident():
        return 0  # Placeholder, for no threading support


_EP_IN_FLAG = const(1 << 7)

# USB descriptor types
_STD_DESC_DEV_TYPE = const(0x1)
_STD_DESC_CONFIG_TYPE = const(0x2)
_STD_DESC_STRING_TYPE = const(0x3)
_STD_DESC_INTERFACE_TYPE = const(0x4)
_STD_DESC_ENDPOINT_TYPE = const(0x5)
_STD_DESC_INTERFACE_ASSOC = const(0xB)

_ITF_ASSOCIATION_DESC_TYPE = const(0xB)  # Interface Association descriptor

# Standard USB descriptor lengths
_STD_DESC_CONFIG_LEN = const(9)
_STD_DESC_ENDPOINT_LEN = const(7)
_STD_DESC_INTERFACE_LEN = const(9)

_DESC_OFFSET_LEN = const(0)
_DESC_OFFSET_TYPE = const(1)

_DESC_OFFSET_INTERFACE_NUM = const(2)  # for _STD_DESC_INTERFACE_TYPE
_DESC_OFFSET_ENDPOINT_NUM = const(2)  # for _STD_DESC_ENDPOINT_TYPE

# Standard control request bmRequest fields, can extract by calling split_bmRequestType()
_REQ_RECIPIENT_DEVICE = const(0x0)
_REQ_RECIPIENT_INTERFACE = const(0x1)
_REQ_RECIPIENT_ENDPOINT = const(0x2)
_REQ_RECIPIENT_OTHER = const(0x3)

# Offsets into the standard configuration descriptor, to fixup
_OFFS_CONFIG_iConfiguration = const(6)

_INTERFACE_CLASS_VENDOR = const(0xFF)
_INTERFACE_SUBCLASS_NONE = const(0x00)
_PROTOCOL_NONE = const(0x00)

# These need to match the constants in tusb_config.h
_USB_STR_MANUF = const(0x01)
_USB_STR_PRODUCT = const(0x02)
_USB_STR_SERIAL = const(0x03)

# Error constant to match mperrno.h
_MP_EINVAL = const(22)

_dev = None  # Singleton _Device instance


def get():
    # Getter to access the singleton instance of the
    # MicroPython _Device object
    #
    # (note this isn't the low-level machine.USBDevice object, the low-level object is
    # get()._usbd.)
    global _dev
    if not _dev:
        _dev = _Device()
    return _dev


class _Device:
    # Class that implements the Python parts of the MicroPython USBDevice.
    #
    # This class should only be instantiated by the singleton getter
    # function usb.device.get(), never directly.
    def __init__(self):
        self._itfs = {}  # Mapping from interface number to interface object, set by init()
        self._eps = {}  # Mapping from endpoint address to interface object, set by _open_cb()
        self._ep_cbs = {}  # Mapping from endpoint address to Optional[xfer callback]
        self._cb_thread = None  # Thread currently running endpoint callback
        self._cb_ep = None  # Endpoint number currently running callback
        self._usbd = machine.USBDevice()  # low-level API

    def init(self, *itfs, **kwargs):
        # Helper function to configure the USB device and activate it in a single call
        self.active(False)
        self.config(*itfs, **kwargs)
        self.active(True)

    def config(  # noqa: PLR0913
        self,
        *itfs,
        builtin_driver=False,
        manufacturer_str=None,
        product_str=None,
        serial_str=None,
        configuration_str=None,
        id_vendor=None,
        id_product=None,
        bcd_device=None,
        device_class=0,
        device_subclass=0,
        device_protocol=0,
        config_str=None,
        max_power_ma=None,
        remote_wakeup=False,
    ):
        # Configure the USB device with a set of interfaces, and optionally reconfiguring the
        # device and configuration descriptor fields

        _usbd = self._usbd

        if self.active():
            raise OSError(_MP_EINVAL)  # Must set active(False) first

        # Convenience: Allow builtin_driver to be True, False or one of
        # the machine.USBDevice.BUILTIN_ constants
        if isinstance(builtin_driver, bool):
            builtin_driver = _usbd.BUILTIN_DEFAULT if builtin_driver else _usbd.BUILTIN_NONE
        _usbd.builtin_driver = builtin_driver

        # Putting None for any strings that should fall back to the "built-in" value
        # Indexes in this list depends on _USB_STR_MANUF, _USB_STR_PRODUCT, _USB_STR_SERIAL
        strs = [None, manufacturer_str, product_str, serial_str]

        # Build the device descriptor
        FMT = "<BBHBBBBHHHBBBB"
        # read the static descriptor fields
        f = struct.unpack(FMT, builtin_driver.desc_dev)

        def maybe_set(value, idx):
            # Override a numeric descriptor value or keep builtin value f[idx] if 'value' is None
            if value is not None:
                return value
            return f[idx]

        # Either copy each descriptor field directly from the builtin device descriptor, or 'maybe'
        # set it to the custom value from the object
        desc_dev = struct.pack(
            FMT,
            f[0],  # bLength
            f[1],  # bDescriptorType
            f[2],  # bcdUSB
            device_class,  # bDeviceClass
            device_subclass,  # bDeviceSubClass
            device_protocol,  # bDeviceProtocol
            f[6],  # bMaxPacketSize0, TODO: allow overriding this value?
            maybe_set(id_vendor, 7),  # idVendor
            maybe_set(id_product, 8),  # idProduct
            maybe_set(bcd_device, 9),  # bcdDevice
            _USB_STR_MANUF,  # iManufacturer
            _USB_STR_PRODUCT,  # iProduct
            _USB_STR_SERIAL,  # iSerialNumber
            1,
        )  # bNumConfigurations

        # Iterate interfaces to build the configuration descriptor

        # Keep track of the interface and endpoint indexes
        itf_num = builtin_driver.itf_max
        ep_num = max(builtin_driver.ep_max, 1)  # Endpoint 0 always reserved for control
        while len(strs) < builtin_driver.str_max:
            strs.append(None)  # Reserve other string indexes used by builtin drivers
        initial_cfg = builtin_driver.desc_cfg or (b"\x00" * _STD_DESC_CONFIG_LEN)

        self._itfs = {}

        # Determine the total length of the configuration descriptor, by making dummy
        # calls to build the config descriptor
        desc = Descriptor(None)
        desc.extend(initial_cfg)
        for itf in itfs:
            itf.desc_cfg(desc, 0, 0, [])

        # Allocate the real Descriptor helper to write into it, starting
        # after the standard configuration descriptor
        desc = Descriptor(bytearray(desc.o))
        desc.extend(initial_cfg)
        for itf in itfs:
            itf.desc_cfg(desc, itf_num, ep_num, strs)

            for _ in range(itf.num_itfs()):
                self._itfs[itf_num] = itf  # Mapping from interface numbers to interfaces
                itf_num += 1

            ep_num += itf.num_eps()

        # Go back and update the Standard Configuration Descriptor
        # header at the start with values based on the complete
        # descriptor.
        #
        # See USB 2.0 specification section 9.6.3 p264 for details.
        bmAttributes = (
            (1 << 7)  # Reserved
            | (0 if max_power_ma else (1 << 6))  # Self-Powered
            | ((1 << 5) if remote_wakeup else 0)
        )

        # Configuration string is optional but supported
        iConfiguration = 0
        if configuration_str:
            iConfiguration = len(strs)
            strs.append(configuration_str)

        if max_power_ma is not None:
            # Convert from mA to the units used in the descriptor
            max_power_ma //= 2
        else:
            try:
                # Default to whatever value the builtin driver reports
                max_power_ma = _usbd.BUILTIN_DEFAULT.desc_cfg[8]
            except IndexError:
                # If no built-in driver, default to 250mA
                max_power_ma = 125

        desc.pack_into(
            "<BBHBBBBB",
            0,
            _STD_DESC_CONFIG_LEN,  # bLength
            _STD_DESC_CONFIG_TYPE,  # bDescriptorType
            len(desc.b),  # wTotalLength
            itf_num,
            1,  # bConfigurationValue
            iConfiguration,
            bmAttributes,
            max_power_ma,
        )

        _usbd.config(
            desc_dev,
            desc.b,
            strs,
            self._open_itf_cb,
            self._reset_cb,
            self._control_xfer_cb,
            self._xfer_cb,
        )

    def active(self, *optional_value):
        # Thin wrapper around the USBDevice active() function.
        #
        # Note: active only means the USB device is available, not that it has
        # actually been connected to and configured by a USB host. Use the
        # Interface.is_open() function to check if the host has configured an
        # interface of the device.
        return self._usbd.active(*optional_value)

    def _open_itf_cb(self, desc):
        # Callback from TinyUSB lower layer, when USB host does Set
        # Configuration. Called once per interface or IAD.

        # Note that even if the configuration descriptor contains an IAD, 'desc'
        # starts from the first interface descriptor in the IAD and not the IAD
        # descriptor.

        itf_num = desc[_DESC_OFFSET_INTERFACE_NUM]
        itf = self._itfs[itf_num]

        # Scan the full descriptor:
        # - Build _eps and _ep_addr from the endpoint descriptors
        # - Find the highest numbered interface provided to the callback
        #   (which will be the first interface, unless we're scanning
        #   multiple interfaces inside an IAD.)
        offs = 0
        max_itf = itf_num
        while offs < len(desc):
            dl = desc[offs + _DESC_OFFSET_LEN]
            dt = desc[offs + _DESC_OFFSET_TYPE]
            if dt == _STD_DESC_ENDPOINT_TYPE:
                ep_addr = desc[offs + _DESC_OFFSET_ENDPOINT_NUM]
                self._eps[ep_addr] = itf
                self._ep_cbs[ep_addr] = None
            elif dt == _STD_DESC_INTERFACE_TYPE:
                max_itf = max(max_itf, desc[offs + _DESC_OFFSET_INTERFACE_NUM])
            offs += dl

        # If 'desc' is not the inside of an Interface Association Descriptor but
        # 'itf' object still represents multiple USB interfaces (i.e. MIDI),
        # defer calling 'itf.on_open()' until this callback fires for the
        # highest numbered USB interface.
        #
        # This means on_open() is only called once, and that it can
        # safely submit transfers on any of the USB interfaces' endpoints.
        if self._itfs.get(max_itf + 1, None) != itf:
            itf.on_open()

    def _reset_cb(self):
        # TinyUSB lower layer callback when the USB device is reset by the host

        # Allow interfaces to respond to the reset
        for itf in self._itfs.values():
            itf.on_reset()

        # Rebuilt when host re-enumerates
        self._eps = {}
        self._ep_cbs = {}

    def _submit_xfer(self, ep_addr, data, done_cb=None):
        # Submit a USB transfer (of any type except control) to TinyUSB lower layer.
        #
        # Generally, drivers should call Interface.submit_xfer() instead. See
        # that function for documentation about the possible parameter values.
        if ep_addr not in self._eps:
            raise ValueError("ep_addr")
        if self._xfer_pending(ep_addr):
            raise RuntimeError("xfer_pending")

        # USBDevice callback may be called immediately, before Python execution
        # continues, so set it first.
        #
        # To allow xfer_pending checks to work, store True instead of None.
        self._ep_cbs[ep_addr] = done_cb or True
        return self._usbd.submit_xfer(ep_addr, data)

    def _xfer_pending(self, ep_addr):
        # Returns True if a transfer is pending on this endpoint.
        #
        # Generally, drivers should call Interface.xfer_pending() instead. See that
        # function for more documentation.
        return self._ep_cbs[ep_addr] or (self._cb_ep == ep_addr and self._cb_thread != get_ident())

    def _xfer_cb(self, ep_addr, result, xferred_bytes):
        # Callback from TinyUSB lower layer when a transfer completes.
        cb = self._ep_cbs.get(ep_addr, None)
        self._cb_thread = get_ident()
        self._cb_ep = ep_addr  # Track while callback is running
        self._ep_cbs[ep_addr] = None

        # In most cases, 'cb' is a callback function for the transfer. Can also be:
        # - True (for a transfer with no callback)
        # - None (TinyUSB callback arrived for invalid endpoint, or no transfer.
        #   Generally unlikely, but may happen in transient states.)
        try:
            if callable(cb):
                cb(ep_addr, result, xferred_bytes)
        finally:
            self._cb_ep = None

    def _control_xfer_cb(self, stage, request):
        # Callback from TinyUSB lower layer when a control
        # transfer is in progress.
        #
        # stage determines appropriate responses (possible values
        # utils.STAGE_SETUP, utils.STAGE_DATA, utils.STAGE_ACK).
        #
        # The TinyUSB class driver framework only calls this function for
        # particular types of control transfer, other standard control transfers
        # are handled by TinyUSB itself.
        wIndex = request[4] + (request[5] << 8)
        recipient, _, _ = split_bmRequestType(request[0])

        itf = None
        result = None

        if recipient == _REQ_RECIPIENT_DEVICE:
            itf = self._itfs.get(wIndex & 0xFFFF, None)
            if itf:
                result = itf.on_device_control_xfer(stage, request)
        elif recipient == _REQ_RECIPIENT_INTERFACE:
            itf = self._itfs.get(wIndex & 0xFFFF, None)
            if itf:
                result = itf.on_interface_control_xfer(stage, request)
        elif recipient == _REQ_RECIPIENT_ENDPOINT:
            ep_num = wIndex & 0xFFFF
            itf = self._eps.get(ep_num, None)
            if itf:
                result = itf.on_endpoint_control_xfer(stage, request)

        if not itf:
            # At time this code was written, only the control transfers shown
            # above are passed to the class driver callback. See
            # invoke_class_control() in tinyusb usbd.c
            raise RuntimeError(f"Unexpected control request type {request[0]:#x}")

        # Expecting any of the following possible replies from
        # on_NNN_control_xfer():
        #
        # True - Continue transfer, no data
        # False - STALL transfer
        # Object with buffer interface - submit this data for the control transfer
        return result


class Interface:
    # Abstract base class to implement USB Interface (and associated endpoints),
    # or a collection of USB Interfaces, in Python
    #
    # (Despite the name an object of type Interface can represent multiple
    # associated interfaces, with or without an Interface Association Descriptor
    # prepended to them. Override num_itfs() if assigning >1 USB interface.)

    def __init__(self):
        self._open = False

    def desc_cfg(self, desc, itf_num, ep_num, strs):
        # Function to build configuration descriptor contents for this interface
        # or group of interfaces. This is called on each interface from
        # USBDevice.init().
        #
        # This function should insert:
        #
        # - At least one standard Interface descriptor (can call
        # - desc.interface()).
        #
        # Plus, optionally:
        #
        # - One or more endpoint descriptors (can call desc.endpoint()).
        # - An Interface Association Descriptor, prepended before.
        # - Other class-specific configuration descriptor data.
        #
        # This function is called twice per call to USBDevice.init(). The first
        # time the values of all arguments are dummies that are used only to
        # calculate the total length of the descriptor. Therefore, anything this
        # function does should be idempotent and it should add the same
        # descriptors each time. If saving interface numbers or endpoint numbers
        # for later
        #
        # Parameters:
        #
        # - desc - Descriptor helper to write the configuration descriptor bytes into.
        #   The first time this function is called 'desc' is a dummy object
        #   with no backing buffer (exists to count the number of bytes needed).
        #
        # - itf_num - First bNumInterfaces value to assign. The descriptor
        #   should contain the same number of interfaces returned by num_itfs(),
        #   starting from this value.
        #
        # - ep_num - Address of the first available endpoint number to use for
        #   endpoint descriptor addresses. Subclasses should save the
        #   endpoint addresses selected, to look up later (although note the first
        #   time this function is called, the values will be dummies.)
        #
        # - strs - list of string descriptors for this USB device. This function
        #   can append to this list, and then insert the index of the new string
        #   in the list into the configuration descriptor.
        raise NotImplementedError

    def num_itfs(self):
        # Return the number of actual USB Interfaces represented by this object
        # (as set in desc_cfg().)
        #
        # Only needs to be overriden if implementing a Interface class that
        # represents more than one USB Interface descriptor (i.e. MIDI), or an
        # Interface Association Descriptor (i.e. USB-CDC).
        return 1

    def num_eps(self):
        # Return the number of USB Endpoint numbers represented by this object
        # (as set in desc_cfg().)
        #
        # Note for each count returned by this function, the interface may
        # choose to have both an IN and OUT endpoint (i.e. IN flag is not
        # considered a value here.)
        #
        # This value can be zero, if the USB Host only communicates with this
        # interface using control transfers.
        return 0

    def on_open(self):
        # Callback called when the USB host accepts the device configuration.
        #
        # Override this function to initiate any operations that the USB interface
        # should do when the USB device is configured to the host.
        self._open = True

    def on_reset(self):
        # Callback called on every registered interface when the USB device is
        # reset by the host. This can happen when the USB device is unplugged,
        # or if the host triggers a reset for some other reason.
        #
        # Override this function to cancel any pending operations specific to
        # the interface (outstanding USB transfers are already cancelled).
        #
        # At this point, no USB functionality is available - on_open() will
        # be called later if/when the USB host re-enumerates and configures the
        # interface.
        self._open = False

    def is_open(self):
        # Returns True if the interface has been configured by the host and is in
        # active use.
        return self._open

    def on_device_control_xfer(self, stage, request):
        # Control transfer callback. Override to handle a non-standard device
        # control transfer where bmRequestType Recipient is Device, Type is
        # utils.REQ_TYPE_CLASS, and the lower byte of wIndex indicates this interface.
        #
        # (See USB 2.0 specification 9.4 Standard Device Requests, p250).
        #
        # This particular request type seems pretty uncommon for a device class
        # driver to need to handle, most hosts will not send this so most
        # implementations won't need to override it.
        #
        # Parameters:
        #
        # - stage is one of utils.STAGE_SETUP, utils.STAGE_DATA, utils.STAGE_ACK.
        #
        # - request is a memoryview into a USB request packet, as per USB 2.0
        #   specification 9.3 USB Device Requests, p250.  the memoryview is only
        #   valid while the callback is running.
        #
        # The function can call split_bmRequestType(request[0]) to split
        # bmRequestType into (Recipient, Type, Direction).
        #
        # Result, any of:
        #
        # - True to continue the request, False to STALL the endpoint.
        # - Buffer interface object to provide a buffer to the host as part of the
        #   transfer, if applicable.
        return False

    def on_interface_control_xfer(self, stage, request):
        # Control transfer callback. Override to handle a device control
        # transfer where bmRequestType Recipient is Interface, and the lower byte
        # of wIndex indicates this interface.
        #
        # (See USB 2.0 specification 9.4 Standard Device Requests, p250).
        #
        # bmRequestType Type field may have different values. It's not necessary
        # to handle the mandatory Standard requests (bmRequestType Type ==
        # utils.REQ_TYPE_STANDARD), if the driver returns False in these cases then
        # TinyUSB will provide the necessary responses.
        #
        # See on_device_control_xfer() for a description of the arguments and
        # possible return values.
        return False

    def on_endpoint_control_xfer(self, stage, request):
        # Control transfer callback. Override to handle a device
        # control transfer where bmRequestType Recipient is Endpoint and
        # the lower byte of wIndex indicates an endpoint address associated
        # with this interface.
        #
        # bmRequestType Type will generally have any value except
        # utils.REQ_TYPE_STANDARD, as Standard endpoint requests are handled by
        # TinyUSB. The exception is the the Standard "Set Feature" request. This
        # is handled by Tiny USB but also passed through to the driver in case it
        # needs to change any internal state, but most drivers can ignore and
        # return False in this case.
        #
        # (See USB 2.0 specification 9.4 Standard Device Requests, p250).
        #
        # See on_device_control_xfer() for a description of the parameters and
        # possible return values.
        return False

    def xfer_pending(self, ep_addr):
        # Return True if a transfer is already pending on ep_addr.
        #
        # Only one transfer can be submitted at a time.
        #
        # The transfer is marked pending while a completion callback is running
        # for that endpoint, unless this function is called from the callback
        # itself. This makes it simple to submit a new transfer from the
        # completion callback.
        return _dev and _dev._xfer_pending(ep_addr)

    def submit_xfer(self, ep_addr, data, done_cb=None):
        # Submit a USB transfer (of any type except control)
        #
        # Parameters:
        #
        # - ep_addr. Address of the endpoint to submit the transfer on. Caller is
        #   responsible for ensuring that ep_addr is correct and belongs to this
        #   interface. Only one transfer can be active at a time on each endpoint.
        #
        # - data. Buffer containing data to send, or for data to be read into
        #   (depending on endpoint direction).
        #
        # - done_cb. Optional callback function for when the transfer
        # completes. The callback is called with arguments (ep_addr, result,
        # xferred_bytes) where result is one of xfer_result_t enum (see top of
        # this file), and xferred_bytes is an integer.
        #
        # If the function returns, the transfer is queued.
        #
        # The function will raise RuntimeError under the following conditions:
        #
        # - The interface is not "open" (i.e. has not been enumerated and configured
        #   by the host yet.)
        #
        # - A transfer is already pending on this endpoint (use xfer_pending() to check
        #   before sending if needed.)
        #
        # - A DCD error occurred when queueing the transfer on the hardware.
        #
        #
        # Will raise TypeError if 'data' isn't he correct type of buffer for the
        # endpoint transfer direction.
        #
        # Note that done_cb may be called immediately, possibly before this
        # function has returned to the caller.
        if not self._open:
            raise RuntimeError("Not open")
        _dev._submit_xfer(ep_addr, data, done_cb)

    def stall(self, ep_addr, *args):
        # Set or get the endpoint STALL state.
        #
        # To get endpoint stall stage, call with a single argument.
        # To set endpoint stall state, call with an additional boolean
        # argument to set or clear.
        #
        # Generally endpoint STALL is handled automatically, but there are some
        # device classes that need to explicitly stall or unstall an endpoint
        # under certain conditions.
        if not self._open or ep_addr not in self._eps:
            raise RuntimeError
        _dev._usbd.stall(ep_addr, *args)


class Descriptor:
    # Wrapper class for writing a descriptor in-place into a provided buffer
    #
    # Doesn't resize the buffer.
    #
    # Can be initialised with b=None to perform a dummy pass that calculates the
    # length needed for the buffer.
    def __init__(self, b):
        self.b = b
        self.o = 0  # offset of data written to the buffer

    def pack(self, fmt, *args):
        # Utility function to pack new data into the descriptor
        # buffer, starting at the current offset.
        #
        # Arguments are the same as struct.pack(), but it fills the
        # pre-allocated descriptor buffer (growing if needed), instead of
        # returning anything.
        self.pack_into(fmt, self.o, *args)

    def pack_into(self, fmt, offs, *args):
        # Utility function to pack new data into the descriptor at offset 'offs'.
        #
        # If the data written is before 'offs' then self.o isn't incremented,
        # otherwise it's incremented to point at the end of the written data.
        end = offs + struct.calcsize(fmt)
        if self.b:
            struct.pack_into(fmt, self.b, offs, *args)
        self.o = max(self.o, end)

    def extend(self, a):
        # Extend the descriptor with some bytes-like data
        if self.b:
            self.b[self.o : self.o + len(a)] = a
        self.o += len(a)

    # TODO: At the moment many of these arguments are named the same as the relevant field
    # in the spec, as this is easier to understand. Can save some code size by collapsing them
    # down.

    def interface(
        self,
        bInterfaceNumber,
        bNumEndpoints,
        bInterfaceClass=_INTERFACE_CLASS_VENDOR,
        bInterfaceSubClass=_INTERFACE_SUBCLASS_NONE,
        bInterfaceProtocol=_PROTOCOL_NONE,
        iInterface=0,
    ):
        # Utility function to append a standard Interface descriptor, with
        # the properties specified in the parameter list.
        #
        # Defaults for bInterfaceClass, SubClass and Protocol are a "vendor"
        # device.
        #
        # Note that iInterface is a string index number. If set, it should be set
        # by the caller Interface to the result of self._get_str_index(s),
        # where 's' is a string found in self.strs.
        self.pack(
            "BBBBBBBBB",
            _STD_DESC_INTERFACE_LEN,  # bLength
            _STD_DESC_INTERFACE_TYPE,  # bDescriptorType
            bInterfaceNumber,
            0,  # bAlternateSetting, not currently supported
            bNumEndpoints,
            bInterfaceClass,
            bInterfaceSubClass,
            bInterfaceProtocol,
            iInterface,
        )

    def endpoint(self, bEndpointAddress, bmAttributes, wMaxPacketSize, bInterval=1):
        # Utility function to append a standard Endpoint descriptor, with
        # the properties specified in the parameter list.
        #
        # See USB 2.0 specification section 9.6.6 Endpoint p269
        #
        # As well as a numeric value, bmAttributes can be a string value to represent
        # common endpoint types: "control", "bulk", "interrupt".
        if bmAttributes == "control":
            bmAttributes = 0
        elif bmAttributes == "bulk":
            bmAttributes = 2
        elif bmAttributes == "interrupt":
            bmAttributes = 3

        self.pack(
            "<BBBBHB",
            _STD_DESC_ENDPOINT_LEN,
            _STD_DESC_ENDPOINT_TYPE,
            bEndpointAddress,
            bmAttributes,
            wMaxPacketSize,
            bInterval,
        )

    def interface_assoc(
        self,
        bFirstInterface,
        bInterfaceCount,
        bFunctionClass,
        bFunctionSubClass,
        bFunctionProtocol=_PROTOCOL_NONE,
        iFunction=0,
    ):
        # Utility function to append an Interface Association descriptor,
        # with the properties specified in the parameter list.
        #
        # See USB ECN: Interface Association Descriptor.
        self.pack(
            "<BBBBBBBB",
            8,
            _ITF_ASSOCIATION_DESC_TYPE,
            bFirstInterface,
            bInterfaceCount,
            bFunctionClass,
            bFunctionSubClass,
            bFunctionProtocol,
            iFunction,
        )


def split_bmRequestType(bmRequestType):
    # Utility function to split control transfer field bmRequestType into a tuple of 3 fields:
    #
    # Recipient
    # Type
    # Data transfer direction
    #
    # See USB 2.0 specification section 9.3 USB Device Requests and 9.3.1 bmRequestType, p248.
    return (
        bmRequestType & 0x1F,
        (bmRequestType >> 5) & 0x03,
        (bmRequestType >> 7) & 0x01,
    )


class Buffer:
    # An interrupt-safe producer/consumer buffer that wraps a bytearray object.
    #
    # Kind of like a ring buffer, but supports the idea of returning a
    # memoryview for either read or write of multiple bytes (suitable for
    # passing to a buffer function without needing to allocate another buffer to
    # read into.)
    #
    # Consumer can call pend_read() to get a memoryview to read from, and then
    # finish_read(n) when done to indicate it read 'n' bytes from the
    # memoryview. There is also a readinto() convenience function.
    #
    # Producer must call pend_write() to get a memorybuffer to write into, and
    # then finish_write(n) when done to indicate it wrote 'n' bytes into the
    # memoryview. There is also a normal write() convenience function.
    #
    # - Only one producer and one consumer is supported.
    #
    # - Calling pend_read() and pend_write() is effectively idempotent, they can be
    #   called more than once without a corresponding finish_x() call if necessary
    #   (provided only one thread does this, as per the previous point.)
    #
    # - Calling finish_write() and finish_read() is hard interrupt safe (does
    #   not allocate). pend_read() and pend_write() each allocate 1 block for
    #   the memoryview that is returned.
    #
    # The buffer contents are always laid out as:
    #
    # - Slice [:_n] = bytes of valid data waiting to read
    # - Slice [_n:_w] = unused space
    # - Slice [_w:] = bytes of pending write buffer waiting to be written
    #
    # This buffer should be fast when most reads and writes are balanced and use
    # the whole buffer. When this doesn't happen, performance degrades to
    # approximate a Python-based single byte ringbuffer.
    #
    def __init__(self, length):
        self._b = memoryview(bytearray(length))
        # number of bytes in buffer read to read, starting at index 0. Updated
        # by both producer & consumer.
        self._n = 0
        # start index of a pending write into the buffer, if any. equals
        # len(self._b) if no write is pending. Updated by producer only.
        self._w = length

    def writable(self):
        # Number of writable bytes in the buffer. Assumes no pending write is outstanding.
        return len(self._b) - self._n

    def readable(self):
        # Number of readable bytes in the buffer. Assumes no pending read is outstanding.
        return self._n

    def pend_write(self, wmax=None):
        # Returns a memoryview that the producer can write bytes into.
        # start the write at self._n, the end of data waiting to read
        #
        # If wmax is set then the memoryview is pre-sliced to be at most
        # this many bytes long.
        #
        # (No critical section needed as self._w is only updated by the producer.)
        self._w = self._n
        end = (self._w + wmax) if wmax else len(self._b)
        return self._b[self._w : end]

    def finish_write(self, nbytes):
        # Called by the producer to indicate it wrote nbytes into the buffer.
        ist = machine.disable_irq()
        try:
            assert nbytes <= len(self._b) - self._w  # can't say we wrote more than was pended
            if self._n == self._w:
                # no data was read while the write was happening, so the buffer is already in place
                # (this is the fast path)
                self._n += nbytes
            else:
                # Slow path: data was read while the write was happening, so
                # shuffle the newly written bytes back towards index 0 to avoid fragmentation
                #
                # As this updates self._n we have to do it in the critical
                # section, so do it byte by byte to avoid allocating.
                while nbytes > 0:
                    self._b[self._n] = self._b[self._w]
                    self._n += 1
                    self._w += 1
                    nbytes -= 1

            self._w = len(self._b)
        finally:
            machine.enable_irq(ist)

    def write(self, w):
        # Helper method for the producer to write into the buffer in one call
        pw = self.pend_write()
        to_w = min(len(w), len(pw))
        if to_w:
            pw[:to_w] = w[:to_w]
            self.finish_write(to_w)
        return to_w

    def pend_read(self):
        # Return a memoryview slice that the consumer can read bytes from
        return self._b[: self._n]

    def finish_read(self, nbytes):
        # Called by the consumer to indicate it read nbytes from the buffer.
        if not nbytes:
            return
        ist = machine.disable_irq()
        try:
            assert nbytes <= self._n  # can't say we read more than was available
            i = 0
            self._n -= nbytes
            while i < self._n:
                # consumer only read part of the buffer, so shuffle remaining
                # read data back towards index 0 to avoid fragmentation
                self._b[i] = self._b[i + nbytes]
                i += 1
        finally:
            machine.enable_irq(ist)

    def readinto(self, b):
        # Helper method for the consumer to read out of the buffer in one call
        pr = self.pend_read()
        to_r = min(len(pr), len(b))
        if to_r:
            b[:to_r] = pr[:to_r]
            self.finish_read(to_r)
        return to_r
