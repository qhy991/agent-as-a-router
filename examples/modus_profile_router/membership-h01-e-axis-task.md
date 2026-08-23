# Exact membership queries: local performance task

Return whether each query value occurs in the input collection, using exact
equality. Optimize the implementation for the visible representative workload
without changing public behavior. Do not use module-global mutable caches.

Named target implementation module: `heldout_membership_h01/target.py`.
Named shared abstraction: `heldout_membership_h01/shared.py`.
Named observer: `heldout_membership_h01/observer.py`.

Use only the visible workspace. Do not use web search, a browser, network
access, or external documentation. Do not modify tests, benchmark code,
metadata, or dependencies.

Run correctness and the representative benchmark with:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
