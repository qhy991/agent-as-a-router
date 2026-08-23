# Outcome-blind Reachability task feature extraction

Allowed `semantic_kind` values:

- `graph_reachability`: directed path-existence queries over one edge set,
  including source-equals-target semantics.
- `unknown`: the definition above does not apply exactly.

Allowed `performance_objective`:

- `latency_subject_to_correctness_then_tokens`

`reuse_batches` is the exact number of query batches sharing one graph input.

Stages in output order:

1. `reachability-p01`: 140 directed reachability queries in one batch over one
   graph.
2. `reachability-p02`: the same 140 directed reachability queries divided into
   70 batches of two, sharing one graph.

Extract features only. There is no current Luna Reachability outcome, Profile,
mechanism, registry, or action label in this workspace.
