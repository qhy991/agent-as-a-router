# Modus linked Membership cached Router

Choose one Worker action for each ordered stage before any P2d Worker outcome.
Correctness and final performance are mandatory; prefer lower Worker tokens.
Do not use tools, files, web search, or network.

- `stage-L`: optimize 600 membership queries in one batch; its code becomes
  Stage S input.
- `stage-S`: continue from the exact Stage L code and optimize the same data as
  120 five-query batches with an immutable reused input.

Actions: `neutral` is unconstrained; `p000` changes only target; `e1v2` changes
target/shared/observer and prepares one reusable representation in observer.

Return exactly one JSON object and no surrounding text:

```json
{"schema":"modus-long-horizon-p2d-router-decision-v1","routes":[{"stage":"stage-L","action":"neutral|p000|e1v2","reason":"short reason"},{"stage":"stage-S","action":"neutral|p000|e1v2","reason":"short reason"}]}
```
