import time
from modus_invariant_polynomial_transform.api import execute

data = ((10000019, -3000007, 7000003, 11, -13, 17, 19, -23), 1000033)
queries = tuple(((i * 49999) % 200003) - 100001 for i in range(80000))
query_batches = tuple(queries[i:i + 4000] for i in range(0, len(queries), 4000))

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
