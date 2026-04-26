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

    def test_fixture_verify_accepts_explicit_json_args(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out_dir = root / ".workstation" / "test-reports" / "tritrpc-fixture-verify-json-args"
        receipt = ".workstation/test-reports/tritrpc-rust-cli-check-json-args.json"
        invoke_args = {"receipt": receipt}
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
            "--args-json",
            json.dumps(invoke_args),
        ]
        proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        result = json.loads(proc.stdout)
        self.assertTrue(result["ok"])
        data = result["data"]
        self.assertTrue(data["ok"])
        self.assertEqual(data["receipt"], receipt)
        self.assertEqual(data["receiptPayload"]["kind"], "TritRPCRustCLICheckReceipt")

        run_receipt = json.loads((out_dir / "run-receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(run_receipt["invocation"]["args"], invoke_args)

    def test_fixture_verify_execute_requires_explicit_paths(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out_dir = root / ".workstation" / "test-reports" / "tritrpc-fixture-verify-execute-missing"
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
            "--args-json",
            json.dumps({"execute": True}),
        ]
        proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, check=False)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("execute mode requires", proc.stderr)


if __name__ == "__main__":
    unittest.main()
