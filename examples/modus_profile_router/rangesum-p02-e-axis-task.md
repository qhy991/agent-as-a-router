# Repeated range sums: P02 performance task

Return the inclusive-exclusive sum for every `(start, stop)` query, clamping
both endpoints into the data bounds; return zero when the clamped start is not
before the clamped stop. Optimize the implementation for the visible
representative workload without changing public behavior. Do not use
module-global mutable caches.

Named target implementation module: `perf_rangesum_p02/target.py`.
Named shared abstraction: `perf_rangesum_p02/shared.py`.
Named observer: `perf_rangesum_p02/observer.py`.

Use only the visible workspace. Do not use web search, a browser, network
access, or external documentation. Do not modify tests, benchmark code,
metadata, or dependencies.

Run:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
