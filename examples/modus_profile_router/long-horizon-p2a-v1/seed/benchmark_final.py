import time
from perf_linked_connectivity.api import execute

import random

nodes = 811
group_size = 19
seed = 20260826
rng = random.Random(seed)
edges = set()
for group_start in range(0, nodes, group_size):
    group_stop = min(nodes, group_start + group_size)
    group_nodes = tuple(range(group_start, group_stop))
    for index, node in enumerate(group_nodes):
        edges.add(tuple(sorted((node, group_nodes[(index + 1) % len(group_nodes)]))))
for _ in range(1439):
    group_start = rng.randrange(0, nodes, group_size)
    group_stop = min(nodes, group_start + group_size)
    left = rng.randrange(group_start, group_stop)
    right = rng.randrange(group_start, group_stop)
    if left != right:
        edges.add(tuple(sorted((left, right))))
data = tuple(sorted(edges))
queries = tuple((rng.randrange(nodes), rng.randrange(nodes)) for _ in range(300))
query_batches = tuple(queries[i:i + 2] for i in range(0, len(queries), 2))

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
