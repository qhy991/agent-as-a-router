# Outcome-blind Nearest mechanism routing

There is no current Luna Nearest outcome or Profile label in this workspace.

Stages:

1. `nearest-p01`: one large batch of 1,000 nearest-value queries over one input
   of 6,000 numeric values.
2. `nearest-p02`: 20 batches of 50 nearest-value queries sharing the same
   input.

Allowed evidence catalog:

- mechanism `shared-ordered-search-v1`, evidence
  `case:rankcount-prefixcount-n3`: build one sorted representation and answer
  order-dependent queries by binary search. Verified 3/3 on both known system
  tasks with p100.
- mechanism `shared-prefix-sum-v1`, evidence
  `case:rangesum-binding-2of2`: build one additive numeric prefix
  representation for inclusive-exclusive range sums, verified with p100.

Profiles are `neutral`, `p000`, and `p100`. Dispatch only when an allowlisted
mechanism directly preserves nearest-value semantics, including smaller-value
tie breaking and empty input. Otherwise abstain. Do not assume an outcome label
for either stage.
