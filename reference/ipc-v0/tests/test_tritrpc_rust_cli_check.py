from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "run-tritrpc-rust-cli-check"


class TritRPCRustCLICheckTests(unittest.TestCase):
    def test_dry_run_emits_receipt(self) -> None:
        receipt = ROOT / ".workstation" / "test-reports" / "tritrpc-rust-cli-check-test.json"
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
        self.assertEqual(payload["kind"], "TritRPCRustCLICheckReceipt")
        self.assertEqual(payload["mode"], "dry-run")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["source"]["repository"], "SocioProphet/TriTRPC")

    def test_execute_requires_all_paths(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(TOOL), "--execute"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("--execute requires", proc.stderr)


if __name__ == "__main__":
    unittest.main()
