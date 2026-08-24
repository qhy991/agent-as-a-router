import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "configs/modus_long_horizon_p2i_agent_proposal_v1.json"


def _tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


class LongHorizonP2iProtocolTest(unittest.TestCase):
    def test_agent_can_only_propose_a_qualification_pair(self):
        value = json.loads(PROTOCOL.read_text())
        self.assertTrue(value["run_authorized"])
        self.assertEqual(value["model"], {
            "local_slug": "gpt-5.6-luna",
            "reasoning_effort": "max",
            "authentication": "ChatGPT login",
        })
        self.assertEqual(value["router"]["repetitions"], 1)
        self.assertFalse(value["next_phase"]["worker_deployment_authorized"])
        self.assertEqual(value["next_phase"]["frozen_pair_order_if_valid"], ["proposed-route", "neutral"])
        self.assertFalse(value["next_phase"]["automatic_redispatch"])

    def test_task_profiles_prompt_and_scorer_are_hash_bound(self):
        value = json.loads(PROTOCOL.read_text())
        for profile in value["profiles"].values():
            self.assertEqual(
                hashlib.sha256(Path(profile["profile_path"]).read_bytes()).hexdigest(),
                profile["profile_sha256"],
            )
        prompt = ROOT / value["router"]["prompt"]
        self.assertEqual(hashlib.sha256(prompt.read_bytes()).hexdigest(), value["router"]["prompt_sha256"])
        seed = ROOT / value["task"]["seed_root"]
        self.assertEqual(_tree_sha256(seed), value["task"]["seed_tree_sha256"])
        qualification = ROOT / value["task"]["qualification_path"]
        self.assertTrue(json.loads(qualification.read_text())["passed"])
        self.assertEqual(hashlib.sha256(qualification.read_bytes()).hexdigest(), value["task"]["qualification_sha256"])
        scorer = ROOT / value["provenance"]["scorer_path"]
        self.assertEqual(hashlib.sha256(scorer.read_bytes()).hexdigest(), value["provenance"]["scorer_sha256_at_freeze"])


if __name__ == "__main__":
    unittest.main()
