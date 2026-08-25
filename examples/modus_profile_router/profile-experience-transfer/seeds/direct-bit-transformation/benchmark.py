import time
from modus_direct_bit_transformation.api import execute

data = (23, 4194301, 49979687, 257, 1000037)
queries = tuple(((i * 32452843) % 6000011) - 3000005 for i in range(240000))
query_batches = (queries,)

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
