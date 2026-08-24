# Linked Distinct Out-Degree Stage L

Return the number of distinct outgoing neighbors for each queried node; duplicate edges count once and absent nodes return zero.

This is the first stage. Optimize the single-batch workload in `benchmark_stage_l.py` while preserving the API and public behavior. A later stage will continue from this exact delivered workspace.

Named target: `perf_linked_outdegree/target.py`; shared abstraction: `perf_linked_outdegree/shared.py`; observer: `perf_linked_outdegree/observer.py`.

Do not modify tests, benchmarks, metadata, or use global mutable caches.
