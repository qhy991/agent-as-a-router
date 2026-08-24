# Linked Keyed Maximum Stage L

Return the maximum integer value for each queried key across all rows; duplicate keys are allowed and absent keys return None.

This is the first stage. Optimize the single-batch workload in `benchmark_stage_l.py` while preserving the API and public behavior. A later stage will continue from this exact delivered workspace.

Named target: `perf_linked_keyedmax/target.py`; shared abstraction: `perf_linked_keyedmax/shared.py`; observer: `perf_linked_keyedmax/observer.py`.

Do not modify tests, benchmarks, metadata, or use global mutable caches.
