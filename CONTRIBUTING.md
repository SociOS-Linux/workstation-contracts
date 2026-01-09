# Contributing

This repository is a **spec + conformance** repo. Keep it small, auditable, and stable.

## Local setup (PEP 668 safe on macOS/Homebrew)

Do **not** install dependencies into system Python. Use the repo-local venv via Make:

    make deps
    make validate

(Those are indented code blocks on purpose, so nobody copies Markdown fences into a terminal.)

## What belongs here

- Versioned JSON Schemas (`schemas/`)
- Validator tooling (`tools/`)
- Examples (`examples/`)
- Conformance fixtures (`conformance/`)
- Docs that explain the spec (`docs/`, `README.md`)

## What does not belong here

- Runner/orchestrator implementations
- Image build pipelines (truth-lane publishing)
- Large dependency graphs or framework code

## Schema changes

- Treat schema changes as **API changes**.
- Add a new schema file for a new version (e.g., `workstation-contract.v0.2.schema.json`).
- Keep older schemas during migrations.
- Update the validator to handle multiple versions if the runner needs it.

## Review checklist

- `make deps && make validate` passes
- New/changed fields documented in README
- Conformance fixtures updated (good + bad cases)
- No new heavy dependencies without strong justification
