# Modus P2q three-task Profile Router

Choose one Profile for each task before any P2q Worker outcome. Correctness and
performance are mandatory; among eligible choices prefer lower Worker tokens.
Do not use tools, files, web search, or network.

Profiles:

- `neutral`: unconstrained implementation and information gathering.
- `p000v2`: target-only implementation with bounded access to the named
  benchmark and one workload asymmetry; best suited to concentrated local work.
- `e1v3`: coordinated target/shared/observer implementation whose observer
  prepares one minimal query-ready final aggregate for reused input.

Tasks:

- `keyed-closest-negative`: 300,000 keyed rows, 450 queries in one batch; return
  the greatest negative value for each key and ignore non-negative values.
- `keyed-distinct-quartic-sum`: 300,000 keyed rows reused across 90 five-query
  batches; return the distinct-value fourth-power sum for each key.
- `rotate-mix32`: a five-integer rotation/xor/affine configuration and 200,000
  queries in one batch; the starter directly maps each query with no input scan
  or reusable index.

Return exactly one JSON object and no surrounding text:

```json
{"schema":"modus-performance-p2q-router-decision-v1","routes":[{"task":"keyed-closest-negative","action":"neutral|p000v2|e1v3","reason":"short reason"},{"task":"keyed-distinct-quartic-sum","action":"neutral|p000v2|e1v3","reason":"short reason"},{"task":"rotate-mix32","action":"neutral|p000v2|e1v3","reason":"short reason"}]}
```
