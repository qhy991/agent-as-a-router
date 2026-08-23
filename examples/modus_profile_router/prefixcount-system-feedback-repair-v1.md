# PrefixCount system performance feedback repair

The current implementation is hidden-correct but failed its frozen performance
gate: manager-side steady time was `0.008650136718642898` seconds, versus a
maximum of `0.007391881713800785` seconds.

Manager diagnosis: the 25 query batches share one input, but the current local
implementation rebuilds reusable preprocessing inside `target.answer` for each
batch. Repair the existing implementation so reusable preprocessing is
performed once by `observer.prepare_input`, represented through `shared.py`,
and consumed without rebuilding by `target.answer`. Preserve public behavior,
case sensitivity, empty-prefix behavior, and direct raw-input support where it
is part of the visible API. Do not use module-global mutable caches.

Named files:

- `heldout_prefixcount_h02/observer.py`
- `heldout_prefixcount_h02/shared.py`
- `heldout_prefixcount_h02/target.py`

Use only the visible workspace. Do not use web search, a browser, network
access, external documentation, or new dependencies. Do not modify tests,
benchmark code, or metadata.

Run:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
