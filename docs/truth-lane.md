# Truth lane

The "truth lane" is the canonical replay environment for workstation/CI contracts.

Rule: container images MUST be pinned by digest (`...@sha256:<64 hex>`), not by tag.

Reason: tags drift; digests don't. This makes builds replayable and auditable.

Examples:
- GOOD: ghcr.io/socios-linux/truth-lane@sha256:...
- BAD:  ghcr.io/socios-linux/truth-lane:latest
