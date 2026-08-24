# Modus linked TokenFrequency transfer Router

Choose one Worker action for each ordered stage before any P2c Worker outcome.
Correctness and final performance are mandatory; prefer lower total Worker
tokens among feasible routes. Do not use tools, files, web search, or network.

- `stage-L`: starts from the frozen starter and optimizes 480 token-frequency
  queries consumed in one batch; its delivered code becomes Stage S input.
- `stage-S`: continues from the exact Stage L code and optimizes the same tokens
  and queries as 120 four-query batches; the immutable input is reused.

Actions: `neutral` is unconstrained; `p000` changes only target and keeps
preparation inside each call; `e1v2` changes target/shared/observer so observer
prepares one reusable representation consumed by target across batches.

Return exactly one JSON object and no surrounding text:

```json
{"schema":"modus-long-horizon-p2c-router-decision-v1","routes":[{"stage":"stage-L","action":"neutral|p000|e1v2","reason":"short reason"},{"stage":"stage-S","action":"neutral|p000|e1v2","reason":"short reason"}]}
```
