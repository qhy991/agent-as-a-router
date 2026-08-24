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

### Codex-Spark E-axis topology interaction

The canonical p000/p100 pair was tested on the same rank-count algorithm under
two workloads: one large query batch and twenty-five small batches sharing one
input. All eight cells passed correctness and the manipulation check: p000
changed only `target.py`, while p100 changed `target.py`, `shared.py`, and
`observer.py` exactly.

On the local workload, both actions were effectively equal in steady time
(p000/p100 median ratio 0.964), while p000 used 37.9% fewer median total tokens.
On the system workload, the valid paired repetition made p100 17.63 times
faster while costing 27.1% more total tokens. A second p100 replication had
the same performance, but its paired p000 cell used Web Search and was excluded.
This is the first clean Spark action crossover: choose p000 for local low-cost
work and p100 for shared multi-batch performance. It supports moving to a
Profile-blind shadow Router; it does not yet establish Router net benefit. See
[`agentic-artifacts/modus-codex-spark-e-axis-v1.json`](../agentic-artifacts/modus-codex-spark-e-axis-v1.json).

Before reading the shadow Router outcome, the economic gate is fixed. The
worker-only routed policy costs 459,549 tokens across the two tasks versus
551,883.5 for the best performance-eligible fixed action, p100. Any net saving
allows at most 92,334.5 Router tokens in total. The existing 15% saving gate is
stricter: at most 9,551.975 total, or 4,775.9875 per decision. A correct Agent
Router above that ceiling is not a net-benefit result; for these obvious states,
the zero-token batch-count rule remains the required ablation.

### Codex-Sol Router shadow

The Spark-specific quota blocked an immediate Router run, and `gpt-5.3-codex`
is unavailable through ChatGPT authentication. A separate cross-model shadow
used `gpt-5.6-sol` with the canonical Router v3 system contract. Six independent
responses were execution-valid, custody-clean, schema-valid, and stable: local
selected neutral 3/3; system selected p100 3/3. The system action matches the
observed E-axis crossover. The local action is not yet scoreable because the
current Spark E matrix did not include neutral.

Median Router cost was 52,941 tokens for local and 53,284 for system, 106,225
combined. This exceeds both the 92,334.5 any-saving ceiling and the 9,551.975
frozen 15% saving ceiling. Therefore a correct high-reasoning Agent Router does
not establish net benefit on these obvious states; the zero-token batch-count
rule is the required baseline. See
[`agentic-artifacts/modus-codex-sol-router-shadow-v1.json`](../agentic-artifacts/modus-codex-sol-router-shadow-v1.json).

Matched Sol Worker evidence later invalidated both shadow choices. On the local
workload, neutral and p000 were performance-equivalent but p000 used 41.4% fewer
tokens. On the system workload, neutral found shared preprocessing in two of
three runs and its median was 24.1 times faster than p100; p100 satisfied the
three-module topology in all three runs but never moved preprocessing out of
the per-batch target. Thus the Sol Router scored 0/2 against Sol Worker outcomes.

This is a model-by-Profile interaction: Spark p100 converted coordinated
topology into a 17.63x system speedup, while Sol p100 controlled topology but
not the optimization mechanism. A task-only Router is therefore insufficient;
the routing context must bind Worker model and model-specific Profile response
evidence. See
[`agentic-artifacts/modus-codex-sol-e-axis-v1.json`](../agentic-artifacts/modus-codex-sol-e-axis-v1.json).

### Codex-Luna Max Profile cost-effectiveness replication

A local replication used `gpt-5.6-luna` at `max` reasoning with neutral,
p000, and p100 on the same two rank-count workloads. All 15 cells were
execution-valid, correctness-clean, usage-complete, and free of Web Search.
On the local workload, the actions were performance-equivalent; p000 used
53.3% fewer median total tokens than neutral and 26.5% fewer than p100.

On the system workload, neutral moved shared preprocessing outside the repeated
target call in two of three runs. Its median was 14.7 times faster than p100,
but it used 103.5% more median total tokens. p100 changed all three named
modules in every run but never moved preprocessing outside the per-batch
target. Therefore topology compliance remains a manipulation check, not a
performance mechanism or utility guarantee.

The Luna action crossover is p000 for local low-cost work and neutral for
system performance work. Together with the Spark and Sol results, this rules
out a task-only Profile policy: the minimum Router state is Worker model x task
state x eligible Profile. The next test is a zero-token model-aware lookup
policy on held-out task families; paying an Agent Router is not yet justified.
See
[`agentic-artifacts/modus-codex-luna-max-e-axis-v1.json`](../agentic-artifacts/modus-codex-luna-max-e-axis-v1.json).

### Held-out membership transfer result

The Luna policy was then frozen before outcome as local p000 and system
neutral, and tested on the pre-existing Modus P1b membership family. The
two-repetition neutral/p000/p100 matrix completed 12/12 execution-valid and
correct cells without Web Search or redispatch.

The local prediction passed: p000 remained within the performance threshold
and used 47.6% fewer median total tokens than neutral. The system prediction
failed: all three actions were performance-equivalent near 2.45 ms, while
neutral used 3.20 times p000's median total tokens. p100 changed all three
modules in both runs but never moved set construction outside the repeated
target call.

