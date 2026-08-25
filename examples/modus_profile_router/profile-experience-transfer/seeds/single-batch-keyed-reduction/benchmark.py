import time
from modus_single_batch_keyed_reduction.api import execute

import random

seed = 20260917
rng = random.Random(seed)
keys = 34019
data = tuple((rng.randrange(keys), rng.randrange(-1000000, 1000001)) for _ in range(340000))
queries = tuple(rng.randrange(keys + 900) for _ in range(540))
query_batches = (queries,)

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
