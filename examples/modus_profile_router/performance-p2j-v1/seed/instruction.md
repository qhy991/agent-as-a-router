# Distinct values by key: performance task

Task id: `group-distinct-p2j`

Return the number of distinct values associated with each queried key; duplicate rows count once and absent keys return zero. Optimize the implementation for the visible representative workload without changing public behavior. Do not use module-global mutable caches.

Named target implementation module: `perf_groupdistinct_p2j/target.py`.
Named shared abstraction: `perf_groupdistinct_p2j/shared.py`.
Named observer: `perf_groupdistinct_p2j/observer.py`.

Run correctness and the representative benchmark with:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
