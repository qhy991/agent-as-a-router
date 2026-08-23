# Repeated range minimum queries: system performance task

Return the minimum for each clamped inclusive-exclusive range, or `None` when
the clamped range is empty. Optimize the implementation for the visible
representative workload without changing public behavior. Do not use
module-global mutable caches.

Named target implementation module: `heldout_rangemin_h02/target.py`.
Named shared abstraction: `heldout_rangemin_h02/shared.py`.
Named observer: `heldout_rangemin_h02/observer.py`.

Use only the visible workspace. Do not use web search, a browser, network
access, or external documentation. Do not modify tests, benchmark code,
metadata, or dependencies.

Run correctness and the representative benchmark with:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