The observed dynamic minimum, local p000 plus system p100, saved only 1.3%
against fixed p000 and failed the frozen 15% gate. Therefore this family has no
useful Profile routing space, and the rankcount-derived local/system policy did
not transfer. Router state must include algorithm family or an observed
bottleneck mechanism, not only Worker model and batch structure. See
[`agentic-artifacts/modus-codex-luna-max-membership-e-axis-v1.json`](../agentic-artifacts/modus-codex-luna-max-membership-e-axis-v1.json).

### Prospective CategorySum Profile-space result

A third Luna family was frozen without assuming the winning action. Every
correct action within 1.25 times the fastest median remained eligible, and
actions within 5% token cost were treated as tied. The two-wave matrix again
completed 12/12 valid and correct cells without Web Search or redispatch.

All actions were performance-eligible on both task states. Local selected p000,
which used 30.3% fewer median total tokens than neutral. On system, p100 used
4.7% fewer tokens than p000, so the two were a pre-registered practical tie.
p100 changed all three modules in both system runs but never moved aggregation
outside the repeated target call.

Even the exact, non-robust local-p000/system-p100 Oracle saved only 2.5% against
fixed p000, failing the 15% gate. CategorySum therefore has no useful Profile
routing space. Across the three Luna families measured so far, Profile cost
effects repeat, but only rankcount has shown an action crossover; membership
and CategorySum both favor a near-fixed low-cost policy. See
[`agentic-artifacts/modus-codex-luna-max-categorysum-e-axis-v1.json`](../agentic-artifacts/modus-codex-luna-max-categorysum-e-axis-v1.json).

### Prospective Anagram Profile-space result

The same frozen, winner-agnostic scoring contract was applied to a fourth Luna
family. The two waves completed 12/12 valid and correct cells without Web
Search or redispatch. Local selected p000: all actions were performance-
eligible, while p000 used 56.9% fewer median total tokens than neutral.

System selected p100 under the frozen median rule. Its two steady results were
56.9 ms and 8.88 ms, versus p000's stable 59.9 ms median, so p100 was 1.82
times faster at the two-run median and the other actions exceeded the 1.25x
eligibility limit. The fast p100 repetition added per-call signature
memoization; the other p100 repetition did not, so the performance mechanism
is bimodal and occurred only 1/2 times.

The local-p000/system-p100 action crossover is therefore preliminary. It saved
10.2% Worker tokens versus the only fixed performance-eligible action, p100,
and failed the frozen 15% economic gate. Across four Luna families, two show an
action crossover, but only rankcount has useful worker-only routing space. See
[`agentic-artifacts/modus-codex-luna-max-anagram-e-axis-v1.json`](../agentic-artifacts/modus-codex-luna-max-anagram-e-axis-v1.json).

A separately frozen third system repetition then tested the unstable p100 fast
mode. Both p000 and p100 were correct, but p100 measured 57.0 ms and failed the
pre-registered 47.9 ms fast threshold. Across all three repetitions, p100 and
p000 differ by only 5.2% steady time and 1.9% tokens. The initial Anagram
crossover therefore did not independently replicate and is not a Router
action label. After replication, only rankcount has a stable and economically
useful action crossover among the four measured Luna families.

### Prospective RangeMin Profile-space result

RangeMin increased task difficulty and completed 12/12 valid and correct cells
under the same scoring contract. Although p000 used much fewer tokens, its
two-run local and system medians were 6.21 ms and 17.85 ms. Neutral was the only
performance-eligible action on both states, at 3.88 ms local and 3.26 ms
system. Thus the cheapest Profile was not the best constrained action.

The local neutral/p100 ordering reversed between the two original runs, so a
separately frozen third repetition was added. Neutral measured 2.38 ms and p100
7.25 ms; their three-run medians differ by 2.69 times in neutral's favor. The
first-run p100 signal did not replicate. RangeMin therefore has no action
crossover or routing saving, but it supplies direct evidence that Profile cost
and performance must be gated separately. See
[`agentic-artifacts/modus-codex-luna-max-rangemin-e-axis-v1.json`](../agentic-artifacts/modus-codex-luna-max-rangemin-e-axis-v1.json).

### Prospective PrefixCount Profile-space result

PrefixCount completed the six-family Luna matrix with 12/12 valid and correct
cells. Local selected p100: p000 and p100 were both within the performance
limit, while p100 used 12.1% fewer median total tokens. System selected neutral,
which was 12.1 times faster than p100; p000 and p100 were both ineligible.

No fixed Profile was performance-eligible on both states: neutral qualified
only on system, while p000 and p100 qualified only on local. The p100/neutral
route is therefore required for portfolio performance feasibility. Its Worker
cost is 253,412 median tokens, but the 15% saving gate cannot be evaluated
because there is no eligible fixed baseline; no token-saving claim is made.
This is the second stable action crossover and the first case where routing
changes feasibility rather than merely reducing cost. See
[`agentic-artifacts/modus-codex-luna-max-prefixcount-e-axis-v1.json`](../agentic-artifacts/modus-codex-luna-max-prefixcount-e-axis-v1.json).

### Six-family Luna conclusion

The completed matrix contains 79/79 valid, correct, usage-complete cells across
six algorithm families and twelve local/system task states. p000 satisfied its
local topology in 26/26 cells, p100 satisfied coordinated topology in 27/27,
and p000 used fewer median tokens than neutral on all 12 task states. This is
strong diagnostic evidence that Profile changes behavior and cost.

