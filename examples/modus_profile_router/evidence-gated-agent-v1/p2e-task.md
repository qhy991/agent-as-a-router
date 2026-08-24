# Modus P2e autonomous evidence-gated Router

Route two stages using only the derived candidate view below. A stage with one
candidate may dispatch that exact tuple or abstain. A stage with `defer` has no
qualified candidate and must not invent a Profile, mechanism, or evidence.
Do not use tools, files, web search, network, or external knowledge.

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
      "resolution": {"decision":"defer","reason":"unqualified_task_state","candidates":[]}
    }
  ]
}
```

Return exactly one `modus-profile-mechanism-route-v1` JSON object with two
ordered routes. Each route has `stage`, `decision`, `profile`, `mechanism_id`,
and `evidence_ref`. Use null payload fields for abstention. Return no surrounding
text.
