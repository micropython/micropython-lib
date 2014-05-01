import time
from multiprocessing import Pool

def f(x):
    return x*x

pool = Pool(4)
future = pool.apply_async(f, (10,))
print(future.get())

def f2(x):
    time.sleep(1)
    return x + 1

future = pool.apply_async(f2, (10,))
while not future.ready():
    print("not ready")
    time.sleep(0.1)

print(future.get())
