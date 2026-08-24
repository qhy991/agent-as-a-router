# Modus P2e v3 autonomous evidence-gated Router

Route two stages using only this derived Agent-facing candidate view. Do not use
tools, files, web search, network, external knowledge, or invented candidates.

```json
{
  "stages": [
    {"stage":"stage-qualified","descriptor":{"worker_model":"gpt-5.6-luna","semantic_kind":"additive_range_sum","reuse_batches":120,"performance_objective":"latency_subject_to_correctness_then_tokens"},"resolution":{"decision":"dispatch","reason":"single_typed_candidate","action":{"profile":"e1v2","mechanism_id":"shared-prefix-sum-v1","evidence_ref":"qualification:p2b:stage-S"}}},
    {"stage":"stage-unqualified","descriptor":{"worker_model":"gpt-5.6-luna","semantic_kind":"token_frequency","reuse_batches":120,"performance_objective":"latency_subject_to_correctness_then_tokens"},"resolution":{"decision":"abstain","reason":"unqualified_task_state","candidates":[]}}
  ]
}
```

Return exactly one JSON object. Its top-level keys must be exactly `schema` and
`routes`; do not use `type`. Use this exact skeleton while deriving route values
from the candidate view:

```json
{"schema":"modus-profile-mechanism-route-v1","routes":[{"stage":"...","decision":"...","profile":null,"mechanism_id":null,"evidence_ref":null}]}
```

Return both ordered stages. A dispatch fills the exact candidate fields; an
abstention leaves all three payload fields null. Return no surrounding text.
