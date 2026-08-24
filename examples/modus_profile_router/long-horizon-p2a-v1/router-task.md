# Modus linked-workflow Agent Router

Choose one Worker action for each ordered stage before any Worker outcome is
available. Correctness and final performance feasibility are mandatory; among
feasible routes, prefer lower total Worker tokens. Do not use tools, files,
web search, network, or external documentation.

The stages operate on one evolving workspace:

- `stage-L`: starts from the frozen starter and optimizes 300 Connectivity
  queries consumed in one batch. Its delivered code becomes Stage S input.
- `stage-S`: continues from the exact Stage L code and optimizes the same graph
  and queries consumed as 150 two-query batches; the immutable input is reused.

Available actions:

- `neutral`: ordinary coding policy with no topology constraint.
- `p000`: E0/T0/A0; only the named target may change, so preparation remains
  local to each target call.
- `e1v2`: mechanism-aware E1/T0/A0; target, shared, and observer change;
  observer prepares one reusable representation through shared, and target
  consumes it across batches.

Return exactly one JSON object with no Markdown or surrounding text:

```json
{"schema":"modus-long-horizon-p2a-router-decision-v1","routes":[{"stage":"stage-L","action":"neutral|p000|e1v2","reason":"short reason"},{"stage":"stage-S","action":"neutral|p000|e1v2","reason":"short reason"}]}
```
