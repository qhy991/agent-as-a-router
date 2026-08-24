# Modus P2h scratch-qualification Router

Propose one Worker action for each ordered stage of a previously unseen
`distinct_out_degree` task. No P2h Worker outcome or route qualification exists
yet. Your response is only a qualification proposal: it cannot authorize a
deployment until a routed/neutral Worker pair passes the frozen gates.

- `stage-L`: optimize 100 distinct-out-degree queries in one batch; the exact
  delivered code becomes Stage S input.
- `stage-S`: continue from that code and optimize the same immutable 200,000-edge
  graph for 20 five-query batches.

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
{"schema":"modus-long-horizon-p2h-router-decision-v1","routes":[{"stage":"stage-L","action":"neutral|p000|e1v2","reason":"short reason"},{"stage":"stage-S","action":"neutral|p000|e1v2","reason":"short reason"}]}
```
