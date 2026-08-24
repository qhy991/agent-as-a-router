# Linked Keyed Maximum Stage S

Return the maximum integer value for each queried key across all rows; duplicate keys are allowed and absent keys return None.

Continue from the delivered Stage L workspace. Optimize the final 60-batch workload in `benchmark_final.py`; the immutable row input is reused across all batches. Preserve the Stage L correctness and API.

Named target: `perf_linked_keyedmax/target.py`; shared abstraction: `perf_linked_keyedmax/shared.py`; observer: `perf_linked_keyedmax/observer.py`.

Do not modify tests, benchmarks, metadata, or use global mutable caches.