Utility is selective. Rankcount has a stable 25.0% Worker-token saving route;
PrefixCount has a stable route required for performance feasibility because no
fixed Profile passes both states. Membership, CategorySum, Anagram, and
RangeMin have no stable useful crossover. The resulting design must route only
2/6 families and abstain to a fixed qualified Profile on 4/6. A universal
Profile Router is rejected; a selective Router with an explicit abstain action
is supported. See
[`agentic-artifacts/modus-codex-luna-max-six-family-summary-v1.json`](../agentic-artifacts/modus-codex-luna-max-six-family-summary-v1.json).

### Twelve-stage Agent Router shadow

A bounded Luna Max Router planned all twelve family/state stages in one turn.
Three task-only repetitions were execution-valid and perfectly stable, but
they all applied the same generic rule—p000 local and p100 system—and matched
only 4/12 verified actions. Task structure alone is therefore not a sufficient
Router state.

Three evidence-bound repetitions matched all 12/12 actions exactly. Their
median Router cost was 43,703 tokens, or 3.08% of the 1,418,863-token selective
Worker plan. One batched Router plan costs less than Rankcount's 86,060.5
Worker-token saving and leaves 42,357.5 tokens of that saving, but the zero-
token evidence table remains strictly cheaper on known states. The Agent Router
should therefore be reserved for unknown states or batched long-horizon plans;
known states should use deterministic evidence lookup. See
[`agentic-artifacts/modus-codex-luna-max-stage-router-shadow-v1.json`](../agentic-artifacts/modus-codex-luna-max-stage-router-shadow-v1.json).

### Router plus Worker end-to-end pilot

A new evidence-bound Router parent matched all 12/12 frozen stage actions and
cost 63,832 tokens. Its actual response generated one twelve-cell fresh Worker
wave. All Workers were execution-valid and hidden-correct, and all eight
selected non-neutral Profiles passed topology fidelity. Worker cost was
1,411,290 tokens; Router plus Worker cost was 1,475,122, a 4.52% Router
overhead. The Router remained below Rankcount's 86,060.5-token saving budget.

The end-to-end gate nevertheless failed. Sequential manager measurement passed
only 10/12 performance thresholds. Rankcount-system and PrefixCount-system both
selected the correct evidence action, neutral, but produced local slow-path
implementations rather than the historical fast mechanism. A prior concurrent
manager measurement was explicitly excluded because CPU contention invalidated
its performance values.

Thus exact Profile routing, correctness, and topology are insufficient for
end-to-end success. Modus requires a verifier-guided feedback stage after each
Worker, with targeted repair rather than whole-run redispatch. See
[`agentic-artifacts/modus-codex-luna-max-router-worker-e2e-v1.json`](../agentic-artifacts/modus-codex-luna-max-router-worker-e2e-v1.json).

### Targeted feedback repair closure

The two actual slow-path workspaces were cloned into neutral/p100 repair pairs
and received identical manager feedback. All four repairs were correct,
coordinated, and performance-eligible. p100 was the lower-token repair for both
tasks: 108,028 tokens for Rankcount and 120,832 for PrefixCount. Initial system
implementation therefore selected neutral, while the explicit feedback-repair
stage selected p100.

The selected repairs close final correctness and performance to 12/12, but add
228,860 tokens. Router plus Workers plus repairs totals 1,703,982 tokens, and
the repair cost erases Rankcount's remaining saving. Modus has now demonstrated
a working route/execute/verify/repair loop, but not an efficient one. See
[`agentic-artifacts/modus-codex-luna-max-e2e-feedback-repair-v1.json`](../agentic-artifacts/modus-codex-luna-max-e2e-feedback-repair-v1.json).

### Proactive mechanism-aware one-shot result

The verified shared-preprocessing mechanism was then supplied before the first
Worker turn in clean Rankcount-system and PrefixCount-system workspaces, with
p100 as the implementation Profile. Both one-shot cells were correct,
coordinated, and performance-eligible. They cost 90,889 and 116,124 tokens.

Together the one-shot Workers used 207,013 tokens, 60.7% less than the 526,964
tokens consumed by initial implementation plus selected repair. Replacing the
two failed Workers yields a 12/12-correct, 12/12-performance Router-plus-Worker
path costing 1,384,031 tokens, 18.8% below the feedback-closed path. The minimum
Modus action is therefore Profile plus verified mechanism evidence, not Profile
alone. This positive result remains single-run and known-state. See
[`agentic-artifacts/modus-codex-luna-max-mechanism-aware-one-shot-v1.json`](../agentic-artifacts/modus-codex-luna-max-mechanism-aware-one-shot-v1.json).

Two additional fresh-starter repetitions per task then replicated the proactive
path. Rankcount-system and PrefixCount-system each reached 3/3 hidden
correctness, coordinated topology, and performance eligibility. Their n=3
median costs are 90,889 and 97,720 tokens. The combined 188,609-token median is
64.2% below the 526,964-token implementation-plus-repair path, giving a
replicated proactive Router-plus-Worker estimate of 1,365,627 tokens. Known-
state Profile-plus-mechanism dispatch is now reliable within this diagnostic;
unseen mechanism transfer remains untested. See
[`agentic-artifacts/modus-codex-luna-max-mechanism-aware-replication-v1.json`](../agentic-artifacts/modus-codex-luna-max-mechanism-aware-replication-v1.json).

