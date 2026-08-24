import time
from perf_reachability_x01.api import execute

import random

nodes = 631
group_size = 13
seed = 20260824
rng = random.Random(seed)
edges = set()
for group_start in range(0, nodes, group_size):
    group_stop = min(nodes, group_start + group_size)
    group_nodes = tuple(range(group_start, group_stop))
    for index, node in enumerate(group_nodes):
        edges.add((node, group_nodes[(index + 1) % len(group_nodes)]))
for group_start in range(0, nodes - group_size, group_size):
    edges.add((group_start + group_size - 1, group_start + group_size))
for _ in range(947):
    source = rng.randrange(nodes)
    target = rng.randrange(nodes)
    if source // group_size <= target // group_size and source != target:
        edges.add((source, target))
data = tuple(sorted(edges))
queries = tuple((rng.randrange(nodes), rng.randrange(nodes)) for _ in range(192))
query_batches = tuple(queries[i:i + 192] for i in range(0, len(queries), 192))

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
