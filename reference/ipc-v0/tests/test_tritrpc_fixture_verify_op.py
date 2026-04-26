from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


class TritRPCFixtureVerifyOperationTests(unittest.TestCase):
    def test_fixture_verify_dry_run_roundtrip(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out_dir = root / ".workstation" / "test-reports" / "tritrpc-fixture-verify-op"
        receipt = ".workstation/test-reports/tritrpc-rust-cli-check-op.json"
        cmd = [
            sys.executable,
            "-m",
            "src.contract_runner.runner",
            "--adapter",
            f"{sys.executable} -m src.adapters.tritrpc_bridge_adapter",
            "--out",
            str(out_dir),
            "--op",
            "tritrpc.fixture.verify",
            "--text",
            "ignored-by-fixture-verify",
        ]
        proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        result = json.loads(proc.stdout)
        self.assertTrue(result["ok"])
        data = result["data"]
        self.assertTrue(data["ok"])
        self.assertEqual(data["mode"], "dry-run")
        self.assertEqual(data["receiptPayload"]["kind"], "TritRPCRustCLICheckReceipt")
        self.assertEqual(data["receiptPayload"]["status"], "pass")

        transcript = (out_dir / "ipc-transcript.ndjson").read_text(encoding="utf-8")
        self.assertIn('"name":"tritrpc.fixture.verify"', transcript)
        self.assertIn('"type":"invoke"', transcript)
        self.assertIn('"type":"result"', transcript)


if __name__ == "__main__":
    unittest.main()
