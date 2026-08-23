import unittest

from acrouter_repro.qualification_economics import (
    QualificationEconomicsError,
    evaluate_qualification_economics,
)


class QualificationEconomicsTest(unittest.TestCase):
    def evaluate(self, **changes):
        values = {
            "acquisition_tokens": 1_976_047,
            "baseline_deployment_tokens": 347_262,
            "candidate_deployment_tokens": 164_656,
            "expected_deployments": 11,
            "correctness_passed": True,
            "performance_passed": True,
            "evidence_stable": True,
            "minimum_saving_fraction": 0.15,
        }
        return evaluate_qualification_economics(**{**values, **changes})

    def test_reachability_full_breaks_even_at_eleven(self):
        before = self.evaluate(expected_deployments=10)
        self.assertEqual(before["break_even_deployments"], 11)
        self.assertEqual(before["net_tokens_at_expected_deployments"], -149_987)
        self.assertEqual(before["decision"], "qualified_but_not_economic")
        at_break_even = self.evaluate(expected_deployments=11)
        self.assertEqual(at_break_even["net_tokens_at_expected_deployments"], 32_619)
        self.assertEqual(at_break_even["decision"], "promote")

    def test_reachability_staged_breaks_even_at_eight(self):
        result = self.evaluate(
            acquisition_tokens=1_427_833,
            expected_deployments=8,
        )
        self.assertEqual(result["break_even_deployments"], 8)
        self.assertEqual(result["net_tokens_at_expected_deployments"], 33_015)
        self.assertEqual(result["decision"], "promote")

    def test_quality_and_stability_precede_economics(self):
        self.assertEqual(
            self.evaluate(correctness_passed=False)["decision"],
            "defer_correctness",
        )
        self.assertEqual(
            self.evaluate(performance_passed=False)["decision"],
            "defer_performance",
        )
        self.assertEqual(
            self.evaluate(evidence_stable=False)["decision"],
            "defer_unstable_evidence",
        )

    def test_low_or_negative_saving_does_not_promote(self):
        low = self.evaluate(
            baseline_deployment_tokens=100_000,
            candidate_deployment_tokens=86_000,
        )
        self.assertAlmostEqual(low["saving_fraction"], 0.14)
        self.assertEqual(low["decision"], "do_not_promote")
        no_saving = self.evaluate(
            baseline_deployment_tokens=100_000,
            candidate_deployment_tokens=100_000,
        )
        self.assertIsNone(no_saving["break_even_deployments"])
        self.assertEqual(no_saving["decision"], "do_not_promote")

    def test_invalid_inputs_fail_closed(self):
        for changes in (
            {"acquisition_tokens": 0},
            {"baseline_deployment_tokens": 0},
            {"candidate_deployment_tokens": -1},
            {"expected_deployments": 0},
            {"correctness_passed": 1},
            {"minimum_saving_fraction": 1.1},
        ):
            with self.subTest(changes=changes):
                with self.assertRaises(QualificationEconomicsError):
                    self.evaluate(**changes)


if __name__ == "__main__":
    unittest.main()
