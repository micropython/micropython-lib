# MicroPython aioble module
# MIT license; Copyright (c) 2021 Jim Mussared

from micropython import const, schedule
import uasyncio as asyncio
import binascii
import json
from . import core
from .core import log_info, log_warn, ble, register_irq_handler
from .device import DeviceConnection

_IRQ_ENCRYPTION_UPDATE = const(28)
_IRQ_GET_SECRET = const(29)
_IRQ_SET_SECRET = const(30)
_IRQ_PASSKEY_ACTION = const(31)

_IO_CAPABILITY_DISPLAY_ONLY = const(0)
_IO_CAPABILITY_DISPLAY_YESNO = const(1)
_IO_CAPABILITY_KEYBOARD_ONLY = const(2)
_IO_CAPABILITY_NO_INPUT_OUTPUT = const(3)
_IO_CAPABILITY_KEYBOARD_DISPLAY = const(4)

_PASSKEY_ACTION_INPUT = const(2)
_PASSKEY_ACTION_DISP = const(3)
_PASSKEY_ACTION_NUMCMP = const(4)

_DEFAULT_PATH = "ble_secrets.json"

# Maintain list of known keys, newest at the bottom / end.
_secrets = {}
_modified = False
_path = None

# If set, limit the pairing db to this many peers
limit_peers = None

SEC_TYPES_SELF = (10, )
SEC_TYPES_PEER = (1, 2, 3, 4)


# Must call this before stack startup.
def load_secrets(path=None):
    global _path, _secrets, limit_peers

    # Use path if specified, otherwise use previous path, otherwise use
    # default path.
    _path = path or _path or _DEFAULT_PATH

    # Reset old secrets.
    _secrets.clear()
    try:
        with open(_path, "r") as f:
            entries = json.load(f)
            # Newest entries at at the end, load them first
            for sec_type, key, value in entries:
                if sec_type not in _secrets:
                    _secrets[sec_type] = []
                # Decode bytes from hex.
                _secrets[sec_type].append((binascii.a2b_base64(key), binascii.a2b_base64(value)))

        if limit_peers:
            # If we need to limit loaded keys, ensure the same addresses of each type are loaded
            keep_keys = None
            for sec_type in SEC_TYPES_PEER:
                if sec_type not in _secrets:
                    continue
                secrets = _secrets[sec_type]
                if len(secrets) > limit_peers:
                    if not keep_keys:
                        keep_keys = [key for key, _ in secrets[-limit_peers:]]
                        log_warn("Limiting keys to", keep_keys)
                    
                    keep_entries = [entry for entry in secrets if entry[0] in keep_keys]
                    while len(keep_entries) < limit_peers:
                        for entry in reversed(secrets):
                            if entry not in keep_entries:
                                keep_entries.append(entry)
                    _secrets[sec_type] = keep_entries
        _log_peers("loaded")

    except:
        log_warn("No secrets available")


# Call this whenever the secrets dict changes.
def _save_secrets(arg=None):
    global _modified, _path

    _path = _path or _DEFAULT_PATH

    if not _modified:
        # Only save if the secrets changed.
        return

    _log_peers('save_secrets')
    
    with open(_path, "w") as f:
        # Convert bytes to hex strings (otherwise JSON will treat them like
        # strings).
        json_secrets = [
            (sec_type, binascii.b2a_base64(key), binascii.b2a_base64(value))
             for sec_type in _secrets for key, value in _secrets[sec_type]
        ]
        json.dump(json_secrets, f)
        _modified = False


def _remove_entry(sec_type, key):
    secrets = _secrets[sec_type]

    # Delete existing secrets matching the type and key.
    deleted = False
    for to_delete in [
        entry for entry in secrets if entry[0] == key
    ]:
        log_info("Removing existing secret matching key")
        secrets.remove(to_delete)
        deleted = True

    return deleted


def _log_peers(heading=""):
    if core.log_level <= 2:
        return
    log_info("secrets:", heading)
    for sec_type in SEC_TYPES_PEER:
        log_info("-", sec_type)

        if sec_type not in _secrets:
            continue
        secrets = _secrets[sec_type]
        for key, value in secrets:
            log_info("  - %s: %s..." % (key, value[0:16]))


