from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs" / "specs" / "ipc-v0-tritrpc-rust-cli-wrapper.md"


class TritRPCRustCLIWrapperDocTests(unittest.TestCase):
    def test_doc_selects_rust_cli_wrapper_path(self) -> None:
        text = DOC.read_text(encoding="utf-8")
        for snippet in [
            "Rust CLI is the preferred wrapper target",
            "rust/tritrpc_v1/src/bin/trpc.rs",
            "trpc pack --service S --method M --json path.json --nonce HEX --key HEX",
            "trpc verify --fixtures fixtures/vectors_hex_unary_rich.txt --nonces fixtures/vectors_hex_unary_rich.txt.nonces",
            "tritrpc.fixture.verify",
            "tritrpc.frame.pack",
        ]:
            self.assertIn(snippet, text)

    def test_doc_preserves_no_network_boundary(self) -> None:
        text = DOC.read_text(encoding="utf-8")
        for snippet in [
            "not as a network client",
            "network transport",
            "remote invocation",
            "implicit fixture fetching",
            "vendoring fixture bytes into workstation-contracts",
        ]:
            self.assertIn(snippet, text)


if __name__ == "__main__":
    unittest.main()
