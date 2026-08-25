# Direct 32-bit rotate-mix transform: performance task

Task id: `rotate_mix32-p2s`

Data is (rotation, xor_mask, multiplier, offset, modulus). Rotate each query's low 32 bits left, xor the mask, multiply, add, and reduce modulo modulus. Optimize the implementation for the visible representative workload without changing public behavior. Do not use module-global mutable caches.

Named target implementation module: `perf_rotate_mix32_p2s/target.py`.
Named shared abstraction: `perf_rotate_mix32_p2s/shared.py`.
Named observer: `perf_rotate_mix32_p2s/observer.py`.

Run correctness and the representative benchmark with:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
