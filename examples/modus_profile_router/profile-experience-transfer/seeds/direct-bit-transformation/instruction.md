# Direct 32-bit rotate-mix transform: performance task

Task id: `direct-bit-transformation`

Data is (rotation, xor_mask, multiplier, offset, modulus). Rotate each query's low 32 bits left, xor the mask, multiply, add, and reduce modulo modulus. Optimize the implementation for the visible representative workload without changing public behavior. Do not use module-global mutable caches.

Named target implementation module: `modus_direct_bit_transformation/target.py`.
Named shared abstraction: `modus_direct_bit_transformation/shared.py`.
Named observer: `modus_direct_bit_transformation/observer.py`.

Run correctness and the representative benchmark with:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
