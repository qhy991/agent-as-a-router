import time
from perf_keyed_distinct_cube_sum_p2n.api import execute

import random

seed = 20260905
rng = random.Random(seed)
keys = 30001
data = tuple((rng.randrange(keys), rng.randrange(-100, 101)) for _ in range(300000))
queries = tuple(rng.randrange(keys + 500) for _ in range(450))
query_batches = tuple(queries[i:i + 5] for i in range(0, len(queries), 5))

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
