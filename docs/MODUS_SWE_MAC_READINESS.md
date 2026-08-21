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
