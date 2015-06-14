from io import BytesIO

b = BytesIO(b'This is a test')
assert b.tell() == 0
assert b.read(2) == b'Th'
assert b.tell() == 2
assert b.read() ==  b'is is a test'
assert b.tell() == 14
print("writing")
assert b.write(b'. And more.') == 11
assert b.tell() == 14 + 11
assert b.seek(14) == 14  # go to beginning of newly written data
assert b.read(3) == b'. A'
testb = bytearray(b'len 5')
assert b.readinto(testb) == 5
assert bytes(testb) == b'nd mo'
assert b.read() == b're.'
print("io: tests passed")
