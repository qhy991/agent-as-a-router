# Modus Agent-as-Router decision

Choose one Worker action for each task before any Worker outcome is available.
Correctness and performance feasibility are mandatory; among feasible actions,
prefer lower expected Worker token use. Do not use web search, network, files,
tools, or external documentation.

The tasks share one immutable graph input and differ only in reuse:

- `connectivity-y01-perf-p1f`: 240 queries consumed in one batch.
- `connectivity-y02-perf-p1f`: the same query count consumed as 120 two-query batches.

Available actions:

- `neutral`: ordinary coding policy; no topology constraint.
- `p000`: bounded local E0/T0/A0 policy; exactly the named target module may
  change, so any graph preparation occurs inside each target call.
- `e1v2`: mechanism-aware E1/T0/A0 candidate; exactly target, shared, and
  observer change, observer prepares one reusable component index through
  shared, and target consumes that prepared representation across batches.

Return exactly one JSON object and no Markdown or surrounding text:

```json
{"schema":"modus-connectivity-p1f-router-decision-v1","routes":[{"task_id":"connectivity-y01-perf-p1f","action":"neutral|p000|e1v2","reason":"short reason"},{"task_id":"connectivity-y02-perf-p1f","action":"neutral|p000|e1v2","reason":"short reason"}]}
```
