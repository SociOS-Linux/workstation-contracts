# LRK Conformance Note

This note anchors the LRK / Semantic Holography conformance work in `workstation-contracts`.

## Role of this repo

`workstation-contracts` is the contract and CI conformance lane.

It is the correct home for:
- LRK schema/example smoke validation
- B11/TruthSurface and DeltaSurface output checks
- publication bundle validation
- trust-closure and governance-grade witness-policy checks
- CI entrypoints that expect a checked-out canonical `sourceos-spec`

## Follow-on work

- land validation scripts
- land CI entrypoints
- land publication/trust-complete checks
- align validation targets to upstream TruthSurface / DeltaSurface naming
