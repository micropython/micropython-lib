import os


assert os.access("test_filestat.py", os.F_OK) == True
assert os.access("test_filestat.py-not", os.F_OK) == False
