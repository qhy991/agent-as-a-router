# Direct bit-mix modular transform: performance task

Task id: `direct-bitmix-p2p`

Data is (xor_mask, multiplier, offset, modulus). For every integer query, xor it with the mask, multiply, add the offset, and reduce modulo modulus. Optimize the implementation for the visible representative workload without changing public behavior. Do not use module-global mutable caches.

Named target implementation module: `perf_direct_bitmix_p2p/target.py`.
Named shared abstraction: `perf_direct_bitmix_p2p/shared.py`.
Named observer: `perf_direct_bitmix_p2p/observer.py`.

Run correctness and the representative benchmark with:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
