# MicroPython USB MIDI module
# MIT license; Copyright (c) 2023 Paul Hamshere, 2023-2024 Angus Gratton
from micropython import const, schedule
import struct

from .core import Interface, Buffer

_EP_IN_FLAG = const(1 << 7)

_INTERFACE_CLASS_AUDIO = const(0x01)
_INTERFACE_SUBCLASS_AUDIO_CONTROL = const(0x01)
_INTERFACE_SUBCLASS_AUDIO_MIDISTREAMING = const(0x03)

# Audio subclass extends the standard endpoint descriptor
# with two extra bytes
_STD_DESC_AUDIO_ENDPOINT_LEN = const(9)
_CLASS_DESC_ENDPOINT_LEN = const(5)

_STD_DESC_ENDPOINT_TYPE = const(0x5)

_JACK_TYPE_EMBEDDED = const(0x01)
_JACK_TYPE_EXTERNAL = const(0x02)

_JACK_IN_DESC_LEN = const(6)
_JACK_OUT_DESC_LEN = const(9)

# MIDI Status bytes. For Channel messages these are only the upper 4 bits, ORed with the channel number.
# As per https://www.midi.org/specifications-old/item/table-1-summary-of-midi-message
_MIDI_NOTE_OFF = const(0x80)
_MIDI_NOTE_ON = const(0x90)
_MIDI_POLY_KEYPRESS = const(0xA0)
_MIDI_CONTROL_CHANGE = const(0xB0)

# USB-MIDI CINs (Code Index Numbers), as per USB MIDI Table 4-1
_CIN_SYS_COMMON_2BYTE = const(0x2)
_CIN_SYS_COMMON_3BYTE = const(0x3)
_CIN_SYSEX_START = const(0x4)
_CIN_SYSEX_END_1BYTE = const(0x5)
_CIN_SYSEX_END_2BYTE = const(0x6)
_CIN_SYSEX_END_3BYTE = const(0x7)
_CIN_NOTE_OFF = const(0x8)
_CIN_NOTE_ON = const(0x9)
_CIN_POLY_KEYPRESS = const(0xA)
_CIN_CONTROL_CHANGE = const(0xB)
_CIN_PROGRAM_CHANGE = const(0xC)
_CIN_CHANNEL_PRESSURE = const(0xD)
_CIN_PITCH_BEND = const(0xE)
_CIN_SINGLE_BYTE = const(0xF)  # Not currently supported

# Jack IDs for a simple bidrectional MIDI device(!)
_EMB_IN_JACK_ID = const(1)
_EXT_IN_JACK_ID = const(2)
_EMB_OUT_JACK_ID = const(3)
_EXT_OUT_JACK_ID = const(4)

# Data flows, as modelled by USB-MIDI and this hypothetical interface, are as follows:
# Device RX = USB OUT EP => _EMB_IN_JACK => _EMB_OUT_JACK
# Device TX = _EXT_IN_JACK => _EMB_OUT_JACK => USB IN EP


