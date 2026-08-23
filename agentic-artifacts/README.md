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
