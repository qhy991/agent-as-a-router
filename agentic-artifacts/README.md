# Agentic Artifacts

This folder is a compact, agent-readable map of the ACRouter open-source
bundle. It is designed for crawlers, coding agents, and lightweight web readers
that need to decide what to inspect before loading the full repository.

## Suggested Load Order

1. Read `PAPER.md` for the root manifest and claim-to-evidence bindings.
2. Read `manifest.json` for machine-readable paths, commands, and key metrics.
3. Read `logic/claims.md` and `logic/experiments.md` for the main evaluation
   claims.
4. Read `evidence/tables/score_matrix.md` to locate the full checked-in
   matrices and result tables.
5. Use `configs/eval_pipeline.example.json` and `scripts/run_pipeline.py` when
   adding new models or benchmark tasks.
6. Use `examples/inference_demo.py` to see how ACRouter plugs into an inference
   workflow.
7. Run the commands in the repository `README.md` if executable verification is
   needed.
8. Read `modus-profile-router-mac-replay.json` and
   `../docs/MODUS_PROFILE_ROUTER.md` for the optional same-model behavioral
   Profile action adapter and its Apple Silicon offline replay.
9. Read `modus-swe-mac-readiness-v1.json` and
   `../docs/MODUS_SWE_MAC_READINESS.md` for the model-free OOD176 task
   materialization and baseline/gold verifier gate.
10. Read `modus-swe-profile-cost-canary-v1.json` for the first prompt-only
    neutral/p000 trajectory and token comparison on a reconstructed SWE task.
11. Read `modus-swe-dsh-gate-canary-v1.json` for the excluded fixed-Worker
    apparatus/provider failure and its no-redispatch evidence.
12. Read `modus-codex-luna-max-e-axis-v1.json` for the local Luna Max
    task-by-Profile cost/performance crossover and cross-model boundary.
13. Read `modus-codex-luna-max-membership-e-axis-v1.json` for the negative
    prospective transfer test on a second algorithm family.
14. Read `modus-codex-luna-max-categorysum-e-axis-v1.json` for the
    Profile-agnostic prospective routing-space test on a third family.
15. Read `modus-codex-luna-max-anagram-e-axis-v1.json` for the preliminary
    fourth-family action crossover and failed economic gate.
16. Read `modus-codex-luna-max-rangemin-e-axis-v1.json` for the fifth-family
    cost-versus-performance tradeoff and replicated no-routing result.
17. Read `modus-codex-luna-max-prefixcount-e-axis-v1.json` for the sixth-family
    performance-feasibility action crossover.
18. Read `modus-codex-luna-max-six-family-summary-v1.json` for the aggregate
    selective-routing and abstention conclusion.
19. Read `modus-codex-luna-max-stage-router-shadow-v1.json` for the task-only
    versus evidence-bound twelve-stage Agent Router comparison.
20. Read `modus-codex-luna-max-router-worker-e2e-v1.json` for the actual
    twelve-stage Router-plus-Worker integration failure and cost accounting.
21. Read `modus-codex-luna-max-e2e-feedback-repair-v1.json` for the targeted
    feedback closure, stage-specific p100 repair choice, and failed cost gate.
22. Read `modus-codex-luna-max-mechanism-aware-one-shot-v1.json` for the
    proactive p100 mechanism path and 60.7% two-stage cost reduction.
23. Read `modus-codex-luna-max-mechanism-aware-replication-v1.json` for the
    3/3 reliability and 64.2% median cost result on both known mechanisms.
24. Read `modus-codex-luna-max-rangesum-heldout-v1.json` for the negative
    outcome-blind Profile-action analogy test on a seventh family.
25. Read `modus-codex-luna-max-rangesum-mechanism-binding-v1.json` for the
    post-outcome proof that p100 succeeds when the analogous mechanism is bound.
26. Read `modus-codex-luna-max-frequency-heldout-v1.json` for the positive
    outcome-blind conservative-abstention result under a bounded catalog.
27. Read `modus-codex-luna-max-nearest-heldout-v1.json` for the partial
    outcome-blind ordered-search dispatch and missing amortization predicate.
28. Read `modus-codex-luna-max-nearest-applicability-router-v1.json` for the
    3/3 post-outcome stage-selective predicate contract result.
29. Read `modus-codex-luna-max-batched-predicate-router-v1.json` for the
    four-stage 56.2% Router-call amortization result.
30. Read `modus-codex-luna-max-lookup-interval-heldout-v1.json` for the
    negative mixed held-out registry matching result and eligibility rollback.
31. Read `modus-codex-luna-max-task-feature-extraction-v1.json` for the 3/3
    closed feature parser and safe typed-matcher replay.
32. Read `modus-codex-luna-max-reachability-feature-heldout-v1.json` for new-
    family parsing and the no-candidate neutral-fallback cost failure.
33. Read `modus-codex-luna-max-reachability-qualification-economics-v1.json`
    for full-versus-staged evidence cost and deployment break-even.
34. Read `modus-codex-luna-max-reachability-deployment-simulation-v1.json` for
    the tested 1–20 deployment decision and net-token curves.
35. Read `modus-codex-luna-max-long-horizon-p2h-invalid-v1.json` for the
    prospective scratch-qualification run that was invalidated by an
    uncontracted verifier tag; its large token/performance crossover is
    exploratory only and no second pair is authorized.
36. Read `modus-experiment-scorecard-v1.json` for the generated P1e–P2h
    comparison under one correctness, performance, cost, acquisition, and
    eight-deployment economic vocabulary. Regenerate it with
    `scripts/build_modus_experiment_scorecard.py`.

## Scope

These artifacts are not a second copy of the full dataset. They are an index
and compact evidence snapshot over the canonical repository files:

- `data/` contains the compact matrices, labels, task metadata, and verifier
  cache.
- `data/coderouterbench/` contains the canonical public task x model result
  tables for CodeRouterBench.
- `outputs/` contains checked-in reference outputs and baseline tables.
- `scripts/` contains the reproducible entrypoints.
- `configs/` and `examples/` contain the custom pipeline and inference demos.
- `tests/` contains bundle-integrity and sandbox-verifier tests.

No live model service credentials are needed for the default reproduction.
