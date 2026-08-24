# Linked Connectivity Stage S

Return whether each undirected (source, target) query belongs to one connected component; every node is connected to itself.

Continue from the delivered Stage L workspace. Optimize the final 150-batch workload in `benchmark_final.py`; the immutable graph input is reused across all batches. Preserve the Stage L correctness and API.

Named target: `perf_linked_connectivity/target.py`; shared abstraction: `perf_linked_connectivity/shared.py`; observer: `perf_linked_connectivity/observer.py`.

Do not modify tests, benchmarks, metadata, or use global mutable caches.
