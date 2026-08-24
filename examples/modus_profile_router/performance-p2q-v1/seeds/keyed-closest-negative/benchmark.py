import time
from perf_keyed_closest_negative_p2q.api import execute

import random

seed = 20260906
rng = random.Random(seed)
keys = 30001
data = tuple((rng.randrange(keys), rng.randrange(-1000000, 1000001)) for _ in range(300000))
queries = tuple(rng.randrange(keys + 500) for _ in range(450))
query_batches = (queries,)

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
