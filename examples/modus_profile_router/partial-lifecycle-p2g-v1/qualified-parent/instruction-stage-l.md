# Linked TokenFrequency Stage L

Return the exact occurrence count for every token query, preserving case sensitivity.

This is the first stage. Optimize the single-batch workload in `benchmark_stage_l.py` while preserving the API and public behavior. A later stage will continue from this exact delivered workspace.

Named target: `perf_linked_frequency/target.py`; shared abstraction: `perf_linked_frequency/shared.py`; observer: `perf_linked_frequency/observer.py`.

Do not modify tests, benchmarks, metadata, or use global mutable caches.