### Held-out RangeSum analogy result

The pre-existing Modus P0 RangeSum pair was frozen before any current Luna
outcome and omitted all action labels from Router workspaces. A complete
neutral/p000/p100, two-task, two-repetition matrix passed 12/12 correctness and
topology. P01 accepts p000 or p100 under the 5% token tie; P02 accepts only
neutral. Its exact dynamic saving versus fixed neutral is 11.5%, below the 15%
gate.

Task-only Router plans were unstable and matched one of two stages in every
repetition. More importantly, the evidence-analogy Router was stable but wrong:
all three plans selected neutral/p100 and matched 0/2 constrained actions. The
zero-token neutral/neutral abstention matched 1/2. Profile-level evidence
analogy therefore did not transfer to held-out RangeSum. Standard p100 changed
topology on P02 but did not produce the shared-prefix fast mechanism, confirming
that the Router action must bind Profile and mechanism evidence. See
[`agentic-artifacts/modus-codex-luna-max-rangesum-heldout-v1.json`](../agentic-artifacts/modus-codex-luna-max-rangesum-heldout-v1.json).

A separately frozen post-outcome diagnostic then bound p100 to the analogous
`shared-prefix-sum-v1` mechanism on two clean RangeSum-P02 starters. Both cells
were correct, coordinated, and performance-eligible. Median cost was 100,636
tokens, 57.9% below neutral, while performance matched neutral and was 5.53
times faster than standard p100. Thus the mechanism itself transferred; the
held-out failure came from transmitting only the Profile label. This does not
change the negative held-out verdict because the exact mechanism prompt was
authored after outcome. See
[`agentic-artifacts/modus-codex-luna-max-rangesum-mechanism-binding-v1.json`](../agentic-artifacts/modus-codex-luna-max-rangesum-mechanism-binding-v1.json).

### Outcome-blind Frequency abstention result

A second unused P0 family tested the new Profile-plus-mechanism contract. The
allowlist contained only ordered-search and prefix-sum mechanisms, neither of
which preserves exact token-frequency semantics. Three independent Luna
Routers therefore abstained on both stages, with no invented mechanism or
evidence reference. Median Router cost was 72,913 tokens.

The complete Worker matrix passed all correctness and topology checks. P01
selects p000 for cost; P02 selects neutral for performance after a third
replication resolved neutral's bimodality. Dynamic p000/neutral saves 12.9%
versus fixed neutral, below the 15% promotion gate. Family-level abstention is
therefore outcome-blind and correct: neutral is performance-safe on both tasks,
and no unsupported mechanism is dispatched. The Agent adds no value over the
zero-token abstention rule and misses a smaller P01 cost opportunity. See
[`agentic-artifacts/modus-codex-luna-max-frequency-heldout-v1.json`](../agentic-artifacts/modus-codex-luna-max-frequency-heldout-v1.json).

### Outcome-blind Nearest positive-dispatch result

Nearest directly matched the allowlisted ordered-search mechanism. Two of three
Routers dispatched p100 plus that mechanism to both stages; one abstained on
both. All responses were schema- and evidence-valid, but the decision was not
stable.

The full standard matrix selects fixed p000 on both stages after a third P02
replication. Mechanism-bound p100 is correct and coordinated 2/2 on each task.
It fails the P01 performance gate because one-batch setup cost is not amortized,
but passes P02 and is 2.93 times faster than standard p000 at 56.8% higher
token cost. Thus semantic mechanism matching alone is insufficient: the Router
must model setup cost, reuse count, and performance objective. Positive
mechanism transfer occurred on the system stage only, so the full held-out
dispatch gate failed. See
[`agentic-artifacts/modus-codex-luna-max-nearest-heldout-v1.json`](../agentic-artifacts/modus-codex-luna-max-nearest-heldout-v1.json).

A post-outcome contract test added the missing applicability predicate:
`shared-ordered-search-v1` requires at least two reuse batches. Three
independent Routers then produced the exact stage-selective plan—abstain on
one-batch P01 and dispatch p100 plus ordered-search on twenty-batch P02. Median
Router cost was 73,827 tokens. This validates predicate execution and decision
stability, but not held-out generalization or cost benefit over a zero-token
predicate table. See
[`agentic-artifacts/modus-codex-luna-max-nearest-applicability-router-v1.json`](../agentic-artifacts/modus-codex-luna-max-nearest-applicability-router-v1.json).

### Four-stage batched Router amortization

Frequency abstention and Nearest applicability routing were combined into one
known-state four-stage plan. Three independent Routers produced the exact plan:
abstain on both Frequency stages and Nearest-P01, then dispatch p100 plus
ordered-search on Nearest-P02. Median Router cost was 64,223 tokens.

Two separate Router calls cost 146,740 median tokens, so batching saved 82,517
tokens or 56.2%, reducing Router overhead from 26.1% to 11.4% of the known
Worker plan. The zero-token predicate table remains cheaper. This validates
longer-plan amortization but not held-out routing. See
[`agentic-artifacts/modus-codex-luna-max-batched-predicate-router-v1.json`](../agentic-artifacts/modus-codex-luna-max-batched-predicate-router-v1.json).

