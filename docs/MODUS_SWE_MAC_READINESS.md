# Modus SWE task readiness on Apple Silicon

Six tasks were selected from the Agent-as-a-Router OOD176 `old112` split and
reconstructed from official SWE-bench Verified metadata. The selection
balanced three local and three system hypotheses across the two repositories
present in Old112: Django and Astropy. No model was called.

Every source archive was bound to its base commit, the official test patch was
applied to a baseline verifier workspace, and the official solution patch was
applied to a separate gold verifier workspace. Five tasks passed the local
readiness gate: baseline plus test patch fails, while gold plus test patch
passes.

| task | stratum | baseline | gold | Mac-native status |
| --- | --- | --- | --- | --- |
| astropy__astropy-13033 | local | 1 failed | 1 passed | ready |
| astropy__astropy-14309 | local | 1 failed | 1 passed | ready |
| django__django-10999 | local | failed | passed | ready |
| django__django-11087 | system | failed | passed | ready |
| django__django-11333 | system | failed | passed | ready |
| astropy__astropy-13398 | system | 4 failed | 3 passed, 1 failed | blocked |

The blocked Astropy coordinate task still fails one gold test under the
official pinned Python packages in a native macOS arm64 build. Since Docker is
not installed on this Mac, the Linux SWE-bench environment cannot be used to
resolve that difference. The task remains excluded instead of being weakened
to a three-test verifier.

## Environment boundary

- Django used Python 3.8.20 with pytz, sqlparse, and asgiref.
- Astropy used Python 3.9.23 and the official SWE-bench pins, including NumPy
  1.25.2, pyerfa 2.0.0.3, pytest 7.4.0, and setuptools 68.0.0.
- Old Astropy C extensions required
  `CFLAGS=-Wno-error=incompatible-function-pointer-types` with the current
  Apple Clang toolchain.
- All tests were local and model-free. The result is apparatus readiness, not
  Profile outcome evidence or official SWE-bench score equivalence.

Machine-readable commits, archive hashes, metadata hashes, and baseline/gold
log hashes are in
[`agentic-artifacts/modus-swe-mac-readiness-v1.json`](../agentic-artifacts/modus-swe-mac-readiness-v1.json).

## Profile consequence

The existing p100-e1-v2 Profile cannot be fairly applied to these tasks. It
requires exactly three named implementation modules with target, shared
abstraction, and observer responsibilities. That wording was created for the
categorysum topology-control sentinel and its precondition is absent from five
of these tasks; four official gold patches touch one implementation module and
one touches two.

The immediate valid cost-generalization experiment is:

```text
five ready tasks × neutral/p000 × two independent repetitions
= 20 fixed Worker cells
```

Each visible task contract must name one target implementation module without
revealing the official solution. This can test whether p000 continues to alter
investigation depth and token cost beyond the two old Modus tasks. It cannot
test a local-versus-system Profile crossover. A separately frozen generic
multi-module Profile is required before system routing can be evaluated.

## First prompt-only cost canary

One neutral-versus-p000 repetition was run on `django__django-10999` with Pi
0.84.2, deepseek-v4-flash/high, and Infini-AI. Both arms used independent base
workspaces, saw the same Profile-blind task, named target module, and visible
nine-test family, and were evaluated afterward with the same hidden test patch.

| arm | visible tests | hidden verifier | first edit message | read/bash/edit | new | cache-read | total |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: |
| neutral | 9 passed | 4 subtests failed | 5 | 5/3/1 | 41,788 | 113,664 | 155,452 |
| p000 | 9 passed | 4 subtests failed | 12 | 5/13/1 | 80,418 | 384,000 | 464,418 |

The p000 arm used 2.99× the observed total tokens, not fewer. It also edited
later and evaluated more often, so the prompt-only Profile did not realize its
intended bounded-investigation behavior. Since both arms are hidden-incorrect,
there is no eligible cost winner and the result must not become an Oracle
label. It is evidence that Profile treatment can alter trajectory and cost,
but not evidence that p000 is cost-effective on this task.

This canary deliberately omits the DSH runtime information gate used by prior
Modus fixed-Worker experiments, so it is a different treatment bundle. The
machine-readable record and all raw-log/session hashes are in
[`agentic-artifacts/modus-swe-profile-cost-canary-v1.json`](../agentic-artifacts/modus-swe-profile-cost-canary-v1.json).

## DSH runtime-gate follow-up

A clean pinned DSH/plugin follow-up attempted to restore the fixed Worker gate
on the same task. It did not produce a valid pair:

- neutral consumed 33,088 complete tokens, performed three information
  attempts, made no edit, and ended `max-tokens`;
- p000 received provider `429 QUOTA` before a finalized assistant response,
  made no edit, and has incomplete usage; its numeric zero fields are not zero
  cost;
- both workspaces remained at the seed and no cell was redispatched;
- the request catalog still exposed `ask_user_question` and `web_search`, so
  the intended unattended fixed-Worker confinement was not established in this
  exact composition;
