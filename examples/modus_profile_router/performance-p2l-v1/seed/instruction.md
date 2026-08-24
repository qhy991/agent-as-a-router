# Distinct-value squared energy by key: performance task

Task id: `keyed-distinct-energy-p2l`

Return the sum of squares of distinct integer values associated with each queried key; duplicate rows count once and absent keys return zero. Optimize the implementation for the visible representative workload without changing public behavior. Do not use module-global mutable caches.

Named target implementation module: `perf_energy_p2l/target.py`.
Named shared abstraction: `perf_energy_p2l/shared.py`.
Named observer: `perf_energy_p2l/observer.py`.

Run correctness and the representative benchmark with:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