### Mixed outcome-blind Lookup and Interval result

A registry-derived four-stage held-out plan mixed semantics with and without a
plausible ordered-search match. All 31 Worker cells were valid, correct, and
topology-clean. The standard Oracle routes p000 on both Lookup stages and
Interval-P01, then neutral on Interval-P02; it saves 30.1% versus fixed neutral.

The Router failed all three plans. It incorrectly dispatched ordered-search to
Lookup-P02 in 3/3 responses despite incompatible canonical-hash semantics, and
dispatched it to Interval-P02 only 1/3. Mechanism-bound Interval Workers were
correct and coordinated but failed both task-level performance gates. Global
identifier/evidence allowlists therefore do not make natural-language semantic
matching reliable. Outcome-blind mechanism eligibility must be revoked until a
deterministic typed feature matcher filters candidates before Agent reasoning.
See
[`agentic-artifacts/modus-codex-luna-max-lookup-interval-heldout-v1.json`](../agentic-artifacts/modus-codex-luna-max-lookup-interval-heldout-v1.json).

### Closed task-feature extraction result

After removing mechanism choice from the Agent, three Luna extractors classified
eight Lookup, Interval, Frequency, and Nearest stages under a fail-closed
feature schema. All three returned the exact semantic kind, reuse count, stage
order, and performance objective for all eight stages. Feeding those outputs to
the zero-token typed matcher produced no candidate for seven stages and only
ordered-search for Nearest-P02, exactly 3/3.

Median extractor cost was 59,567 tokens, 30.7% below the old unsafe direct
Router but still strictly worse than trusted zero-token metadata. This supports
Agent use as a bounded parser only when authoritative features are unavailable;
mechanism compatibility remains deterministic. See
[`agentic-artifacts/modus-codex-luna-max-task-feature-extraction-v1.json`](../agentic-artifacts/modus-codex-luna-max-task-feature-extraction-v1.json).

### Outcome-blind Reachability feature result

On the unused P0 Reachability family, three Luna extractors returned exact and
stable `graph_reachability` features with reuse counts 1 and 70. The typed
matcher safely produced no mechanism candidates in 3/3 replays. Median parser
cost was 43,452 tokens.

The complete Worker matrix and a third P02 replication selected fixed p000 on
both tasks. p000 remained performance-eligible and used 52.6% fewer tokens than
neutral. Thus feature parsing generalized and candidate filtering was safe, but
resolving zero candidates directly to neutral missed a large Profile cost
opportunity. Zero candidate must mean unqualified/defer and trigger bounded
offline Profile qualification, not assert that neutral is optimal. See
[`agentic-artifacts/modus-codex-luna-max-reachability-feature-heldout-v1.json`](../agentic-artifacts/modus-codex-luna-max-reachability-feature-heldout-v1.json).

### Reachability evidence-acquisition economics

The complete Parser plus 15-cell qualification path consumed 1,976,047 actual
tokens. Promoting p000 saves 182,606 tokens per future two-stage deployment, so
the full evidence investment breaks even only on deployment 11. At ten
deployments it remains 149,987 tokens negative.

A post-outcome neutral/p000-first replay excludes 548,214 p100 tokens, retains
the paired P02 ambiguity replication, and reduces acquisition cost to
1,427,833 tokens. Its break-even is deployment 8 and its net saving after ten
deployments is 398,227 tokens. This staged policy has not been prospectively
validated; it defines the next experiment. Evidence acquisition must be gated
by expected future family reuse, not only by per-deployment savings. See
[`agentic-artifacts/modus-codex-luna-max-reachability-qualification-economics-v1.json`](../agentic-artifacts/modus-codex-luna-max-reachability-qualification-economics-v1.json).

A tested qualification economics function then simulated deployment horizons
1–20. It always evaluates correctness, performance, and evidence stability
before saving. Full qualification remains `qualified_but_not_economic` through
deployment 10 and promotes at 11. Staged qualification promotes at deployment
8. Removing the Agent parser does not change the staged break-even, but saves
43,452 additional tokens at every horizon. See
[`agentic-artifacts/modus-codex-luna-max-reachability-deployment-simulation-v1.json`](../agentic-artifacts/modus-codex-luna-max-reachability-deployment-simulation-v1.json).

### Prospective staged-qualification replication

The staged neutral/p000-first policy was tested prospectively. A
protocol was frozen and hash-bound before dispatch over a new independent
Reachability pair (`reachability-p03` cycle-and-chord six-query batches,
`reachability-p04` the same input as ninety-six two-query batches) with new
task ids, a new graph family, and its own lock set. Eight gpt-5.3-codex-spark
high cells (neutral/p000 x 2 repetitions x 2 tasks) all executed validly,
passed hidden-case correctness, kept p000 local-only topology, and reported
complete usage with no web search and no redispatch.

All eight cells remained valid, but the staged prediction failed. p000 used
45.8% and 31.6% fewer median total tokens while running 1.912x and 2.136x
slower than neutral. Both ratios exceed the frozen absolute 1.25x performance
gate, so only neutral is eligible and no token break-even or promotion exists.

