# Interval P01 ordered-search mechanism implementation

Apply the router-eligible `shared-ordered-search-v1` mechanism from
`case:rankcount-prefixcount-n3` to the clean Interval P01 starter. Build one
sorted, overlap-merged interval representation through `observer.prepare_input`
and `shared.py`; answer membership in `target.answer` by binary search without
rebuilding it.

Preserve inclusive endpoints, unsorted and overlapping input intervals, and
public behavior. Do not use module-global mutable caches. Use only the visible
workspace; do not use web search, network, external documentation, or new
dependencies. Do not modify tests, benchmark, or metadata.
