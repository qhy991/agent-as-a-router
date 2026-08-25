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

--- Current evidence view ---

{
  "decision_contract": {
    "allowed_decisions": [
      "dispatch",
      "abstain",
      "request_qualification"
    ],
    "allowed_strategies": [
      "unconstrained-optimization",
      "target-scoped-optimization",
      "prepared-shared-optimization"
    ],
    "evidence_required_for_dispatch": true,
    "no_relevant_experience": "request_qualification"
  },
  "decision_policy": {
    "decisions": [
      "dispatch",
      "abstain",
      "request_qualification"
    ],
    "exact_cache_before_agent": true,
    "maximum_performance_ratio": 1.25,
    "maximum_relative_mad": 0.1,
    "minimum_token_saving_fraction": 0.15,
    "missing_evidence_decision": "request_qualification",
    "quality_order": [
      "correctness",
      "behavior",
      "performance",
      "stability",
      "tokens"
    ]
  },
  "provenance": {
    "experience_registry_sha256": "1ddbb06180c24773984e2e6e68da587de50d37c41f89b2b540ab09781dfb6a08",
    "router_policy_sha256": "bfc14548f3b8d8825802bf115f443211eae49c46b6cc8602aa6942ec3547762a"
  },
  "router_experience": [
    {
      "evidence_ref": "evidence:router-policy:evidence-bound-routing",
      "experience_id": "evidence-required-for-routing",
      "maturity": "replicated-development",
      "observation": {
        "evidence_bound_exact_plan_matches": "3/3",
        "evidence_bound_stage_matches": "12/12",
        "known_state_zero_token_cache_preferred": true,
        "task_only_exact_plan_matches": "0/3",
        "task_only_stage_matches": "4/12"
      }
    }
  ],
  "schema": "modus-router-evidence-batch-v1",
  "strategies": [
    {
      "behavior_contract": {
        "reusable_preparation": "optional",
        "topology": "unconstrained"
      },
      "strategy_id": "unconstrained-optimization",
      "summary": "Broad implementation search without a required edit topology."
    },
    {
      "behavior_contract": {
        "reusable_preparation": "absent",
        "topology": "target-only"
      },
      "strategy_id": "target-scoped-optimization",
      "summary": "Concentrate implementation changes in the named target module."
    },
    {
      "behavior_contract": {
        "reusable_preparation": "required",
        "topology": "observer-shared-target"
      },
      "strategy_id": "prepared-shared-optimization",
      "summary": "Prepare one minimal query-ready shared representation and consume it in the target."
    }
  ],
  "tasks": [
    {
      "relevant_experience": [
        {
          "evidence_ref": "evidence:profile-affinity:single-batch-keyed-reduction",
          "experience_id": "single-batch-keyed-reduction",
          "maturity": "prospective-single-instance",
          "observations": {
            "behavior_passed": true,
            "correctness_passed": true,
            "performance_ratio_to_unconstrained": 0.9420727522306109,
            "selected_worker_tokens": 66555,
            "token_saving_fraction_vs_unconstrained": 0.6135039866202867
          },
          "rejected_strategies": [],
          "selected_strategy": "target-scoped-optimization",
          "task_signature": {
            "performance_objective": "latency-subject-to-correctness-then-tokens",
            "reusable_preparation": false,
            "semantic_kind": "keyed-reduction",
            "workload_shape": "single-batch"
          }
        }
      ],
      "task": {
        "performance_objective": "latency-subject-to-correctness-then-tokens",
        "reusable_preparation": false,
        "schema": "modus-router-task-descriptor-v1",
        "semantic_kind": "keyed-reduction",
        "task_id": "single-batch-keyed-reduction",
        "worker_model": {
          "reasoning_effort": "max",
          "slug": "gpt-5.6-luna"
        },
        "workload_shape": "single-batch"
      }
    },
    {
      "relevant_experience": [
        {
          "evidence_ref": "evidence:profile-affinity:repeated-batch-keyed-aggregate",
          "experience_id": "repeated-batch-keyed-aggregate",
          "maturity": "prospective-single-instance",
          "observations": {
            "behavior_passed": true,
            "correctness_passed": true,
            "performance_ratio_to_unconstrained": 0.946623713845342,
            "selected_worker_tokens": 159978,
            "token_saving_fraction_vs_unconstrained": 0.4180120924614925
          },
          "rejected_strategies": [
            {
              "performance_ratio_to_unconstrained": 8.40570976297263,
              "reason": "performance-ineligible",
              "strategy_id": "target-scoped-optimization",
              "token_saving_fraction_vs_unconstrained": 0.6932829359506989
            }
          ],
          "selected_strategy": "prepared-shared-optimization",
          "task_signature": {
            "performance_objective": "latency-subject-to-correctness-then-tokens",
            "reusable_preparation": true,
            "semantic_kind": "keyed-distinct-aggregate",
            "workload_shape": "repeated-batches"
          }
        }
      ],
      "task": {
        "performance_objective": "latency-subject-to-correctness-then-tokens",
        "reusable_preparation": true,
        "schema": "modus-router-task-descriptor-v1",
        "semantic_kind": "keyed-distinct-aggregate",
        "task_id": "repeated-batch-keyed-aggregate",
        "worker_model": {
          "reasoning_effort": "max",
          "slug": "gpt-5.6-luna"
        },
        "workload_shape": "repeated-batches"
      }
    },
    {
      "relevant_experience": [
        {
          "evidence_ref": "evidence:profile-affinity:direct-bit-transformation",
          "experience_id": "direct-bit-transformation",
          "maturity": "prospective-single-instance",
          "observations": {
            "behavior_passed": true,
            "correctness_passed": true,
            "performance_ratio_to_unconstrained": 0.9484019432370238,
            "selected_worker_tokens": 125279,
            "token_saving_fraction_vs_unconstrained": 0.9225360734478648
          },
          "rejected_strategies": [],
          "selected_strategy": "target-scoped-optimization",
          "task_signature": {
            "performance_objective": "latency-subject-to-correctness-then-tokens",
            "reusable_preparation": false,
            "semantic_kind": "direct-bit-transformation",
            "workload_shape": "single-batch"
          }
        }
      ],
      "task": {
        "performance_objective": "latency-subject-to-correctness-then-tokens",
        "reusable_preparation": false,
        "schema": "modus-router-task-descriptor-v1",
        "semantic_kind": "direct-bit-transformation",
        "task_id": "direct-bit-transformation",
        "worker_model": {
          "reasoning_effort": "max",
          "slug": "gpt-5.6-luna"
        },
        "workload_shape": "single-batch"
      }
    }
  ]
}

--- Required response ---

Return exactly one JSON object and no surrounding text. Return one route for every task in the given order:

{"schema":"modus-router-batch-decision-v1","routes":[{"task_id":"single-batch-keyed-reduction","decision":"dispatch|abstain|request_qualification","strategy":"one allowed strategy or null","evidence_refs":["required for dispatch"],"reason":"short evidence-grounded reason"},{"task_id":"repeated-batch-keyed-aggregate","decision":"dispatch|abstain|request_qualification","strategy":"one allowed strategy or null","evidence_refs":["required for dispatch"],"reason":"short evidence-grounded reason"},{"task_id":"direct-bit-transformation","decision":"dispatch|abstain|request_qualification","strategy":"one allowed strategy or null","evidence_refs":["required for dispatch"],"reason":"short evidence-grounded reason"}]}
