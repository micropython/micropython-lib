from mip import _mpy_tag_ok

# Exact match on version/sub-version/arch (bits 0-15), no arch-flags.
assert _mpy_tag_ok(0x0A06, 0x0A06) is True

# Different version/sub-version/arch -> reject.
assert _mpy_tag_ok(0x0A06, 0x0B06) is False
assert _mpy_tag_ok(0x0A06, 0x0A07) is False

# Arch-flags (bits 16+): tag's required flags must be a subset of the
# device's, not an exact match.
assert _mpy_tag_ok(0x0A06 | (0b001 << 16), 0x0A06 | (0b011 << 16)) is True
assert _mpy_tag_ok(0x0A06 | (0b011 << 16), 0x0A06 | (0b001 << 16)) is False
assert _mpy_tag_ok(0x0A06, 0x0A06 | (0b111 << 16)) is True  # tag needs nothing
assert _mpy_tag_ok(0x0A06 | (0b111 << 16), 0x0A06) is False  # device supports nothing

# No _mpy support on the device (e.g. bytecode-only build).
assert _mpy_tag_ok(0x0A06, None) is False

# Bytecode-only tag (arch nibble 0): only the major version must match --
# sub-version and arch are ignored, mirroring mp_raw_code_load()'s own
# fast path for non-native code in py/persistentcode.c.
_BYTECODE_TAG = 0x0206  # version=6, sub-version=2, arch=NONE(0)
assert _mpy_tag_ok(_BYTECODE_TAG, 0x0A06) is True  # same major, different sub/arch on device
assert _mpy_tag_ok(_BYTECODE_TAG, 0x0107) is False  # different major version

# Omitting device_mpy falls back to sys.implementation._mpy; just check it
# runs without raising, since that value depends on the build running the test.
_mpy_tag_ok(0x0A06)

print("PASS")
