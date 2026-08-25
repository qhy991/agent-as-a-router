import time
from modus_invariant_rolling_hash.api import execute

data = (1000003, 173, 1000033)
sequences = tuple(tuple(((i * 17 + j * 29) & 255) for j in range(12)) for i in range(24000))
query_batches = tuple(sequences[i:i + 1200] for i in range(0, len(sequences), 1200))

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
