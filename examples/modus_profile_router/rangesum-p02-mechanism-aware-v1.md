# RangeSum P02 mechanism-bound implementation

Optimize the clean RangeSum P02 starter. Bind the following mechanism evidence
to this Worker: the 20 query batches share one input, so inclusive-exclusive
range sums must use a prefix-sum representation built once by
`observer.prepare_input`, represented through `shared.py`, and consumed by
`target.answer` without rebuilding for each batch.

Preserve endpoint clamping, empty-range zero results, negative values, public
behavior, and direct raw-input support where it is part of the visible API. Do
not use module-global mutable caches.

Named files:

- `perf_rangesum_p02/observer.py`
- `perf_rangesum_p02/shared.py`
- `perf_rangesum_p02/target.py`

Use only the visible workspace. Do not use web search, a browser, network
access, external documentation, or new dependencies. Do not modify tests,
benchmark code, or metadata.

Run:

```bash
python3 -m unittest discover -s tests -v
python3 benchmark.py
```
