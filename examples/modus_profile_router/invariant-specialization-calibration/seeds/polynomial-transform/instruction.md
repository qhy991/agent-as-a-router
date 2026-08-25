# Fixed polynomial transformation: performance task

Task id: `polynomial-transform`

Evaluate the configured polynomial at every integer query and reduce every Horner step modulo the fixed modulus. Optimize the implementation for the visible representative workload without changing public behavior. Do not use module-global mutable caches.

Named target implementation module: `modus_invariant_polynomial_transform/target.py`.
Named shared abstraction: `modus_invariant_polynomial_transform/shared.py`.
Named observer: `modus_invariant_polynomial_transform/observer.py`.

Run correctness and the representative benchmark with:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
