from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "check-fixture-reference"
MANIFEST = ROOT / "fixtures" / "tritrpc-v1-fixture-reference.json"


class FixtureReferenceCheckerTests(unittest.TestCase):
    def test_manifest_has_expected_source(self) -> None:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["kind"], "TriTRPCFixtureReference")
        self.assertEqual(data["source"]["repository"], "SocioProphet/TriTRPC")
        self.assertEqual(data["source"]["commit"], "58741244057ed1346676c7b95c9a1ec940f12952")
        self.assertEqual(data["source"]["path"], "fixtures/vectors_hex_unary_rich.txt")

    def test_checker_emits_receipt(self) -> None:
        receipt = ROOT / ".workstation" / "test-reports" / "fixture-reference-check-test.json"
        if receipt.exists():
            receipt.unlink()
        proc = subprocess.run(
            [sys.executable, str(TOOL), "--receipt", str(receipt)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(payload["kind"], "FixtureReferenceCheckReceipt")
        self.assertEqual(payload["status"], "pass")


if __name__ == "__main__":
    unittest.main()
