# Contributing

## Local setup (PEP 668 safe on macOS/Homebrew)
Do **not** install dependencies into system Python. Use the repo-local venv via Make:

    make deps
    make validate

## Adding a new contract example
1. Add a JSON file under `examples/`
2. Run `make validate`
3. If you introduce a new semantic rule, update `tools/validate_contract.py` and document it in SPEC.md.

## Adding a new schema version
- Add `schemas/workstation-contract.vX.Y.schema.json`
- Keep old versions in place (do not rewrite history)
- Update validator dispatch to select schema by `contract_version`

## Style rules
- Container images MUST be pinned by digest (`...@sha256:<64 hex>`)
- Tags are not allowed for replay lanes (tags drift; digests don’t)