def _security_irq(event, data):
    global _modified

    if event == _IRQ_ENCRYPTION_UPDATE:
        # Connection has updated (usually due to pairing).
        conn_handle, encrypted, authenticated, bonded, key_size = data
        log_info("encryption update", conn_handle, encrypted, authenticated, bonded, key_size)
        if connection := DeviceConnection._connected.get(conn_handle, None):
            connection.encrypted = encrypted
            connection.authenticated = authenticated
            connection.bonded = bonded
            connection.key_size = key_size
            # TODO: Handle failure.
            if encrypted and connection._pair_event:
                connection._pair_event.set()

    elif event == _IRQ_SET_SECRET:
        sec_type, key, value = data
        key = bytes(key)
        value = bytes(value) if value else None

        is_saving = value is not None
        is_deleting = not is_saving

        if core.log_level > 2:
            if is_deleting:
                log_info("del secret:", key)
            else:
                shortval = value
                if len(value) > 16:
                    shortval = value[0:16] + b"..."
                log_info("set secret:", sec_type, key, shortval)

        if sec_type not in _secrets:
            _secrets[sec_type] = []
        secrets = _secrets[sec_type]
        
        # Delete existing secrets matching the type and key.
        removed = _remove_entry(sec_type, key)

        if is_deleting and not removed:
            # Delete mode, but no entries were deleted
            return False

        if is_saving:
            # Save new secret.
            if limit_peers and sec_type in SEC_TYPES_PEER and len(secrets) >= limit_peers:
                addr, _ = secrets[0]
                log_warn("Removing old peer to make space for new one")
                ble.gap_unpair(addr)
                log_info("Removed:", addr)
            # Add new value to database
            secrets.append((key, value))

        _log_peers("set_secret")            

        # Queue up a save (don't synchronously write to flash).
        _modified = True
        schedule(_save_secrets, None)

        return True

    elif event == _IRQ_GET_SECRET:
        sec_type, index, key = data

        log_info("get secret:", sec_type, index, bytes(key) if key else None)

        secrets = _secrets.get(sec_type, [])
        if key is None:
            # Return the index'th secret of this type.
            # This is used when loading "all" secrets at startup
            if len(secrets) > index:
                key, val = secrets[index]
                return val

            return None
        else:
            # Return the secret for this key (or None).
            key = bytes(key)

            for k, v in secrets:
                if k == key:
                    return v
            return None

    elif event == _IRQ_PASSKEY_ACTION:
        conn_handle, action, passkey = data
        log_info("passkey action", conn_handle, action, passkey)
        # if action == _PASSKEY_ACTION_NUMCMP:
        #     # TODO: Show this passkey and confirm accept/reject.
        #     accept = 1
        #     self._ble.gap_passkey(conn_handle, action, accept)
        # elif action == _PASSKEY_ACTION_DISP:
        #     # TODO: Generate and display a passkey so the remote device can enter it.
        #     passkey = 123456
        #     self._ble.gap_passkey(conn_handle, action, passkey)
        # elif action == _PASSKEY_ACTION_INPUT:
        #     # TODO: Ask the user to enter the passkey shown on the remote device.
        #     passkey = 123456
        #     self._ble.gap_passkey(conn_handle, action, passkey)
        # else:
        #     log_warn("unknown passkey action")


def _security_shutdown():
    global _secrets, _modified, _path
    _secrets = {}
    _modified = False
    _path = None


register_irq_handler(_security_irq, _security_shutdown)


# Use device.pair() rather than calling this directly.
async def pair(
    connection,
    bond=True,
    le_secure=True,
    mitm=False,
    io=_IO_CAPABILITY_NO_INPUT_OUTPUT,
    timeout_ms=20000,
):
    ble.config(bond=bond, le_secure=le_secure, mitm=mitm, io=io)

    with connection.timeout(timeout_ms):
        connection._pair_event = asyncio.ThreadSafeFlag()
        ble.gap_pair(connection._conn_handle)
        await connection._pair_event.wait()
        # TODO: Allow the passkey action to return to here and
        # invoke a callback or task to process the action.
