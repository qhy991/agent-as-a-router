# Evidence-gated Modus Router: qualified case

Route two ordered RangeSum stages using only the exact qualified candidates
below. Do not use tools, files, web search, network, or invent evidence.

- Stage L: profile `p000`, mechanism `local-prefix-sum-v1`, evidence
  `qualification:p2b:stage-L`.
- Stage S: profile `e1v2`, mechanism `shared-prefix-sum-v1`, evidence
  `qualification:p2b:stage-S`.

You may abstain, but any dispatch must use the exact candidate for that stage.
Return exactly one JSON object with no surrounding text:

```json
{"schema":"modus-profile-mechanism-route-v1","routes":[{"stage":"stage-L","decision":"dispatch|abstain","profile":"p000 or null","mechanism_id":"local-prefix-sum-v1 or null","evidence_ref":"qualification:p2b:stage-L or null"},{"stage":"stage-S","decision":"dispatch|abstain","profile":"e1v2 or null","mechanism_id":"shared-prefix-sum-v1 or null","evidence_ref":"qualification:p2b:stage-S or null"}]}
```

