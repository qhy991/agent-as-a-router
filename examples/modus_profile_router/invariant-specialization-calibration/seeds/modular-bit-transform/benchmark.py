import time
from modus_invariant_modular_bit_transform.api import execute

data = (23, 4194301, 49979687, 257, 1000037)
queries = tuple(((i * 32452843) % 6000011) - 3000005 for i in range(120000))
query_batches = tuple(queries[i:i + 6000] for i in range(0, len(queries), 6000))

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
