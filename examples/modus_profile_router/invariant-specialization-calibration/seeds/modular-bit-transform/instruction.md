# Modular bit transformation: performance task

Task id: `modular-bit-transform`

For every integer query, rotate its low 32 bits, xor a fixed mask, apply a fixed affine transform, and reduce modulo the configured modulus. Optimize the implementation for the visible representative workload without changing public behavior. Do not use module-global mutable caches.

Named target implementation module: `modus_invariant_modular_bit_transform/target.py`.
Named shared abstraction: `modus_invariant_modular_bit_transform/shared.py`.
Named observer: `modus_invariant_modular_bit_transform/observer.py`.

Run correctness and the representative benchmark with:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
