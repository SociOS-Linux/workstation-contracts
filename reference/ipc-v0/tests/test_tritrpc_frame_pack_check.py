from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "run-tritrpc-frame-pack-check"
PAYLOAD = ROOT / "fixtures" / "payload-addvertex-a.json"


class TritRPCFramePackCheckTests(unittest.TestCase):
    def test_dry_run_emits_receipt(self) -> None:
        receipt = ROOT / ".workstation" / "test-reports" / "tritrpc-frame-pack-check-test.json"
        if receipt.exists():
            receipt.unlink()
        proc = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "--service",
                "hyper.v1",
                "--method",
                "AddVertex_a.REQ",
                "--json",
                str(PAYLOAD),
                "--receipt",
                str(receipt),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(payload["kind"], "TritRPCFramePackCheckReceipt")
        self.assertEqual(payload["mode"], "dry-run")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["service"], "hyper.v1")
        self.assertEqual(payload["method"], "AddVertex_a.REQ")
        self.assertEqual(payload["keyHexRedacted"], "<redacted>")

    def test_execute_requires_trpc_path(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "--service",
                "hyper.v1",
                "--method",
                "AddVertex_a.REQ",
                "--json",
                str(PAYLOAD),
                "--execute",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("--execute requires --trpc", proc.stderr)

    def test_rejects_bad_nonce(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "--service",
                "hyper.v1",
                "--method",
                "AddVertex_a.REQ",
                "--json",
                str(PAYLOAD),
                "--nonce",
                "not-hex",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("nonce", proc.stderr)


if __name__ == "__main__":
    unittest.main()
