import time
from perf_linked_keyedmax.api import execute

import random

seed = 20260831
rng = random.Random(seed)
keys = 25001
data = tuple((rng.randrange(keys), rng.randrange(-1000000, 1000001)) for _ in range(180000))
queries = tuple(rng.randrange(keys + 500) for _ in range(300))
query_batches = tuple(queries[i:i + 300] for i in range(0, len(queries), 300))

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
