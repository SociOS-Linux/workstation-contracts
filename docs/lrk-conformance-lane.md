# LRK Conformance Lane

This document defines the conformance posture for the LRK / Semantic Holography layer within `workstation-contracts`.

## Purpose

This repo should ensure that:

1. LRK schema examples validate against the canonical contract shapes,
2. lane contracts that produce truth/B11-style surfaces are well-formed,
3. starter and spine outputs can be smoke-tested before they are trusted by downstream automation.

## Recommended scope here

- schema/example validation
- B11/TruthSurface and DeltaSurface output checks
- publication bundle validation
- governance-grade witness-policy and trust-closure checks

## Not in scope

- computing semantic invariants
- owning the canonical schema family
- runtime collection or publication logic
