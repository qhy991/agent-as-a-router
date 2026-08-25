import time
from perf_keyed_distinct_quartic_sum_p2s.api import execute

import random

seed = 20260910
rng = random.Random(seed)
keys = 32003
data = tuple((rng.randrange(keys), rng.randrange(-30, 31)) for _ in range(320000))
queries = tuple(rng.randrange(keys + 700) for _ in range(500))
query_batches = tuple(queries[i:i + 5] for i in range(0, len(queries), 5))

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
