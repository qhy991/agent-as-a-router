# Modus behavioral Profile replay fixture

`modus-fixed-behavior-pilot-v2-cells.json` is a byte-identical copy of the
curated 18-cell development matrix from
`qhy991/Modus:results/modus30/dsh-fixed-behavior-pilot-v2/cells.json`.

- source SHA-256: `8c6eca781f0fd23c92779d3f83b101a4cbb8dc2f193d20e76dee28c55be948de`
- tasks: degree and timeslice selected old P1c tasks
- actions: neutral, p000, p100
- repetitions: three per task/action
- scientific evidence: false

The fixture tests that the ACRouter action/evaluation structure can be reused
for same-model behavioral Profiles. It intentionally reproduces the negative
result: p000 is both the best fixed action and the Oracle action on both tasks,
so the observed Oracle saving is zero and no routing space is present. It is
not a benchmark of the upstream model router and does not establish Modus
Router benefit.
