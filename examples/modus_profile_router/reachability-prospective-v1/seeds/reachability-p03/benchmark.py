import time
from perf_reachability_p03.api import execute

# Prospective cycle-and-chord workload: ring edges plus skip chords make every
# node mutually reachable, so every query is decided by component membership.
nodes = 640
edges = [(i, (i + 1) % nodes) for i in range(nodes)]
edges.extend((i, (i + 61) % nodes) for i in range(0, nodes, 4))
edges.extend(((i + 3) % nodes, i) for i in range(0, nodes, 16))
data = tuple(edges)
queries = tuple(((j * 29) % nodes, (j * 53 + 97) % nodes) for j in range(192))
query_batches = tuple(queries[i:i + 6] for i in range(0, len(queries), 6))

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
