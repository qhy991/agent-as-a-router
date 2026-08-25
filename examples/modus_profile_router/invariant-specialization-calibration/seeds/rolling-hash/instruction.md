# Rolling hash batches: performance task

Task id: `rolling-hash`

Return the polynomial rolling hash of every byte sequence using the fixed base, salt, and modulus. Optimize the implementation for the visible representative workload without changing public behavior. Do not use module-global mutable caches.

Named target implementation module: `modus_invariant_rolling_hash/target.py`.
Named shared abstraction: `modus_invariant_rolling_hash/shared.py`.
Named observer: `modus_invariant_rolling_hash/observer.py`.

Run correctness and the representative benchmark with:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
