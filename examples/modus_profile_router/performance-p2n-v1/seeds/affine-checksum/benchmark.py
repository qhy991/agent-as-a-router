import time
from perf_affine_checksum_p2n.api import execute

data = (15485863, -97, 1000003)
queries = tuple(((i * 32452843) % 2000003) - 1000001 for i in range(200000))
query_batches = (queries,)

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
