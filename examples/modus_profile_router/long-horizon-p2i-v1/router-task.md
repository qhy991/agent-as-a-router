# Modus P2i scratch-qualification Router

Propose one Worker action for each ordered stage of a previously unseen
`keyed_max` task. No P2i Worker outcome or route qualification exists yet. Your
response is only a qualification proposal and cannot authorize deployment until
a separately frozen routed/neutral Worker pair passes every gate.

- `stage-L`: optimize 300 maximum-by-key queries in one batch; the exact
  delivered code becomes Stage S input.
- `stage-S`: continue from that code and optimize the same immutable 180,000-row
  input for 60 five-query batches.

Actions:

- `neutral`: no Modus Profile constraints.
- `p000`: change only the named target implementation.
- `e1v2`: change target, shared abstraction, and observer to prepare one reusable
  representation before the query batches.

Correctness and performance are mandatory. Prefer the action whose permitted
implementation topology best matches each workload stage; token cost is a
secondary objective. Do not use tools, files, web search, or network.

Return exactly one JSON object and no surrounding text:

```json
{"schema":"modus-long-horizon-p2i-router-decision-v1","routes":[{"stage":"stage-L","action":"neutral|p000|e1v2","reason":"short reason"},{"stage":"stage-S","action":"neutral|p000|e1v2","reason":"short reason"}]}
```
