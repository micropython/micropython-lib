import os
import os.path

def resource_stream(package, resource):
    p = __import__(package)
    d = os.path.dirname(p.__file__)
    if d[0] != "/":
        d = os.getcwd() + "/" + d
    return open(d + "/" + resource, "rb")
