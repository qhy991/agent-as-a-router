import time
from perf_linked_frequency.api import execute

import random

seed = 20260828
rng = random.Random(seed)
data = tuple(f"token-{rng.randrange(1201)}" for _ in range(18000))
queries = tuple(f"token-{rng.randrange(1401)}" for _ in range(480))
query_batches = tuple(queries[i:i + 4] for i in range(0, len(queries), 4))

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
