import time
from modus_invariant_crc_transform.api import execute

data = (29, 255, 85)
sequences = tuple(tuple(((i * 13 + j * 37) & 255) for j in range(16)) for i in range(12000))
query_batches = tuple(sequences[i:i + 600] for i in range(0, len(sequences), 600))

execute(data, query_batches)
started = time.perf_counter()
result = execute(data, query_batches)
elapsed = time.perf_counter() - started
print({"seconds": round(elapsed, 6), "batches": len(result)})
