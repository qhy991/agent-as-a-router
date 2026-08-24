import time
from perf_groupdistinct_p2j.api import execute

import random

seed = 20260901
rng = random.Random(seed)
keys = 25001
data = tuple((rng.randrange(keys), rng.randrange(1000003)) for _ in range(180000))
queries = tuple(rng.randrange(keys + 500) for _ in range(300))
query_batches = (queries,)

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
