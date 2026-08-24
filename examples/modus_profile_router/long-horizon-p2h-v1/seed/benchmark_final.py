import time
from perf_linked_outdegree.api import execute

import random

seed = 20260830
rng = random.Random(seed)
nodes = 30001
data = tuple((rng.randrange(nodes), rng.randrange(nodes)) for _ in range(200000))
queries = tuple(rng.randrange(nodes + 500) for _ in range(100))
query_batches = tuple(queries[i:i + 5] for i in range(0, len(queries), 5))

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
