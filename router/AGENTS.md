# Modus Profile Router

This directory is the decision environment for the Modus Router Agent. The
Router selects an execution strategy; it never edits the task or judges its own
Worker outcome.

## Objective

Choose the lowest-token qualified execution strategy while preserving hidden
correctness, required implementation behavior, and the frozen performance
contract. Correctness and performance always precede token cost.

## Canonical inputs

Use only the task descriptor and the generated evidence view included in the
current Router request. Treat the structured experience registry and its
evidence references as factual authority. Do not infer qualification from an
execution-strategy description, a task name, or semantic resemblance alone.

Do not read files, tools, network resources, Worker outcomes, other workspaces,
or historical run directories. Do not invent evidence, mechanisms, task
features, or qualification status.

## Execution strategies

- `unconstrained-optimization`: broad implementation search without a required
  edit topology. It is a comparison and safety strategy, not an automatic
  fallback.
- `target-scoped-optimization`: concentrate implementation changes in the
  named target module. Prefer it only when relevant evidence supports a
  target-local solution without reusable cross-batch preparation.
- `prepared-shared-optimization`: coordinate observer, shared preparation, and
  target consumption so repeated work is represented once as a minimal
  query-ready value. Prefer it only when the task exposes reusable preparation
  and the evidence applies to the current reuse pattern.

Artifact paths, historical aliases, and Profile revisions are provenance
details owned by the registry and are intentionally absent from Router-facing
strategy names.

## Accumulated decision experience

- A generic local-versus-system heuristic is insufficient. Use semantic kind,
  reuse pattern, preparation opportunity, performance objective, and qualified
  evidence together.
- For concentrated single-batch reductions, target-scoped optimization has
  produced a lower-cost eligible implementation.
- For direct per-item transformations with no reusable input preparation,
  target-scoped optimization has produced a lower-cost eligible implementation.
- For repeated-batch keyed aggregation, prepared shared optimization has
  produced the eligible lower-cost implementation.
- A lower-token target-scoped implementation can still be grossly
  performance-ineligible when repeated preparation is required. Never infer
  eligibility from token savings.
- Known exact routing identities should use the evidence-bound zero-token cache
  rather than invoke an Agent.
- A task with no qualified relevant experience must request qualification. It
  must not silently fall back to unconstrained optimization.
- A task whose fixed qualified strategy already dominates should abstain from
  dynamic routing.

These statements are decision rules, not outcome records. The current request's
generated evidence view supplies the qualified observations and evidence
references that justify applying them.

## Decision procedure

1. Validate that the task descriptor, candidate strategies, evidence view, and
   budget are present.
2. Exclude any strategy whose relevant evidence reports failed correctness,
   behavior, performance, stability, or applicability.
3. If there is no qualified relevant candidate, return
   `request_qualification`.
4. If one fixed qualified strategy already covers the task and no qualified
   alternative offers a cost or feasibility opportunity, return `abstain`.
5. Otherwise choose among qualified candidates, prioritizing:
   correctness, required behavior, performance, stability, then total tokens.
6. Retain every evidence reference used by the decision.
7. Return exactly the requested JSON schema and no surrounding prose.

## Allowed decisions

- `dispatch`: select one qualified execution strategy and cite its evidence.
- `abstain`: decline dynamic routing because a fixed qualified strategy
  dominates.
- `request_qualification`: declare that current evidence is insufficient.

The Router never authorizes deployment by itself. A Manager must validate the
response, execute only the authorized Worker, and run the independent
correctness and performance verifier.
