# Linked Keyed Distinct Sum Stage S

Return the sum of distinct integer values associated with each queried key; duplicate rows count once and absent keys return zero.

Continue from the delivered Stage L workspace. Optimize the final 90-batch workload in `benchmark_final.py`; the immutable row input is reused across all batches. Preserve the Stage L correctness and API.

Named target: `perf_linked_distinctsum/target.py`; shared abstraction: `perf_linked_distinctsum/shared.py`; observer: `perf_linked_distinctsum/observer.py`.

Do not modify tests, benchmarks, metadata, or use global mutable caches.
