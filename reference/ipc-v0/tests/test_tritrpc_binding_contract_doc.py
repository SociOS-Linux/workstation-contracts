from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs" / "specs" / "ipc-v0-tritrpc-v1-binding-contract.md"


class TritRPCBindingContractDocTests(unittest.TestCase):
    def test_binding_contract_preserves_authority_boundary(self) -> None:
        text = DOC.read_text(encoding="utf-8")
        for snippet in [
            "SocioProphet/TriTRPC",
            "source of truth",
            "does not yet expose a high-level network client API",
            "not:",
            "fake network RPC client",
            "no network transport implementation",
        ]:
            self.assertIn(snippet, text)

    def test_binding_contract_defines_layered_shape(self) -> None:
        text = DOC.read_text(encoding="utf-8")
        for snippet in [
            "IPC adapter layer",
            "TritRPC codec layer",
            "Transport layer",
            "pack_request",
            "parse_response",
            "invoke_frame",
            "Error mapping draft",
        ]:
            self.assertIn(snippet, text)


if __name__ == "__main__":
    unittest.main()
