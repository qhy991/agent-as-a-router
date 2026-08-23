# Outcome-blind Frequency mechanism routing

There is no current Luna Frequency outcome, Profile label, or verified
Frequency mechanism in this workspace.

Stages:

1. `frequency-p01`: one large batch of 800 exact token-frequency queries over
   one input of 12,000 case-sensitive tokens.
2. `frequency-p02`: 20 batches of 40 exact token-frequency queries sharing the
   same input.

Allowed evidence catalog:

- mechanism `shared-ordered-search-v1`, evidence
  `case:rankcount-prefixcount-n3`: verified for sorted ordered-search and
  prefix-bound queries whose semantics use order comparisons.
- mechanism `shared-prefix-sum-v1`, evidence
  `case:rangesum-binding-2of2`: verified for numeric inclusive-exclusive range
  sums using an additive prefix representation.

Profiles are `neutral`, `p000`, and `p100`. A dispatch is authorized only when
an allowed mechanism directly preserves the Frequency task semantics. Similar
many-batch structure alone is not sufficient evidence. If neither catalog
mechanism applies exactly, abstain for that stage.
