import time
from modus_repeated_batch_keyed_aggregate.api import execute

import random

seed = 20260918
rng = random.Random(seed)
keys = 34019
data = tuple((rng.randrange(keys), rng.randrange(-30, 31)) for _ in range(340000))
queries = tuple(rng.randrange(keys + 900) for _ in range(540))
query_batches = tuple(queries[i:i + 5] for i in range(0, len(queries), 5))

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
