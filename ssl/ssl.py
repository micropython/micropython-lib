from ussl import *

# Constants
for sym in "CERT_NONE", "CERT_OPTIONAL", "CERT_REQUIRED":
    if sym not in globals():
        globals()[sym] = object()
