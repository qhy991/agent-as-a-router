# Distinct-value fourth-power sum by key: performance task

Task id: `keyed_distinct_quartic_sum-p2s`

Return the sum of fourth powers of distinct integer values associated with each queried key; duplicate rows count once and absent keys return zero. Optimize the implementation for the visible representative workload without changing public behavior. Do not use module-global mutable caches.

Named target implementation module: `perf_keyed_distinct_quartic_sum_p2s/target.py`.
Named shared abstraction: `perf_keyed_distinct_quartic_sum_p2s/shared.py`.
Named observer: `perf_keyed_distinct_quartic_sum_p2s/observer.py`.

Run correctness and the representative benchmark with:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
