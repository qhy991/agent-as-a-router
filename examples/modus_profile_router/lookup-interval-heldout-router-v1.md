# Outcome-blind mixed Lookup and Interval mechanism routing

Use the frozen Luna mechanism registry snapshot. Only
`shared-ordered-search-v1` is Router-eligible:

- evidence `case:rankcount-prefixcount-n3`;
- verified Profile `p100`;
- semantic predicate: ordered queries over one reusable sorted representation
  while preserving exact boundary semantics;
- `minimum_reuse_batches = 2`.

`shared-prefix-sum-v1` is not Router-eligible in this snapshot.

Stages in response order:

1. `lookup-p01`: canonicalized string-key lookup, one query batch.
2. `lookup-p02`: canonicalized string-key lookup, 20 batches sharing one input.
3. `interval-p01`: inclusive interval-membership queries over unsorted,
   overlapping intervals, one query batch.
4. `interval-p02`: the same interval semantics, 20 batches sharing one input.

Dispatch only if the eligible mechanism satisfies both semantic and reuse
predicates. Otherwise abstain. There is no current Luna Lookup or Interval
outcome or exact action label in this workspace.
