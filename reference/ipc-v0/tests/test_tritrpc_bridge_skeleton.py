from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


class TritRPCBridgeSkeletonTests(unittest.TestCase):
    def test_remote_echo_skeleton_roundtrip(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out_dir = root / ".workstation" / "test-reports" / "tritrpc-bridge"
        cmd = [
            sys.executable,
            "-m",
            "src.contract_runner.runner",
            "--adapter",
            f"{sys.executable} -m src.adapters.tritrpc_bridge_adapter",
            "--out",
            str(out_dir),
            "--op",
            "remote.echo",
            "--text",
            "bridge",
        ]
        proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        result = json.loads(proc.stdout)
        self.assertTrue(result["ok"])
        self.assertTrue(result["data"]["skeletonMode"])
        self.assertEqual(result["data"]["transport"], "tritrpc")
        self.assertEqual(result["data"]["method"], "echo")
        self.assertEqual(result["data"]["args"], {"text": "bridge"})

        transcript = (out_dir / "ipc-transcript.ndjson").read_text(encoding="utf-8")
        self.assertIn('"name":"remote.echo"', transcript)
        self.assertIn('"type":"invoke"', transcript)
        self.assertIn('"type":"result"', transcript)

        receipt = json.loads((out_dir / "run-receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["invocation"]["op"], "remote.echo")
        self.assertTrue(receipt["result"]["data"]["skeletonMode"])


if __name__ == "__main__":
    unittest.main()
