# Modus P2n three-task Profile Router

Choose one Profile for each task before any P2n Worker outcome. Correctness and
performance are mandatory; among eligible choices prefer lower Worker tokens.
Do not use tools, files, web search, or network.

Profiles:

- `neutral`: unconstrained implementation and information gathering.
- `p000v2`: target-only implementation with bounded access to the named
  benchmark and one workload asymmetry; best suited to concentrated local work.
- `e1v3`: coordinated target/shared/observer implementation whose observer
  prepares one minimal query-ready final aggregate for reused input.

Tasks:

- `keyed-distinct-min`: 300,000 keyed rows, 450 queries in one batch; return the
  minimum value for each key.
- `keyed-distinct-cube-sum`: 300,000 keyed rows reused across 90 five-query
  batches; return the distinct-value cube sum for each key.
- `affine-checksum`: a three-integer affine configuration and 200,000 queries in
  one batch; the starter already directly maps each query with no input scan or
  reusable index.

Return exactly one JSON object and no surrounding text:

```json
{"schema":"modus-performance-p2n-router-decision-v1","routes":[{"task":"keyed-distinct-min","action":"neutral|p000v2|e1v3","reason":"short reason"},{"task":"keyed-distinct-cube-sum","action":"neutral|p000v2|e1v3","reason":"short reason"},{"task":"affine-checksum","action":"neutral|p000v2|e1v3","reason":"short reason"}]}
```
