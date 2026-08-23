"""Constraint-first economics for acquiring and promoting Profile evidence."""

from __future__ import annotations

import math
from typing import Any


class QualificationEconomicsError(ValueError):
    """Qualification economics input violates the decision contract."""


def _positive_int(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise QualificationEconomicsError(f"{field} must be a positive integer")
    return value


def _boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise QualificationEconomicsError(f"{field} must be boolean")
    return value


def evaluate_qualification_economics(
    *,
    acquisition_tokens: int,
    baseline_deployment_tokens: int,
    candidate_deployment_tokens: int,
    expected_deployments: int,
    correctness_passed: bool,
    performance_passed: bool,
    evidence_stable: bool,
    minimum_saving_fraction: float = 0.15,
) -> dict[str, Any]:
    """Evaluate quality gates first, then saving and deployment break-even."""
    acquisition = _positive_int(acquisition_tokens, "acquisition_tokens")
    baseline = _positive_int(
        baseline_deployment_tokens,
        "baseline_deployment_tokens",
    )
    candidate = _positive_int(
        candidate_deployment_tokens,
        "candidate_deployment_tokens",
    )
    deployments = _positive_int(expected_deployments, "expected_deployments")
    correctness = _boolean(correctness_passed, "correctness_passed")
    performance = _boolean(performance_passed, "performance_passed")
    stable = _boolean(evidence_stable, "evidence_stable")
    if (
        not isinstance(minimum_saving_fraction, (int, float))
        or isinstance(minimum_saving_fraction, bool)
        or not math.isfinite(float(minimum_saving_fraction))
        or not 0 <= float(minimum_saving_fraction) <= 1
    ):
        raise QualificationEconomicsError(
            "minimum_saving_fraction must be finite and between zero and one"
        )
    minimum = float(minimum_saving_fraction)
    saving_per_deployment = baseline - candidate
    saving_fraction = 1.0 - candidate / baseline
    break_even = (
        math.ceil(acquisition / saving_per_deployment)
        if saving_per_deployment > 0
        else None
    )
    net = deployments * saving_per_deployment - acquisition

    if not correctness:
        decision = "defer_correctness"
    elif not performance:
        decision = "defer_performance"
    elif not stable:
        decision = "defer_unstable_evidence"
    elif saving_per_deployment <= 0 or saving_fraction < minimum:
        decision = "do_not_promote"
    elif break_even is None or deployments < break_even:
        decision = "qualified_but_not_economic"
    else:
        decision = "promote"

    return {
        "acquisition_tokens": acquisition,
        "baseline_deployment_tokens": baseline,
        "candidate_deployment_tokens": candidate,
        "expected_deployments": deployments,
        "correctness_passed": correctness,
        "performance_passed": performance,
        "evidence_stable": stable,
        "minimum_saving_fraction": minimum,
        "saving_per_deployment_tokens": saving_per_deployment,
        "saving_fraction": saving_fraction,
        "break_even_deployments": break_even,
        "net_tokens_at_expected_deployments": net,
        "decision": decision,
    }
