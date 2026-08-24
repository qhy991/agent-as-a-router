import time
from perf_linked_rangesum.api import execute

import random

seed = 20260827
rng = random.Random(seed)
data = tuple(rng.randrange(-100, 101) for _ in range(6000))
queries = tuple(
    (lambda start, width: (start, min(len(data), start + width)))(
        rng.randrange(0, 5800), rng.randrange(1, 201)
    )
    for _ in range(360)
)
query_batches = tuple(queries[i:i + 3] for i in range(0, len(queries), 3))

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
