from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_REF = ROOT / "fixtures" / "tritrpc-v1-fixture-reference.json"


class TritRPCFixtureReferenceTests(unittest.TestCase):
    def test_fixture_reference_pins_source_repo_commit_and_path(self) -> None:
        data = json.loads(FIXTURE_REF.read_text(encoding="utf-8"))
        source = data["source"]
        self.assertEqual(source["repository"], "SocioProphet/TriTRPC")
        self.assertEqual(source["commit"], "58741244057ed1346676c7b95c9a1ec940f12952")
        self.assertEqual(source["path"], "fixtures/vectors_hex_unary_rich.txt")
        self.assertEqual(source["noncePath"], "fixtures/vectors_hex_unary_rich.txt.nonces")

    def test_fixture_reference_tracks_expected_labels_and_boundary(self) -> None:
        data = json.loads(FIXTURE_REF.read_text(encoding="utf-8"))
        labels = set(data["expectedLabels"])
        self.assertIn("hyper.v1.AddVertex_a.REQ", labels)
        self.assertIn("hyper.v1.GetSubgraph_a_k1.RSP", labels)
        notes = "\n".join(data["notes"])
        self.assertIn("remain owned by SocioProphet/TriTRPC", notes)
        self.assertIn("No network transport binding", notes)


if __name__ == "__main__":
    unittest.main()