- the pinned DSH lockfile was stale, forcing an unpinned dependency resolution.

The run is therefore an apparatus/provider failure, not evidence that the DSH
gate succeeds or fails. It is excluded from the Profile pipeline and Oracle.
See
[`agentic-artifacts/modus-swe-dsh-gate-canary-v1.json`](../agentic-artifacts/modus-swe-dsh-gate-canary-v1.json).

### Apparatus repair

The local plugin repair at `15fb98d2c98767dfdba748d6e79aa2b11ec2aa6e`
adds `web_search` to the fixed-Worker deny SSOT. On the pinned clean DSH
checkout, the real ToolRuntime test now proves both model-catalog exclusion and
pre-body execution denial for `ask_user_question` and `web_search`. The full
plugin checks pass: 35 Node tests, 33 Python tests, and 17 real DSH compatibility
tests.

Before a future model request, run the repository preflight:

```bash
python3 scripts/check_modus_dsh_runtime.py \
  --dsh-root /absolute/path/to/deepseek-harness \
  --plugin-root /absolute/path/to/dsh-personal-plugins \
  --expected-plugin-commit <full-plugin-commit> \
  --report /absolute/path/to/run/preflight.json
```

It fails closed unless both repositories are clean and pinned, the plugin
declares the auxiliary-tool-confinement contract, the DSH lockfile passes a
frozen offline check, and the real DSH compatibility suite passes. The repair
preflight made zero model requests and passed. This closes the known apparatus
defects but does not repair or reinterpret the provider `429`; a new paired
Profile run remains pending a representative provider preflight.

See
[`agentic-artifacts/modus-swe-dsh-preflight-repair-v1.json`](../agentic-artifacts/modus-swe-dsh-preflight-repair-v1.json).

### Repaired paired canaries

Two new neutral/p000 development pairs were run only after the repaired
model-free preflight passed and a two-token provider probe returned HTTP 200.
Both used fresh workspaces, the same task seed, Profile-blind host verifiers,
complete finalized usage, and no redispatch.

At the original `4096` request cap, both arms made three information attempts,
never edited, ended `max-tokens`, passed the nine visible tests, and failed five
hidden cases. p000 used 26,382 total tokens versus neutral's 25,953, a 1.65%
increase. This is a valid dual-failure development pair, not a cost winner.

A separately frozen apparatus calibration raised the common request cap to
`16384` after observing that both prior final responses had exhausted exactly
4096 reasoning tokens. It was not pooled with the original pair as a
pre-registered repetition. The calibration produced a clear manipulation
effect:

| Arm | Terminal | Typed edits | Hidden failures | New tokens | Cache-read tokens | Total tokens |
|---|---|---:|---:|---:|---:|---:|
| neutral | max-tokens | 0 | 5 | 74,529 | 214,528 | 289,057 |
| p000 | completed | 4 | 4 | 148,005 | 1,089,536 | 1,237,541 |

The actual p000 request catalog initially matched neutral. After three
pre-edit information attempts, the runtime removed `bash`, `glob`, `grep`,
`read`, and `read_image`; the first typed edit then occurred at step 6 and the
catalog was restored. Neutral had no such transition and never edited. Thus
the Profile plus qualified behavior gate changed the Worker trajectory in the
intended direction. It did not produce an accepted solution: p000 fixed only
one of five hidden failures and cost 4.28 times neutral's total tokens. Neither
arm is quality-eligible, so no cost-efficiency or Profile-preference winner is
declared.

The calibration also found a task-runtime defect. Isolating `HOME` hid the
prebuilt `acrouter-swe-django30-py38` environment from micromamba. Neutral
created a replacement environment inside its cell home; p000 installed missing
packages inside its own cell home. No user environment was modified, but these
different recovery paths confound benchmark cost. A model-free check proved
that setting the existing `MAMBA_ROOT_PREFIX` while retaining an isolated HOME
makes the declared visible command pass. Future outcome cells must freeze that
binding and disable package installation before dispatch.

The redacted record is
[`agentic-artifacts/modus-swe-dsh-repaired-paired-canary-v2-v3.json`](../agentic-artifacts/modus-swe-dsh-repaired-paired-canary-v2-v3.json).

### Frozen task-runtime preflight

`scripts/check_modus_task_runtime.py` closes the isolated-HOME environment gap
before another model request. It requires the declared existing micromamba
environment, runs the task's Python acceptance command with `HOME` isolated and
`MAMBA_ROOT_PREFIX` bound, disables index-backed pip installation, requires pip
to be inside a virtual environment, and disables bytecode writes. The pass or
failure is written before dispatch and always reports zero model requests.

The same environment mapping must be injected into the DSH Worker process; a
host-only passing probe is not sufficient. A missing environment or failing
task command stops the cell before the prompt. This is development apparatus
qualification, not outcome evidence.

### First fixed-only T-axis attempt

