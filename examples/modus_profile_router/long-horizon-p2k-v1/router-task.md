# Modus P2k evidence-bound long-horizon Router

Propose one Worker action for each ordered stage of a previously unseen
`keyed_distinct_sum` task before any P2k Worker outcome. The response can only
authorize a qualification pair; deployment still requires the pair to pass.

- `stage-L`: optimize 450 queries in one batch; the exact delivered code becomes
  Stage S input.
- `stage-S`: continue from that code and optimize the same immutable 300,000-row
  input for 90 five-query batches.

Actions:

- `neutral`: no Modus Profile constraints.
- `p000`: target-only, bounded context without the representative benchmark;
  it recently failed the Stage L performance gate despite low token cost.
- `p000v2`: target-only with bounded access to the directly named benchmark and
  one workload asymmetry; P2j authorized it for this P2k generalization trial.
- `e1v2`: target/shared/observer coordinated preparation; prior linked evidence
  qualifies it for immutable-input reuse across many target calls.

Correctness and final performance are mandatory; among eligible routes prefer
lower Worker tokens. Do not use tools, files, web search, or network.

Return exactly one JSON object and no surrounding text:

```json
{"schema":"modus-long-horizon-p2k-router-decision-v1","routes":[{"stage":"stage-L","action":"neutral|p000|p000v2|e1v2","reason":"short reason"},{"stage":"stage-S","action":"neutral|p000|p000v2|e1v2","reason":"short reason"}]}
```
