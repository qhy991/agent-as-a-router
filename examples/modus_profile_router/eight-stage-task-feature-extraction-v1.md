# Eight-stage closed task feature extraction

Allowed `semantic_kind` values:

- `canonical_key_lookup`: case-folded or canonicalized exact key lookup.
- `interval_membership`: point membership in possibly overlapping intervals.
- `token_frequency`: exact occurrence counts for query tokens.
- `ordered_search`: nearest, rank, prefix-bound, or other queries whose exact
  semantics are directly answered from a reusable sorted scalar representation.
- `unknown`: none of the definitions above applies exactly.

Allowed `performance_objective`:

- `latency_subject_to_correctness_then_tokens`

`reuse_batches` is the exact number of query batches sharing one input.

Stages in output order:

1. `lookup-p01`: canonicalized string-key lookup; one batch.
2. `lookup-p02`: canonicalized string-key lookup; 20 batches.
3. `interval-p01`: inclusive membership in unsorted, overlapping intervals;
   one batch.
4. `interval-p02`: the same interval semantics; 20 batches.
5. `frequency-p01`: exact case-sensitive token occurrence counts; one batch.
6. `frequency-p02`: the same frequency semantics; 20 batches.
7. `nearest-p01`: nearest numeric value with smaller-value tie breaking; one
   batch.
8. `nearest-p02`: the same nearest-value semantics; 20 batches.

Extract features only. No mechanism, Profile, registry, or performance outcome
is provided.
