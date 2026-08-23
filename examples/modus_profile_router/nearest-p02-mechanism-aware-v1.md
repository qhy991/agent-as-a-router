# Nearest P02 shared ordered-search implementation

Optimize the clean Nearest P02 starter with the verified
`shared-ordered-search-v1` mechanism from
`case:rankcount-prefixcount-n3`. The 20 query batches share one input. Build
one sorted representation through `observer.prepare_input` and `shared.py`;
use binary search in `target.answer` without rebuilding the representation.

Preserve nearest-distance semantics, smaller-value tie breaking, empty-input
`None`, and direct raw-input support where it is part of the visible API. Do
not use module-global mutable caches.

Named files:

- `perf_nearest_p02/observer.py`
- `perf_nearest_p02/shared.py`
- `perf_nearest_p02/target.py`

Use only the visible workspace. Do not use web search, a browser, network
access, external documentation, or new dependencies. Do not modify tests,
benchmark code, or metadata. Run the public tests and benchmark.
