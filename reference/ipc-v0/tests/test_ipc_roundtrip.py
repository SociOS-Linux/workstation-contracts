from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


class IPCV0RoundtripTests(unittest.TestCase):
    def test_caps_adapter_roundtrip(self) -> None:
        root = Path(__file__).resolve().parents[1]
        out_dir = root / ".workstation" / "test-reports" / "ipc"
        cmd = [
            sys.executable,
            "-m",
            "src.contract_runner.runner",
            "--adapter",
            f"{sys.executable} -m src.adapters.caps_adapter",
            "--out",
            str(out_dir),
            "--op",
            "text.caps",
            "--text",
            "abc",
        ]
        proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        result = json.loads(proc.stdout)
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["text"], "ABC")

        transcript = (out_dir / "ipc-transcript.ndjson").read_text(encoding="utf-8")
        self.assertIn('"type":"hello"', transcript)
        self.assertIn('"type":"capabilities"', transcript)
        self.assertIn('"type":"invoke"', transcript)
        self.assertIn('"type":"result"', transcript)

        receipt = json.loads((out_dir / "run-receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["v"], "run-receipt.v0")
        self.assertEqual(receipt["result"]["data"]["text"], "ABC")


if __name__ == "__main__":
    unittest.main()
