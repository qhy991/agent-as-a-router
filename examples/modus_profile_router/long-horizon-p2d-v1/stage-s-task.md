# Linked Membership Stage S

Return whether each query value occurs in the input collection, using exact equality.

Continue from the delivered Stage L workspace. Optimize the final 150-batch workload in `benchmark_final.py`; the immutable graph input is reused across all batches. Preserve the Stage L correctness and API.

Named target: `perf_linked_membership/target.py`; shared abstraction: `perf_linked_membership/shared.py`; observer: `perf_linked_membership/observer.py`.

Do not modify tests, benchmarks, metadata, or use global mutable caches.
