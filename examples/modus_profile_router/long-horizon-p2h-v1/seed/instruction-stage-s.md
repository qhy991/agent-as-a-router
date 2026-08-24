# Linked Distinct Out-Degree Stage S

Return the number of distinct outgoing neighbors for each queried node; duplicate edges count once and absent nodes return zero.

Continue from the delivered Stage L workspace. Optimize the final 20-batch workload in `benchmark_final.py`; the immutable edge input is reused across all batches. Preserve the Stage L correctness and API.

Named target: `perf_linked_outdegree/target.py`; shared abstraction: `perf_linked_outdegree/shared.py`; observer: `perf_linked_outdegree/observer.py`.

Do not modify tests, benchmarks, metadata, or use global mutable caches.
