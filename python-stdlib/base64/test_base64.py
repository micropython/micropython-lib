import base64

b = base64.b64encode(b"zlutoucky kun upel dabelske ody")
print(b)

if b != b"emx1dG91Y2t5IGt1biB1cGVsIGRhYmVsc2tlIG9keQ==":
    raise Exception("Error")

d = base64.b64decode(b)
print(d)

if d != b"zlutoucky kun upel dabelske ody":
    raise Exception("Error")

s0 = b"Aladdin:open sesame"
s1 = base64.encodebytes(s0)
if s1 != b"QWxhZGRpbjpvcGVuIHNlc2FtZQ==\n":
    raise Exception("Error")
print(s1)
s2 = base64.decodebytes(s1)
if s0 != s2:
    raise Exception("Error")

binary = b"\x99\x10\xaa"
b = base64.b64encode(binary)
if b != b"mRCq":
    raise Exception("Error")

d = base64.b64decode(b)
print(d)
if d != binary:
    raise Exception("Error")

d = base64.b32encode(b"zlutoucky kun upel dabelske ody")
if d != b"PJWHK5DPOVRWW6JANN2W4IDVOBSWYIDEMFRGK3DTNNSSA33EPE======":
    raise Exception("Error")

print(d)
b = base64.b32decode(d)
if b != b"zlutoucky kun upel dabelske ody":
    raise Exception("Error")

binary = b"\x99\x10\xaa"
b = base64.b32encode(binary)
if b != b"TEIKU===":
    raise Exception("Error")

d = base64.b32decode(b)
print(d)
if d != binary:
    raise Exception("Error")


print("OK")
