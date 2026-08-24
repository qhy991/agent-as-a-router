import time
from perf_linked_membership.api import execute

import random

seed = 20260829
rng = random.Random(seed)
data = tuple(rng.randrange(250003) for _ in range(20000))
queries = tuple(rng.randrange(300007) for _ in range(600))
query_batches = tuple(queries[i:i + 600] for i in range(0, len(queries), 600))

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
