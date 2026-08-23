# Four-stage known-state mechanism routing

This is a known-state batching test. Apply every catalog predicate exactly.

Catalog:

- `shared-ordered-search-v1`, evidence
  `case:rankcount-prefixcount-n3`, verified profile `p100`:
  - semantics require ordered search over one reusable sorted representation;
  - `minimum_reuse_batches = 2`.
- `shared-prefix-sum-v1`, evidence `case:rangesum-binding-2of2`, verified
  profile `p100`:
  - semantics require additive inclusive-exclusive range sums;
  - `minimum_reuse_batches = 2`.

Stages in response order:

1. `frequency-p01`: exact case-sensitive token counts, one query batch.
2. `frequency-p02`: exact case-sensitive token counts, 20 query batches sharing
   one input.
3. `nearest-p01`: ordered nearest-value queries with smaller-value tie breaking,
   one query batch.
4. `nearest-p02`: the same nearest-value semantics, 20 query batches sharing
   one input.

Dispatch only when semantic and amortization predicates both pass. Otherwise
abstain. Use only allowed Profile, mechanism, and evidence values.
