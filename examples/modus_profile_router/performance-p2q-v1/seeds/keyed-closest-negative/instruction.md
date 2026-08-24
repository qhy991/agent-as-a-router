# Closest-to-zero negative value by key: performance task

Task id: `keyed_closest_negative-p2q`

For each queried key, return its greatest associated negative integer; ignore non-negative values and return None when no negative value exists. Optimize the implementation for the visible representative workload without changing public behavior. Do not use module-global mutable caches.

Named target implementation module: `perf_keyed_closest_negative_p2q/target.py`.
Named shared abstraction: `perf_keyed_closest_negative_p2q/shared.py`.
Named observer: `perf_keyed_closest_negative_p2q/observer.py`.

Run correctness and the representative benchmark with:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
