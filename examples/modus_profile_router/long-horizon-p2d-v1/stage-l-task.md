# Linked Membership Stage L

Return whether each query value occurs in the input collection, using exact equality.

This is the first stage. Optimize the single-batch workload in `benchmark_stage_l.py` while preserving the API and public behavior. A later stage will continue from this exact delivered workspace.

Named target: `perf_linked_membership/target.py`; shared abstraction: `perf_linked_membership/shared.py`; observer: `perf_linked_membership/observer.py`.

Do not modify tests, benchmarks, metadata, or use global mutable caches.
