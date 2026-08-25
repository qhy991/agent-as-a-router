# Distinct-value fourth-power sum by key: performance task

Task id: `repeated-batch-keyed-aggregate`

Return the sum of fourth powers of distinct integer values associated with each queried key; duplicate rows count once and absent keys return zero. Optimize the implementation for the visible representative workload without changing public behavior. Do not use module-global mutable caches.

Named target implementation module: `modus_repeated_batch_keyed_aggregate/target.py`.
Named shared abstraction: `modus_repeated_batch_keyed_aggregate/shared.py`.
Named observer: `modus_repeated_batch_keyed_aggregate/observer.py`.

Run correctness and the representative benchmark with:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
