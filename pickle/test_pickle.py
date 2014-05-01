import pickle
import sys
import io

pickle.dump({1:2}, sys.stdout)

print(pickle.loads("{4:5}"))
