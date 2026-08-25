import time
from perf_keyed_closest_negative_p2s.api import execute

import random

seed = 20260909
rng = random.Random(seed)
keys = 32003
data = tuple((rng.randrange(keys), rng.randrange(-1000000, 1000001)) for _ in range(320000))
queries = tuple(rng.randrange(keys + 700) for _ in range(500))
query_batches = (queries,)

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
