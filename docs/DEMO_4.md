# Demo 4: Zetaris Evidence Lens

Demo 4 is a feature milestone beyond Demo 3. Previously, Zetaris returned the
full encoded catalogue and Python generated the partner shortlist. Connected
mode now asks real SQL to rank a favourite-specific pool and visibly explains
the evidence behind it. Python still checks team fit and source sets, and the
independent validator retains final authority over historical legality.

## What changed

- Five safely normalised historical tables supplement the original catalogue.
- SQL joins facts, usage, teammate relationships, sourced-set counts and snapshot
  identity. It excludes locked/avoided species and returns at most 48 partners.
- The Evidence Lens exposes completed live-query status, selected favourite,
  joined sources, month/cutoff, row counts, aggregate coverage, timing and safe receipts.
- Changing Charizard to Pelipper changes the SQL evidence: Torkoal versus
  Archaludon at the top of the historical association ranking.
- A connected failure stops the result. Offline sample is a deliberate separate
  choice, and the saved genuine Demo 3 repair is explicitly labelled saved.

For a provided six-member review fixture or six locked favourites, the Lens is
comparison context. It does not claim SQL generated that input team. Set repair
continues through the proven Critic / Planner / independent-check workflow.

## Verified scope

The upgrade passed 174 application tests in each of two clean installations,
13/13 H-MEM conformance checks, two real HTTP recording rehearsals and two browser
rehearsals. A genuine live Nemotron repair regression also passed, including an
explicit continuation after a gateway interruption. See the complete
[verification and submission gate](EVIDENCE_VERIFICATION.md).

The release-label/documentation commit does not change application code or make
additional model requests. The previous `demo-3` tag stays at
`acc708bf565d786e1d1d1bcde3903fe8229b7192`; Demo 1 and Demo 2 remain preserved too.

## Run and record

Follow the [exact setup, registration and three-minute runbook](ZETARIS_EVIDENCE_LENS.md).
Use connected local planning for Charizard, inspect the receipts, then repeat
with Pelipper. Both builds make zero model calls. Present the separately saved
Sneasler model repair as saved genuine evidence, never as an instant live response.

The existing limitation remains historical Regulation H / November 2024 at the
1500 cutoff. Usage and association do not prove a win rate or an optimal team.
Gateway availability and hands-on player validation remain limitations. No
additional snapshot, PokeAPI feature, opponent preview or SpaceXAI/Grok work is claimed.

See the [fresh release security audit](SECURITY_AUDIT_DEMO_4.md). The milestone
tag identifies source code; the final hackathon form still requires submission
and confirmation by the creator.
