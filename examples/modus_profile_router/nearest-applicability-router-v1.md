# Nearest mechanism routing with applicability predicates

This is a post-outcome Router contract test. Apply the catalog predicates
exactly; do not infer a new mechanism.

Allowed evidence catalog:

- `shared-ordered-search-v1`, evidence
  `case:rankcount-prefixcount-n3`, verified profile `p100`:
  - semantic predicate: queries require ordered search over one reusable sorted
    input representation;
  - amortization predicate: `minimum_reuse_batches = 2`;
  - dispatch only when both predicates hold.
- `shared-prefix-sum-v1`, evidence `case:rangesum-binding-2of2`, verified
  profile `p100`:
  - semantic predicate: additive inclusive-exclusive range sums;
  - amortization predicate: `minimum_reuse_batches = 2`.

Stages:

1. `nearest-p01`: nearest numeric queries with tie-to-smaller semantics, one
   query batch over one input.
2. `nearest-p02`: the same semantics, 20 query batches sharing one input.

If no catalog entry passes every semantic and amortization predicate, abstain.
Otherwise dispatch its verified Profile, mechanism ID, and evidence reference.
