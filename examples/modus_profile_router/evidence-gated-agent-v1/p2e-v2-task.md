# Modus P2e v2 autonomous evidence-gated Router

Route two stages using only this derived Agent-facing candidate view. Do not use
tools, files, web search, network, or external knowledge. Do not invent a
candidate. A stage resolution may contain one exact dispatch action or the
canonical Agent decision `abstain`.

```json
{
  "stages": [
    {
      "stage": "stage-qualified",
      "descriptor": {"worker_model":"gpt-5.6-luna","semantic_kind":"additive_range_sum","reuse_batches":120,"performance_objective":"latency_subject_to_correctness_then_tokens"},
      "resolution": {"decision":"dispatch","reason":"single_typed_candidate","action":{"profile":"e1v2","mechanism_id":"shared-prefix-sum-v1","evidence_ref":"qualification:p2b:stage-S"}}
    },
    {
      "stage": "stage-unqualified",
      "descriptor": {"worker_model":"gpt-5.6-luna","semantic_kind":"token_frequency","reuse_batches":120,"performance_objective":"latency_subject_to_correctness_then_tokens"},
      "resolution": {"decision":"abstain","reason":"unqualified_task_state","candidates":[]}
    }
  ]
}
```

Return exactly one `modus-profile-mechanism-route-v1` JSON object with the two
ordered routes and fields `stage`, `decision`, `profile`, `mechanism_id`, and
`evidence_ref`. Use null payload fields for abstention. Return no surrounding
text.
