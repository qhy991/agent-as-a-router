import time
from perf_reachability_p04.api import execute

# Prospective many-batch workload: one ring-and-chord input consumed by many
# small query batches, so per-batch recomputation dominates the visible cost.
nodes = 640
edges = [(i, (i + 1) % nodes) for i in range(nodes)]
edges.extend((i, (i + 61) % nodes) for i in range(0, nodes, 4))
edges.extend(((i + 3) % nodes, i) for i in range(0, nodes, 16))
data = tuple(edges)
queries = tuple(((j * 29) % nodes, (j * 53 + 97) % nodes) for j in range(192))
query_batches = tuple(queries[i:i + 2] for i in range(0, len(queries), 2))

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
