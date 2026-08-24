# Linked Keyed Distinct Sum Stage L

Return the sum of distinct integer values associated with each queried key; duplicate rows count once and absent keys return zero.

This is the first stage. Optimize the single-batch workload in `benchmark_stage_l.py` while preserving the API and public behavior. A later stage will continue from this exact delivered workspace.

Named target: `perf_linked_distinctsum/target.py`; shared abstraction: `perf_linked_distinctsum/shared.py`; observer: `perf_linked_distinctsum/observer.py`.

Do not modify tests, benchmarks, metadata, or use global mutable caches.
