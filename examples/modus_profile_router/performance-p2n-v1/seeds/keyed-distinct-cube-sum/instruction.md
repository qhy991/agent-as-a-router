# Distinct-value cube sum by key: performance task

Task id: `keyed_distinct_cube_sum-p2n`

Return the sum of cubes of distinct integer values associated with each queried key; duplicate rows count once and absent keys return zero. Optimize the implementation for the visible representative workload without changing public behavior. Do not use module-global mutable caches.

Named target implementation module: `perf_keyed_distinct_cube_sum_p2n/target.py`.
Named shared abstraction: `perf_keyed_distinct_cube_sum_p2n/shared.py`.
Named observer: `perf_keyed_distinct_cube_sum_p2n/observer.py`.

Run correctness and the representative benchmark with:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
