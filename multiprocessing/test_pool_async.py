from multiprocessing import Pool

def f(x):
    return x*x

pool = Pool(4)
future = pool.apply_async(f, (10,))
print(future.get())