This corrects the first checked-in score, whose implementation mistakenly
evaluated `ratio <= 1 + 1.25` (2.25x) despite the protocol specifying an
absolute 1.25x maximum. The scorer now has a boundary regression test, and the
same preserved outcomes were rescored without redispatch. The result shows a
real Profile cost/behavior effect, but not a favorable cost-performance trade.
See
[`agentic-artifacts/modus-codex-spark-reachability-prospective-v1.json`](../agentic-artifacts/modus-codex-spark-reachability-prospective-v1.json).

### Luna P1e prospective Profile-task interaction

A new Modus-owned Reachability pair was then frozen at Modus `a1fc62d` and
run with gpt-5.6-luna max. All eight neutral/p000 cells completed with full
usage, hidden correctness, and expected p000 local-only topology. The first
manager summary was invalid because its implementation mishandled the public
benchmark format, ran seven rather than the frozen nine rounds, and omitted
benchmark success from the aggregate gate. That output is preserved; no model
cell was rerun, and a separately named corrected verifier measured the same
workspaces against the pre-registered rules.

The two tasks selected different actions. On one batch, p000 was slightly
faster and used 53.9% fewer tokens, so it was selected. On ninety-six batches,
p000 used 51.5% fewer tokens but was 2.77x slower, so it failed the absolute
1.25x performance gate and neutral was selected. The routed pair therefore
uses p000 for X01 and neutral for X02, saving 25.0% median tokens versus the
best eligible fixed action. This is positive prospective evidence for a
Profile-task interaction, not yet an economic deployment result: the 1,060,359
token acquisition cost breaks even only at deployment 12, while the frozen
horizon is eight. The unambiguous p000 failure on X02 authorizes only the
pre-registered p100 follow-up. See
[`agentic-artifacts/modus-codex-luna-max-reachability-p1e-stage1-v1.json`](../agentic-artifacts/modus-codex-luna-max-reachability-p1e-stage1-v1.json).

The authorized P100 follow-up then ran only on X02. Both repetitions were
correct, used complete usage, and changed exactly observer, shared, and target,
but remained 2.76x slower than neutral. P100 was therefore rejected and the
final route stayed X01→p000, X02→neutral. The follow-up added 218,664 evidence
tokens without improving the route; total acquisition became 1,279,023 tokens,
moving break-even to deployment 15 and leaving a 560,151-token deficit at the
frozen eight-deployment horizon.

Source inspection explains the null P100 result. The current P100 Profile
controls the three-file edit shape but tells observer to preserve raw input;
both Workers consequently rebuilt adjacency inside each batch rather than
preparing it once. Thus Profile topology is controllable, while intended
mechanism placement is not yet controlled. The next valid experiment is to
repair that E1 contract on development data and test it on a different frozen
multi-batch holdout, not rerun P1e as confirmation. See
[`agentic-artifacts/modus-codex-luna-max-reachability-p1e-final-v1.json`](../agentic-artifacts/modus-codex-luna-max-reachability-p1e-final-v1.json).

The existing additive `p100/e1-v2` development candidate already expressed
the missing mechanism: observer invokes shared preparation once and target
consumes the prepared representation. A frozen development-only calibration
therefore compared fresh neutral and e1-v2 twice on the already observed X02
task. All four cells were valid and correct; both e1-v2 cells passed exact
three-module topology and a dynamic non-raw prepared-representation gate.

E1-v2 reached 0.00601 seconds median, 2.12x faster than canonical p100 and
faster than fresh neutral's 0.00771 seconds. It also used 27.5% fewer median
tokens than neutral. This validates the Profile wording as a mechanism repair,
but the candidate remains unqualified because the task was used for
development. The result authorizes a different unseen connectivity holdout;
it is excluded from Router and deployment-economics evidence. See
[`agentic-artifacts/modus-codex-luna-max-reachability-e1v2-calibration-v1.json`](../agentic-artifacts/modus-codex-luna-max-reachability-e1v2-calibration-v1.json).

### Outcome-blind Agent route on unseen Connectivity P1f

Modus `42e9e10` added an unseen undirected-connectivity pair with one and 120
query batches. Before any Worker outcome, two gpt-5.6-luna max Router calls saw
only trusted contract/reuse descriptors and the three available action
mechanisms. Both returned the same route: Y01→p000 and Y02→e1-v2. Their reasons
consistently mapped single-batch work to local preparation and multi-batch
work to amortized shared preprocessing.

Both responses were exact valid JSON with complete usage. Router acquisition
was 31,067 tokens and its median live cost is 15,533.5 tokens per future
two-task deployment. This cost is frozen into the upcoming end-to-end
economics. The result authorizes a separately frozen selected-action Worker
comparison, but does not yet validate either route. See
[`agentic-artifacts/modus-codex-luna-max-connectivity-p1f-agent-router-v1.json`](../agentic-artifacts/modus-codex-luna-max-connectivity-p1f-agent-router-v1.json).

The separately frozen selected-action Worker wave then completed eight valid
cells. Every cell passed hidden correctness, exact topology, complete usage,
and nine-round noise gates; e1-v2 also passed its prepared-representation gate
twice. The Agent choices matched the lowest-token eligible action in both
evaluated selected-versus-neutral sets. P000 saved 55.1% Worker tokens on Y01;
e1-v2 saved 50.0% on Y02.