class MIDIInterface(Interface):
    # Base class to implement a USB MIDI device in Python.
    #
    # To be compliant this also regisers a dummy USB Audio interface, but that
    # interface isn't otherwise used.

    def __init__(self, rxlen=16, txlen=16):
        # Arguments are size of transmit and receive buffers in bytes.

        super().__init__()
        self.ep_out = None  # Set during enumeration. RX direction (host to device)
        self.ep_in = None  # TX direction (device to host)
        self._rx = Buffer(rxlen)
        self._tx = Buffer(txlen)

    # Callbacks for handling received MIDI messages.
    #
    # Subclasses can choose between overriding on_midi_event
    # and handling all MIDI events manually, or overriding the
    # functions for note on/off and control change, only.

    def on_midi_event(self, cin, midi0, midi1, midi2):
        ch = midi0 & 0x0F
        if cin == _CIN_NOTE_ON:
            self.on_note_on(ch, midi1, midi2)
        elif cin == _CIN_NOTE_OFF:
            self.on_note_off(ch, midi1, midi2)
        elif cin == _CIN_CONTROL_CHANGE:
            self.on_control_change(ch, midi1, midi2)

    def on_note_on(self, channel, pitch, vel):
        pass  # Override to handle Note On messages

    def on_note_off(self, channel, pitch, vel):
        pass  # Override to handle Note On messages

    def on_control_change(self, channel, controller, value):
        pass  # Override to handle Control Change messages

    # Helper functions for sending common MIDI messages

    def note_on(self, channel, pitch, vel=0x40):
        self.send_event(_CIN_NOTE_ON, _MIDI_NOTE_ON | channel, pitch, vel)

    def note_off(self, channel, pitch, vel=0x40):
        self.send_event(_CIN_NOTE_OFF, _MIDI_NOTE_OFF | channel, pitch, vel)

    def control_change(self, channel, controller, value):
        self.send_event(_CIN_CONTROL_CHANGE, _MIDI_CONTROL_CHANGE | channel, controller, value)

    def send_event(self, cin, midi0, midi1=0, midi2=0):
        # Queue a MIDI Event Packet to send to the host.
        #
        # CIN = USB-MIDI Code Index Number, see USB MIDI 1.0 section 4 "USB-MIDI Event Packets"
        #
        # Remaining arguments are 0-3 MIDI data bytes.
        #
        # Note this function returns when the MIDI Event Packet has been queued,
        # not when it's been received by the host.
        #
        # Returns False if the TX buffer is full and the MIDI Event could not be queued.
        w = self._tx.pend_write()
        if len(w) < 4:
            return False  # TX buffer is full. TODO: block here?
        w[0] = cin  # leave cable number as 0?
        w[1] = midi0
        w[2] = midi1
        w[3] = midi2
        self._tx.finish_write(4)
        self._tx_xfer()
        return True

    def _tx_xfer(self):
        # Keep an active IN transfer to send data to the host, whenever
        # there is data to send.
        if self.is_open() and not self.xfer_pending(self.ep_in) and self._tx.readable():
            self.submit_xfer(self.ep_in, self._tx.pend_read(), self._tx_cb)

    def _tx_cb(self, ep, res, num_bytes):
        if res == 0:
            self._tx.finish_read(num_bytes)
        self._tx_xfer()

    def _rx_xfer(self):
        # Keep an active OUT transfer to receive MIDI events from the host
        if self.is_open() and not self.xfer_pending(self.ep_out) and self._rx.writable():
            self.submit_xfer(self.ep_out, self._rx.pend_write(), self._rx_cb)

    def _rx_cb(self, ep, res, num_bytes):
        if res == 0:
            self._rx.finish_write(num_bytes)
            schedule(self._on_rx, None)
        self._rx_xfer()

    def on_open(self):
        super().on_open()
        # kick off any transfers that may have queued while the device was not open
        self._tx_xfer()
        self._rx_xfer()

    def _on_rx(self, _):
        # Receive MIDI events. Called via micropython.schedule, outside of the USB callback function.
        m = self._rx.pend_read()
        i = 0
        while i <= len(m) - 4:
            cin = m[i] & 0x0F
            self.on_midi_event(cin, m[i + 1], m[i + 2], m[i + 3])
            i += 4
        self._rx.finish_read(i)

    def desc_cfg(self, desc, itf_num, ep_num, strs):
        # Start by registering a USB Audio Control interface, that is required to point to the
        # actual MIDI interface
        desc.interface(itf_num, 0, _INTERFACE_CLASS_AUDIO, _INTERFACE_SUBCLASS_AUDIO_CONTROL)

        # Append the class-specific AudioControl interface descriptor
        desc.pack(
            "<BBBHHBB",
            9,  # bLength
            0x24,  # bDescriptorType CS_INTERFACE
            0x01,  # bDescriptorSubtype MS_HEADER
            0x0100,  # BcdADC
            0x0009,  # wTotalLength
            0x01,  # bInCollection,
            itf_num + 1,  # baInterfaceNr - points to the MIDI Streaming interface
        )

        # Next add the MIDI Streaming interface descriptor
        desc.interface(
            itf_num + 1, 2, _INTERFACE_CLASS_AUDIO, _INTERFACE_SUBCLASS_AUDIO_MIDISTREAMING
        )

        # Append the class-specific interface descriptors

        # Midi Streaming interface descriptor
        desc.pack(
            "<BBBHH",
            7,  # bLength
            0x24,  # bDescriptorType CS_INTERFACE
            0x01,  # bDescriptorSubtype MS_HEADER
            0x0100,  # BcdADC
            # wTotalLength: of all class-specific descriptors
            7
            + 2
            * (
                _JACK_IN_DESC_LEN
                + _JACK_OUT_DESC_LEN
                + _STD_DESC_AUDIO_ENDPOINT_LEN
                + _CLASS_DESC_ENDPOINT_LEN
            ),
        )

        # The USB MIDI standard 1.0 allows modelling a baffling range of MIDI
        # devices with different permutations of Jack descriptors, with a lot of
        # scope for indicating internal connections in the device (as
        # "virtualised" by the USB MIDI standard). Much of the options don't
        # really change the USB behaviour but provide metadata to the host.
        #
        # As observed elsewhere online, the standard ends up being pretty
        # complex and unclear in parts, but there is a clear simple example in
        # an Appendix. So nearly everyone implements the device from the
        # Appendix as-is, even when it's not a good fit for their application,
        # and ignores the rest of the standard.
        #
        # For now, this is what this class does as well.

        _jack_in_desc(desc, _JACK_TYPE_EMBEDDED, _EMB_IN_JACK_ID)
        _jack_in_desc(desc, _JACK_TYPE_EXTERNAL, _EXT_IN_JACK_ID)
        _jack_out_desc(desc, _JACK_TYPE_EMBEDDED, _EMB_OUT_JACK_ID, _EXT_IN_JACK_ID, 1)
        _jack_out_desc(desc, _JACK_TYPE_EXTERNAL, _EXT_OUT_JACK_ID, _EMB_IN_JACK_ID, 1)

        # One MIDI endpoint in each direction, plus the
        # associated CS descriptors

        self.ep_out = ep_num
        self.ep_in = ep_num | _EP_IN_FLAG

        # rx side, USB "in" endpoint and embedded MIDI IN Jacks
        _audio_endpoint(desc, self.ep_in, _EMB_OUT_JACK_ID)

        # tx side, USB "out" endpoint and embedded MIDI OUT jacks
        _audio_endpoint(desc, self.ep_out, _EMB_IN_JACK_ID)

    def num_itfs(self):
        return 2

    def num_eps(self):
        return 1


