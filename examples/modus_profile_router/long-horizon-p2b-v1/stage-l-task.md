# Linked RangeSum Stage L

Return the inclusive-exclusive sum for every (start, stop) query, clamping both endpoints into the data bounds; return zero when the clamped start is not before the clamped stop.

This is the first stage. Optimize the single-batch workload in `benchmark_stage_l.py` while preserving the API and public behavior. A later stage will continue from this exact delivered workspace.

Named target: `perf_linked_rangesum/target.py`; shared abstraction: `perf_linked_rangesum/shared.py`; observer: `perf_linked_rangesum/observer.py`.

Do not modify tests, benchmarks, metadata, or use global mutable caches.
