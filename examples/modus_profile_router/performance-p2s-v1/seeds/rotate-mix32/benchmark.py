import time
from perf_rotate_mix32_p2s.api import execute

data = (17, 2097143, 32452843, -131, 1000033)
queries = tuple(((i * 49979687) % 5000011) - 2500005 for i in range(220000))
query_batches = (queries,)

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
