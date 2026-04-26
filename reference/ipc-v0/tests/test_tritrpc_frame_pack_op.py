from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


class TritRPCFramePackOperationTests(unittest.TestCase):
    def test_frame_pack_dry_run_roundtrip(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out_dir = root / ".workstation" / "test-reports" / "tritrpc-frame-pack-op"
        payload = root / "fixtures" / "payload-addvertex-a.json"
        receipt = ".workstation/test-reports/tritrpc-frame-pack-op.json"
        invoke_args = {
            "service": "hyper.v1",
            "method": "AddVertex_a.REQ",
            "json": str(payload),
            "receipt": receipt,
        }
        cmd = [
            sys.executable,
            "-m",
            "src.contract_runner.runner",
            "--adapter",
            f"{sys.executable} -m src.adapters.tritrpc_bridge_adapter",
            "--out",
            str(out_dir),
            "--op",
            "tritrpc.frame.pack",
            "--args-json",
            json.dumps(invoke_args),
        ]
        proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        result = json.loads(proc.stdout)
        self.assertTrue(result["ok"])
        data = result["data"]
        self.assertTrue(data["ok"])
        self.assertEqual(data["mode"], "dry-run")
        self.assertEqual(data["receipt"], receipt)
        self.assertEqual(data["receiptPayload"]["kind"], "TritRPCFramePackCheckReceipt")
        self.assertEqual(data["receiptPayload"]["service"], "hyper.v1")
        self.assertEqual(data["receiptPayload"]["method"], "AddVertex_a.REQ")

        transcript = (out_dir / "ipc-transcript.ndjson").read_text(encoding="utf-8")
        self.assertIn('"name":"tritrpc.frame.pack"', transcript)
        self.assertIn('"type":"invoke"', transcript)
        self.assertIn('"type":"result"', transcript)

    def test_frame_pack_requires_service_method_and_json(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out_dir = root / ".workstation" / "test-reports" / "tritrpc-frame-pack-missing-args"
        cmd = [
            sys.executable,
            "-m",
            "src.contract_runner.runner",
            "--adapter",
            f"{sys.executable} -m src.adapters.tritrpc_bridge_adapter",
            "--out",
            str(out_dir),
            "--op",
            "tritrpc.frame.pack",
            "--args-json",
            json.dumps({"service": "hyper.v1"}),
        ]
        proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, check=False)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("tritrpc.frame.pack requires", proc.stderr)


if __name__ == "__main__":
    unittest.main()