The routed Workers save 52.1% versus fixed neutral. After charging 15,533.5
live Router tokens per deployment, end-to-end saving remains 49.5%. Router and
Worker acquisition total 1,757,306 tokens; break-even is deployment 7, and the
frozen eight-deployment horizon yields a 552,342-token net saving. This is the
first prospective Modus result where an actual Agent Router selects different
Profiles on an unseen contract and remains net-positive after Router cost.

The result is preliminary rather than promoted evidence because selected
performance ratios are 1.236x and 1.210x, close to the absolute 1.25x gate,
and the initial protocol did not precommit an ambiguity repetition. A separate
post-outcome third-pair replication is required and must add its evidence cost.
See
[`agentic-artifacts/modus-codex-luna-max-connectivity-p1f-initial-v1.json`](../agentic-artifacts/modus-codex-luna-max-connectivity-p1f-initial-v1.json).

The separately frozen post-outcome third pair completed four additional valid
cells without changing actions or gates. Combining three repetitions per
action strengthens the route: Y01 p000 is now the fastest action and saves
47.2% Worker tokens; Y02 e1-v2 is only 1.057x slower than neutral and saves
45.9%. Both remain correct, topology-faithful, and noise-qualified; e1-v2 again
passes the prepared-representation mechanism gate. The original Agent route
continues to match the constrained Oracle on both tasks.

Replicated per-deployment economics remain attractive: Workers save 46.4%,
and Router-inclusive saving is 43.7%. But the extra four cells cost 683,322
tokens. Combined acquisition rises to 2,440,628 tokens, moving break-even from
deployment 7 to deployment 10. At the frozen eight-deployment horizon the
system is 424,028 tokens negative. Thus Modus now has replicated evidence that
Profile routing improves per-deployment cost-performance, but not that this
more robust evidence plan is net-positive at eight deployments. See
[`agentic-artifacts/modus-codex-luna-max-connectivity-p1f-replicated-v1.json`](../agentic-artifacts/modus-codex-luna-max-connectivity-p1f-replicated-v1.json).

### Linked long-horizon P2a Router

Modus `6166963` introduced one sequential workspace: Stage L optimizes one
batch, and Stage S inherits the exact Stage L implementation before optimizing
150 batches. Model-free qualification binds the parent implementation digest
and shows a 141x Stage S oracle advantage on the final workload.

Before any P2a Worker outcome, two Luna max Router calls independently selected
Stage L→p000 and Stage S→e1-v2. Both JSON responses were valid and their reasons
matched local preparation versus cross-batch reuse. Router acquisition is
37,789 tokens and its median live cost is 18,894.5 tokens per deployment. This
authorizes a balanced AB/BA routed-versus-neutral pipeline protocol; no linked
quality, performance, or economics conclusion is available yet. See
[`agentic-artifacts/modus-codex-luna-max-long-horizon-p2a-router-v1.json`](../agentic-artifacts/modus-codex-luna-max-long-horizon-p2a-router-v1.json).

The balanced AB/BA phase then completed four linked pipelines and eight Worker
calls. Every Stage L and Stage S passed correctness, custody, topology, parent
binding, and benchmark gates; routed Stage S passed the prepared mechanism in
both repetitions. Routed two-stage Workers used 36.2% fewer tokens, and still
saved 31.8% after charging the live Router.

No conclusion is released yet. Pair 1 routed final performance was 1.445x
neutral, while pair 2 was 0.528x, so the paired ratios straddle the frozen
1.25x boundary. The precommitted ambiguity rule requires one additional
routed-neutral linked pair. Initial acquisition is 1,415,122 tokens; its
hypothetical break-even would be 11 deployments, but economics remains deferred
until replication. See
[`agentic-artifacts/modus-codex-luna-max-long-horizon-p2a-initial-v1.json`](../agentic-artifacts/modus-codex-luna-max-long-horizon-p2a-initial-v1.json).

The hash-ordered third pair (neutral then routed) completed four more linked
Worker stages. Combining three repetitions per arm resolves the ambiguity.
Routed Stage L is 1.121x the fastest Stage L, and routed final performance is
slightly faster than neutral. All six pipelines are correct, all Stage S parent
bindings hold, and all three routed Stage S deliveries satisfy the coordinated
prepared-representation mechanism.

The linked route uses 37.4% fewer Worker tokens and 32.9% fewer tokens after
charging the live Router. This validates the complete behavioral chain on one
long-horizon workflow. The economic conclusion remains negative at the frozen
horizon: Router plus 12 Worker calls cost 2,107,808 acquisition tokens, so the
140,728-token per-deployment saving breaks even only at deployment 15; at eight
deployments the result is 981,984 tokens negative. The remaining problem is
not Worker routing utility but qualification cost. See
[`agentic-artifacts/modus-codex-luna-max-long-horizon-p2a-final-v1.json`](../agentic-artifacts/modus-codex-luna-max-long-horizon-p2a-final-v1.json).

### Low-acquisition linked P2b transfer

P2b changed the semantic contract to linked RangeSum while reusing the already
qualified single-batch p000 and prepared-reuse e1-v2 predicates. One
outcome-blind Router call selected Stage L→p000 and Stage S→e1-v2. The frozen
first-pair order was neutral then routed; both pipelines and all four stages
passed correctness, custody, parent binding, topology, mechanism, and noise.

