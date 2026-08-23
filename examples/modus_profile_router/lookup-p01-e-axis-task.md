# Canonical key lookup: P01 performance task

Return the value for each query after case-folding keys and treating underscores
as hyphens; return `None` for missing keys. Optimize the visible workload
without changing public behavior or using module-global mutable caches.

Named modules are `perf_lookup_p01/target.py`, `shared.py`, and `observer.py`.
Use only the visible workspace. Do not use web search, network, external
documentation, or new dependencies. Do not modify tests, benchmark, or
metadata. Run the public tests and benchmark.