The current M1 `p010` (`E0/T1/A0`, SHA-256 `8b0e10fb...`) was added as the
explicit fixed-only `t1-v1` candidate. It is mechanically identical to p000 in
the envelope, E0, and A0 segments and differs only by T0 to T1. It is absent
from the Router action space. The real DSH test proves that p010 retains broad
pre-edit information access after a fourth attempt while keeping the same
auxiliary-tool confinement; p000 still activates its three-attempt T0 lock.

A one-task p010/p000 development pair was frozen after both fresh workspaces
passed the repaired task-runtime preflight with zero model requests. The first
preflight correctly failed because workspace `PYTHONPATH` was missing; a
before-dispatch amendment bound it in both the host probe and Worker process,
after which both arms passed the nine visible tests. No treatment, budget,
schedule, or verifier field changed.

The scheduled first p010 cell completed 15 finalized assistant steps, made its
first typed edit at step 8, ran the declared environment directly, and made no
environment-creation or package-install call. It then received provider `429
QUOTA` during the sixteenth proposed step. Its finalized usage fold is
incomplete and the numeric counters are only lower bounds, never cost. The
partial workspace passes 9/9 visible tests but still fails four hidden cases,
fixing only the negative-zero subcase. The frozen provider-failure rule stopped
the pair, so p000 was not started and no T-axis comparison exists.

See
[`agentic-artifacts/modus-swe-t-axis-development-v1.json`](../agentic-artifacts/modus-swe-t-axis-development-v1.json).

A new pair was later frozen after a fresh provider probe returned HTTP 200,
with the order reversed to p000 then p010. p000 completed its usage ledger but
ended `max-tokens` after three information attempts and no edit: 38,674 total
tokens, 9/9 visible tests, and five hidden failures. p010 made five information
attempts and no edit, then received provider 429 during its sixth proposed
step. Its 85,972 finalized tokens are an incomplete lower bound; it also has
five hidden failures. Thus the expected early T1 manipulation direction
(continued investigation beyond the T0 boundary) appeared, but correctness
did not improve and the provider failure still prevents a valid paired cost or
outcome comparison. See
[`agentic-artifacts/modus-swe-t-axis-development-v2.json`](../agentic-artifacts/modus-swe-t-axis-development-v2.json).

### A-axis visible-feedback task

`django__django-11087` is selected for the first p000/p001 development matrix.
Its official SWE-bench test patch is promoted into the visible workspace before
dispatch, so the seed fails `test_only_referenced_fields_selected` and the gold
implementation passes it on the existing Mac-native environment. This makes
post-edit feedback informative, unlike the duration task whose visible tests
did not expose the hidden semantic error. The promotion changes the task from
an official hidden SWE-bench score into a visible-feedback mechanism probe.

The frozen task contract is
[`configs/modus_swe_a_axis_v1.json`](../configs/modus_swe_a_axis_v1.json). It
plans two counterbalanced repetitions of p000/p001 but remains
`run_authorized=false` until a stable provider window is available.

### Codex-Spark A-axis result

The visible-feedback task was replicated with the local
`gpt-5.3-codex-spark` Codex CLI route at high reasoning. This is a prompt-only
Codex harness, not DSH: canonical p000/p001 text was prepended to the task and
no DSH behavior gate was present. Two apparatus pilots were excluded before
the final matrix: parallel micromamba lock contention in v1 and one unpinned
Web Search call in v2. The final v3 used the frozen environment Python directly,
forbade external information, and produced four complete, custody-clean,
web-free cells.

Both profiles were 2/2 correct. Both had a median of one focused verifier after
the first edit, so A1 did not produce its expected feedback-frequency
signature. p001 used 1.46 times p000 median total tokens and 1.04 times median
uncached-input-plus-output tokens. This is a clean task-level negative result:
no manipulation, quality, or cost advantage for p001. The task branch stops;
p001 remains unqualified. See
[`agentic-artifacts/modus-codex-spark-a-axis-v1.json`](../agentic-artifacts/modus-codex-spark-a-axis-v1.json).

### Codex-Spark T-axis task interaction

A clean prompt-only Spark matrix compared p000/p010 on one simple Astropy FITS
repair and one relation-heavy Django deletion repair, two repetitions each.
Eight cells were admitted in two four-cell waves after a successful Spark
probe. All eight had complete usage, zero Web Search, one allowed implementation
file, and a passing independent host verifier.

The manipulation succeeded: p010 used 11.5 versus p000's 3.0 median pre-edit
commands on the simple task, and 20.5 versus 10.5 on the complex task. The
outcome did not improve: every profile was 2/2 correct on both tasks. p010 used
2.10 times p000 median total tokens on the simple task and 2.21 times on the
complex task. The pre-edit command effect differed by only 1.5 commands between
task types, so broader investigation was not selectively useful on the complex
task. This supports controllable Profile behavior but not T1 suitability or
cost efficiency; the T branch stops for this screen. See
[`agentic-artifacts/modus-codex-spark-t-axis-v1.json`](../agentic-artifacts/modus-codex-spark-t-axis-v1.json).
