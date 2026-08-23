# RankCount system mechanism-aware implementation

Optimize the system workload from its clean starter state. Verified mechanism
evidence: 25 query batches share one input; reusable sorted preprocessing must
be performed once by `observer.prepare_input`, represented through `shared.py`,
and consumed without rebuilding by `target.answer`. Preserve public behavior,
duplicates, inclusive `<=` semantics, and direct raw-input support where it is
part of the visible API. Do not use module-global mutable caches.

Named files:

- `heldout_rankcount_h02/observer.py`
- `heldout_rankcount_h02/shared.py`
- `heldout_rankcount_h02/target.py`

Use only the visible workspace. Do not use web search, a browser, network
access, external documentation, or new dependencies. Do not modify tests,
benchmark code, or metadata.

Run:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
