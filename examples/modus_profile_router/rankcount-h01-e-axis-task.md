# Rank count queries: local performance task

For each numeric query, return the number of stored values less than or equal
to it; duplicates count separately. Optimize the implementation for the visible
representative workload without changing public behavior. Do not use
module-global mutable caches.

Named target implementation module: `heldout_rankcount_h01/target.py`.
Named shared abstraction: `heldout_rankcount_h01/shared.py`.
Named observer: `heldout_rankcount_h01/observer.py`.

Use only the visible workspace. Do not use web search, a browser, network
access, or external documentation. Do not modify tests, benchmark code,
metadata, or dependencies.

Run correctness and the representative benchmark with:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
