from multiprocessing import Pool

def f(x):
    return x*x

pool = Pool(4)
print(pool.apply(f, (10,)))
