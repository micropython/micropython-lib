import os

print(os.getcwd())

l = os.listdir()
print(l)
assert "test_dirs.py" in l
assert "os" in l

# return bytes if a bytes path is given
l = os.listdir(b".")
assert b"test_dirs.py" in l

for t in os.walk("."):
    print(t)

for t in os.walk(".", False):
    print(t)