def _jack_in_desc(desc, bJackType, bJackID):
    # Utility function appends a "JACK IN" descriptor with
    # specified bJackType and bJackID
    desc.pack(
        "<BBBBBB",
        _JACK_IN_DESC_LEN,  # bLength
        0x24,  # bDescriptorType CS_INTERFACE
        0x02,  # bDescriptorSubtype MIDI_IN_JACK
        bJackType,
        bJackID,
        0x00,  # iJack, no string descriptor support yet
    )


def _jack_out_desc(desc, bJackType, bJackID, bSourceId, bSourcePin):
    # Utility function appends a "JACK IN" descriptor with
    # specified bJackType and bJackID
    desc.pack(
        "<BBBBBBBBB",
        _JACK_OUT_DESC_LEN,  # bLength
        0x24,  # bDescriptorType CS_INTERFACE
        0x03,  # bDescriptorSubtype MIDI_OUT_JACK
        bJackType,
        bJackID,
        0x01,  # bNrInputPins
        bSourceId,  # baSourceID(1)
        bSourcePin,  # baSourcePin(1)
        0x00,  # iJack, no string descriptor support yet
    )


def _audio_endpoint(desc, bEndpointAddress, emb_jack_id):
    # Append a standard USB endpoint descriptor and the USB class endpoint descriptor
    # for this endpoint.
    #
    # Audio Class devices extend the standard endpoint descriptor with two extra bytes,
    # so we can't easily call desc.endpoint() for the first part.
    desc.pack(
        # Standard USB endpoint descriptor (plus audio tweaks)
        "<BBBBHBBB"
        # Class endpoint descriptor
        "BBBBB",
        _STD_DESC_AUDIO_ENDPOINT_LEN,  # wLength
        _STD_DESC_ENDPOINT_TYPE,  # bDescriptorType
        bEndpointAddress,
        2,  # bmAttributes, bulk
        64,  # wMaxPacketSize
        0,  # bInterval
        0,  # bRefresh (unused)
        0,  # bSynchInterval (unused)
        _CLASS_DESC_ENDPOINT_LEN,  # bLength
        0x25,  # bDescriptorType CS_ENDPOINT
        0x01,  # bDescriptorSubtype MS_GENERAL
        1,  # bNumEmbMIDIJack
        emb_jack_id,  # BaAssocJackID(1)
    )
