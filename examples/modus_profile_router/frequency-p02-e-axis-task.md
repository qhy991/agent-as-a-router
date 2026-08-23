# Token frequency queries: P02 performance task

Return the exact occurrence count for every token query, preserving case
sensitivity. Optimize the implementation for the visible representative
workload without changing public behavior. Do not use module-global mutable
caches.

Named target implementation module: `perf_frequency_p02/target.py`.
Named shared abstraction: `perf_frequency_p02/shared.py`.
Named observer: `perf_frequency_p02/observer.py`.

Use only the visible workspace. Do not use web search, a browser, network
access, or external documentation. Do not modify tests, benchmark code,
metadata, or dependencies.

Run:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
