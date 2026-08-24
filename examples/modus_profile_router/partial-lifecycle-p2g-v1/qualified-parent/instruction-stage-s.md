# Linked TokenFrequency Stage S

Return the exact occurrence count for every token query, preserving case sensitivity.

Continue from the delivered Stage L workspace. Optimize the final 150-batch workload in `benchmark_final.py`; the immutable graph input is reused across all batches. Preserve the Stage L correctness and API.

Named target: `perf_linked_frequency/target.py`; shared abstraction: `perf_linked_frequency/shared.py`; observer: `perf_linked_frequency/observer.py`.

Do not modify tests, benchmarks, metadata, or use global mutable caches.
