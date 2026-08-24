# Direct affine modular transform: performance task

Task id: `affine_checksum-p2n`

Data is (multiplier, offset, modulus). Return (query * multiplier + offset) modulo modulus for every integer query. Optimize the implementation for the visible representative workload without changing public behavior. Do not use module-global mutable caches.

Named target implementation module: `perf_affine_checksum_p2n/target.py`.
Named shared abstraction: `perf_affine_checksum_p2n/shared.py`.
Named observer: `perf_affine_checksum_p2n/observer.py`.

Run correctness and the representative benchmark with:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
