> Historical three-Pokemon integration notes. The final paragraph describes an earlier prototype, not Demo 1. See VERIFICATION.md and docs/ARCHITECTURE.md for the current real-data, model-free application.

# DoublesCheck H-MEM verification

Verified on 23 October 2026 in the existing `open-agent-hack` project.

## Implemented product feature

H-MEM stores explicit player preferences and retrieves them in later processes.
Recalled preferences reach both the Builder and Evaluator. A deterministic
partner filter prevents approval of an avoided partner, independently of the
model's verdict. The run trace records recalled memory IDs and constraints.

This uses the Apache-2.0 Meterless reference engine pinned to commit
`1742dec56a66e58eef9dda2d2b865823758ca8cd`. Source, license, hashes and compiled
runtime are included under `vendor/hmem/`. The app facade additionally persists
retrieval access counters. No external embedding service is used.

## Results

- Official Meterless conformance suite against `hmem-engine.mjs`: **13/13 passed**.
- Application suite (`test_coaching` and `test_hmem`): **26 tests passed**.
- All 17 unique vendored source files matched their recorded SHA-256 hashes.
- Python syntax checks passed.

Conformance covers record source validation, exact confidence feedback deltas,
ranking order, sleep guardrails, conflict resolution without deletion, audit
history and dream approval boundaries. It is the upstream suite, not a claim
of exhaustive security or production validation.

The nine integration tests use actual H-MEM processes and local persistence.
They verify fresh-process recall, provenance, profile isolation, corrections
with preserved history, idempotent input, explicit clearing and audit reason,
busy-profile handling, invalid profile rejection, preference reinjection into
both model roles, and refusal to approve a forbidden partner after the revision
limit. Mocked model responses deliberately return false approval in the
constraint tests; Python still rejects the proposal.

A live check exposed contradictory model prose despite correct numeric fields.
The app now generates published explanations, trade-offs and beginner guidance
from computed facts before evaluation. A regression test injects the observed
false claim that Charizard is neutral to Electric and verifies it cannot appear
in the published explanation. Model-generated teammate selection remains subject
to catalogue, preference and numerical checks.

## Live service checks

The separate `memory-proof` profile saved Charizard as favourite and Blastoise as
an avoided partner. A fresh engine process recalled both records. The Zetaris
query succeeded and the live Builder/Evaluator workflow selected Venusaur in two
AI calls (trace `9aa9afe828e44f13b1d19b8b4008f3d8`). The prose issue observed in
that run is addressed by the factual-rendering regression above.

After the correction, a final fresh app process again recalled both preferences
and retrieved the Zetaris data, but Nightshift returned HTTP 502 on the Builder
request (trace `8b57ca743b3b4d90bd2fa80d096517c5`). No retry was sent and no result
was approved. The local logs examined did not establish the cause. Thus memory
persistence and enforcement pass, while reliable live model routing remains an
external service limitation; a successful final live response is not claimed.

## Scope

Memory tests make no API or model calls. The engine uses reference hash
embeddings and JSON storage. Only explicit preferences are written by this app;
automatic memory mining, dreaming and sleep are not app features. The coaching
catalogue remains three mock Pokemon and VGC legality remains `not_verified`.
Passing these tests demonstrates the feature; event eligibility is decided by
the organizers.
