# MicroPython aioble module
# MIT license; Copyright (c) 2021 Jim Mussared

from micropython import const, schedule
import uasyncio as asyncio
import binascii
import ustruct
import json

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

# Maintain list of known keys, newest at the top.
_secrets = []
_modified = False
_path = None

connected_sec = None
gatt_svc = None


# Must call this before stack startup.
def load_secrets(path=None):
    global _path, _secrets

    # Use path if specified, otherwise use previous path, otherwise use
    # default path.
    _path = path or _path or _DEFAULT_PATH

    # Reset old secrets.
    _secrets = []
    try:
        with open(_path, "r") as f:
            entries = json.load(f)
            for sec_type, key, value, *digest in entries:
                digest = digest[0] or None
                # Decode bytes from hex.
                _secrets.append(((sec_type, binascii.a2b_base64(key)), binascii.a2b_base64(value), digest))
    except:
        log_warn("No secrets available")


# Call this whenever the secrets dict changes.
def _save_secrets(arg=None):
    global _modified, _path

    _path = _path or _DEFAULT_PATH

    if not _modified:
        # Only save if the secrets changed.
        return

    with open(_path, "w") as f:
        # Convert bytes to hex strings (otherwise JSON will treat them like
        # strings).
        json_secrets = [
            (sec_type, binascii.b2a_base64(key), binascii.b2a_base64(value), digest)
            for (sec_type, key), value, digest in _secrets
        ]
        json.dump(json_secrets, f)
        _modified = False


def _security_irq(event, data):
    global _modified, connected_sec, gatt_svc

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

            if bonded and \
                    None not in (gatt_svc, connected_sec) and \
                    connected_sec[2] != gatt_svc.hexdigest:
                gatt_svc.send_changed(connection)

                # Update the hash in the database
                _secrets.remove(connected_sec)
                updated_sec = connected_sec[:-1] + (gatt_svc.hexdigest,)
                _secrets.insert(0, updated_sec)
                # Queue up a save (don't synchronously write to flash).
                _modified = True
                schedule(_save_secrets, None)

    elif event == _IRQ_SET_SECRET:
        sec_type, key, value = data
        key = sec_type, bytes(key)
        value = bytes(value) if value else None

        log_info("set secret:", key, value)

        if value is None:
            # Delete secret.
            for to_delete in [
                entry for entry in _secrets if entry[0] == key
            ]:
                _secrets.remove(to_delete)

        else:
            # Save secret.
            current_digest = gatt_svc.hexdigest if gatt_svc else None
            _secrets.insert(0, (key, value, current_digest))

        # Queue up a save (don't synchronously write to flash).
        _modified = True
        schedule(_save_secrets, None)

        return True

    elif event == _IRQ_GET_SECRET:
        sec_type, index, key = data

        log_info("get secret:", sec_type, index, bytes(key) if key else None)

        if key is None:
            # Return the index'th secret of this type.
            i = 0
            for (t, _key), value, digest in _secrets:
                if t == sec_type:
                    if i == index:
                        return value
                    i += 1
            return None
        else:
            # Return the secret for this key (or None).
            key = sec_type, bytes(key)

            for k, v, d in _secrets:
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


register_irq_handler(_security_irq)


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
