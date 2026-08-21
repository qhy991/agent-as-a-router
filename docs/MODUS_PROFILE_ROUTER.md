# Behavioral Profile routing on ACRouter

This branch adds a constraint-first offline replay for Modus behavioral
Profiles while preserving the original model-routing implementation.

## Why the adapter is separate

The upstream ACRouter pipeline selects backend models under a performance-cost
trade-off and supports verify-then-escalate chains. Modus keeps the model,
provider, harness, tools, task start, and budget fixed; its action is a system
prompt/runtime behavioral Profile. Re-running the same task under a second
Profile would contaminate the action comparison, so the adapter does not use
`ACRouter.run_with_verifier()` and never escalates within a task.

Profile eligibility is lexicographic rather than a soft weighted score:

1. behavior fidelity passes;
2. every repetition passes correctness;
3. the benchmark result is present;
4. median performance is within the frozen tolerance of the fastest action;
5. token usage is complete;
6. only then is the lowest median total-token action selected.

An equivalence band prevents tiny token differences from creating an unstable
Oracle label. The fixed action ordering breaks ties inside that band.

## Reproduce the upstream experiments on Apple Silicon

The following was verified on an Apple Silicon Mac with macOS 15.7.3 and an
isolated micromamba Python 3.11.15 environment. No API key, live model call, or
GPU was used.

```bash
micromamba create -y -n acrouter-modus-py311 \
  python=3.11 pip numpy scipy scikit-learn=1.8 joblib threadpoolctl
micromamba run -n acrouter-modus-py311 python -m pip install -e . --no-deps
micromamba run -n acrouter-modus-py311 python -m unittest discover -s tests

micromamba run -n acrouter-modus-py311 \
  python scripts/run_id.py --output-dir /tmp/acrouter-id
micromamba run -n acrouter-modus-py311 \
  python scripts/run_acrouter_ood176.py --output-dir /tmp/acrouter-ood176
micromamba run -n acrouter-modus-py311 \
  python scripts/run_baselines_ood176.py --output-dir /tmp/acrouter-baselines
```

Observed headline values match the upstream README:

| replay | n | AvgPerf | CumReg | total cost | wall time |
| --- | ---: | ---: | ---: | ---: | ---: |
| ID hierarchical | 2,919 | 50.14 | 202.0 | $22.31 | 0.42 s |
| ACRouter OOD176 | 176 | 73.30 | 15.9 | $86.72 | 0.11 s |
| all OOD176 baselines | 176 | 15 methods | complete | — | 23.05 s |

Wall times are descriptive single local measurements. The replay uses bundled
task-model outcomes; it does not rerun the original backend models.

## Run the Modus Profile replay

```bash
micromamba run -n acrouter-modus-py311 \
  python scripts/run_profile_pipeline.py \
  --config configs/modus_profile_replay.json \
  --cells examples/modus_profile_router/modus-fixed-behavior-pilot-v2-cells.json \
  --output-dir /tmp/modus-profile-replay
```

The expected result is deliberately negative:

```text
best fixed Profile: p000
degree Oracle: p000
timeslice Oracle: p000
Oracle token saving versus best fixed: 0%
routing space observed: false
claim status: no-profile-routing-space-observed
```

On degree, old p100 is also ineligible for a Profile mechanism claim because
only two of three repetitions exhibit its required coordinated topology. On
timeslice, all three actions are eligible, but p000 still has the lowest median
total token count. This replay validates the adapter and the stopping rule; it
does not validate a dynamic Router.

## Required next data

The next Modus experiment must provide a fresh complete matrix over
`neutral/p000/p100-e1-v2`, with the same task start and fixed runtime for every
action. A Router experiment is authorized only if the constrained Oracle uses
at least two Profiles and saves at least 15% total tokens versus the best fixed
Profile without correctness or performance loss. Until that crossover exists,
ACRouter training or live Profile dispatch would have no positive target to
learn.
