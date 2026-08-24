# Linked RangeSum Stage S

Return the inclusive-exclusive sum for every (start, stop) query, clamping both endpoints into the data bounds; return zero when the clamped start is not before the clamped stop.

Continue from the delivered Stage L workspace. Optimize the final 150-batch workload in `benchmark_final.py`; the immutable graph input is reused across all batches. Preserve the Stage L correctness and API.

Named target: `perf_linked_rangesum/target.py`; shared abstraction: `perf_linked_rangesum/shared.py`; observer: `perf_linked_rangesum/observer.py`.

Do not modify tests, benchmarks, metadata, or use global mutable caches.
