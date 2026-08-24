import time
from perf_rotate_mix32_p2q.api import execute

data = (13, 1048573, 15485863, -97, 1000003)
queries = tuple(((i * 32452843) % 4000007) - 2000003 for i in range(200000))
query_batches = (queries,)

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
