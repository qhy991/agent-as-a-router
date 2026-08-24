# Linked Connectivity Stage L

Return whether each undirected (source, target) query belongs to one connected component; every node is connected to itself.

This is the first stage. Optimize the single-batch workload in `benchmark_stage_l.py` while preserving the API and public behavior. A later stage will continue from this exact delivered workspace.

Named target: `perf_linked_connectivity/target.py`; shared abstraction: `perf_linked_connectivity/shared.py`; observer: `perf_linked_connectivity/observer.py`.

Do not modify tests, benchmarks, metadata, or use global mutable caches.
