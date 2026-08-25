# CRC transformation batches: performance task

Task id: `crc-transform`

Return the CRC-8 value for every byte sequence using the fixed polynomial, initial value, and final xor. Optimize the implementation for the visible representative workload without changing public behavior. Do not use module-global mutable caches.

Named target implementation module: `modus_invariant_crc_transform/target.py`.
Named shared abstraction: `modus_invariant_crc_transform/shared.py`.
Named observer: `modus_invariant_crc_transform/observer.py`.

Run correctness and the representative benchmark with:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
