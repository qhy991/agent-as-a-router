# Closest-to-zero negative value by key: performance task

Task id: `single-batch-keyed-reduction`

For each queried key, return its greatest associated negative integer; ignore non-negative values and return None when no negative value exists. Optimize the implementation for the visible representative workload without changing public behavior. Do not use module-global mutable caches.

Named target implementation module: `modus_single_batch_keyed_reduction/target.py`.
Named shared abstraction: `modus_single_batch_keyed_reduction/shared.py`.
Named observer: `modus_single_batch_keyed_reduction/observer.py`.

Run correctness and the representative benchmark with:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