The routed final result is faster than neutral. It uses 66.2% fewer Worker
tokens and 63.8% fewer Router-inclusive deployment tokens. Router plus four
Workers cost 907,042 acquisition tokens; saving is 424,596 tokens per
deployment, break-even is deployment 3, and the eight-deployment horizon is
2,489,726 tokens positive. No uncertainty trigger fired, so the protocol
correctly stopped without a second pair. This supports the hypothesis that
Modus becomes economic when qualified Profile predicates are transferred with
minimal, outcome-gated evidence. See
[`agentic-artifacts/modus-codex-luna-max-long-horizon-p2b-transfer-v1.json`](../agentic-artifacts/modus-codex-luna-max-long-horizon-p2b-transfer-v1.json).

P2c independently repeated the same low-acquisition protocol on linked
TokenFrequency. The Agent again selected Stage L→p000 and Stage S→e1-v2; both
pipelines were correct, parent-bound, and mechanism-faithful. Routed final
performance was faster, Worker tokens fell 23.0%, and live-Router deployment
tokens fell 18.7%. No uncertainty trigger fired, so the run stopped after one
pair.

Unlike P2b, P2c is not economic at eight deployments: 667,461 acquisition
tokens and 68,653 saving per deployment break even at deployment 10, leaving an
118,237-token deficit at eight. Thus low-cost transfer reliably improves
deployment efficiency across two semantics, but live-Agent net benefit is not
universal. A post-outcome calculation shows that caching the already verified
route would break even at deployment 8 with 9,371 tokens positive; that is a
next design hypothesis, not part of this primary result. See
[`agentic-artifacts/modus-codex-luna-max-long-horizon-p2c-transfer-v1.json`](../agentic-artifacts/modus-codex-luna-max-long-horizon-p2c-transfer-v1.json).

### Exact evidence-bound route cache

A minimal route cache now treats an Agent decision as reusable evidence only
under an exact identity. The key binds the task contract, typed descriptor,
Router prompt, model and effort, ordered action catalog, and every Profile
digest. The entry additionally binds the original Router score and decision
hash. Any drift, missing evidence, tampering, or unsupported action fails
closed and requires a new Agent decision.

The actual P2c decision replays from this cache with the same p000→e1-v2 route,
zero Router model calls, and zero Router tokens. This is model-free mechanism
evidence, not a new P2c outcome. Under cached repeated deployments, P2c would
break even at deployment 8 with 9,371 tokens positive; that arithmetic remains
post-outcome until a new P2d contract validates first-call creation and later
exact hits prospectively. See
[`agentic-artifacts/modus-route-cache-p2c-mechanism-v1.json`](../agentic-artifacts/modus-route-cache-p2c-mechanism-v1.json).

### Prospective cached-routing P2d first pair

On unseen linked Membership, one Agent call selected a new reverse route:
Stage L→e1-v2 prepares the reusable representation early, then Stage S→p000
changes only target relative to the exact parent. The hash-bound entry replayed
that route with zero model calls before any Worker outcome. Both pipelines and
all mechanism, parent, topology, custody, and correctness gates passed.

The cached route uses 22.9% fewer Worker tokens, but the first pair is not
conclusive. Routed final performance is 1.215x neutral, inside the frozen near-
threshold band, and neutral relative MAD is 14.2%. Cached economics miss the
eight-deployment horizon by only 12 tokens, but the precommitted rule requires
a reversed second pair before any conclusion. See
[`agentic-artifacts/modus-codex-luna-max-long-horizon-p2d-initial-v1.json`](../agentic-artifacts/modus-codex-luna-max-long-horizon-p2d-initial-v1.json).

The reversed second pair resolved P2d as a negative routing result. All four
pipelines remained correct, linked, topology-faithful, and mechanism-faithful;
the cache continued to replay the exact Agent decision with zero model cost.
But the decision itself was wrong for utility. Across two repetitions, the
reversed route was 1.387x slower, used 3.6% more Worker tokens, and has no
break-even deployment. Combined acquisition is 1,224,149 tokens and the eight-
deployment net is -1,310,165 tokens.

This separates cache correctness from route qualification. An exact cache can
reliably replay a bad outcome-blind decision. A deployment cache must therefore
bind correctness, performance, stability, and cost evidence—not only Router
JSON and its provenance—and the Agent must abstain when its action conflicts
with qualified stage-mechanism evidence. See
[`agentic-artifacts/modus-codex-luna-max-long-horizon-p2d-final-v1.json`](../agentic-artifacts/modus-codex-luna-max-long-horizon-p2d-final-v1.json).

### Outcome-qualified route cache

Cache identity and route qualification are now separate immutable layers. A
deployment loader first validates the exact v1 cache entry, then requires a
derived qualification envelope that binds the same decision, the Worker
outcome evidence hash, and the current correctness/performance/noise/token
policy. Status is recomputed from observed evidence; callers cannot promote a
route by editing `status`.

P2b produces a qualified envelope and returns p000→e1-v2 with zero model calls.
P2d produces a rejected envelope and returns no route despite an exact cache
hit. Route mismatch, evidence tamper/missing files, threshold drift, status
tamper, and cache/decision tamper all fail closed. This closes the defect found
by P2d: cached Agent provenance is necessary, while qualified Worker outcome
evidence is the deployment authority. See
[`agentic-artifacts/modus-route-qualification-envelope-v1.json`](../agentic-artifacts/modus-route-qualification-envelope-v1.json).
