import uuid

u1 = uuid.uuid4()
u2 = uuid.uuid4()

assert str(u1) != str(u2), "Two uuid4 should not match"

assert len(str(u1)) == len(str(u1)) == 36

assert str(repr(u1)).startswith("<UUID")
assert str(repr(u1)).endswith(">")

assert len(u1.hex) == 32

print("OK")
