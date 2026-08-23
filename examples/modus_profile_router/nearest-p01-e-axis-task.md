# Nearest numeric value: P01 performance task

Return the nearest stored value for each numeric query; on equal distance
choose the smaller value, and return `None` for empty input. Optimize the
implementation for the visible representative workload without changing
public behavior. Do not use module-global mutable caches.

Named target implementation module: `perf_nearest_p01/target.py`.
Named shared abstraction: `perf_nearest_p01/shared.py`.
Named observer: `perf_nearest_p01/observer.py`.

Use only the visible workspace. Do not use web search, a browser, network
access, or external documentation. Do not modify tests, benchmark code,
metadata, or dependencies.

Run:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
