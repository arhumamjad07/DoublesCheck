# DoublesCheck — submission preparation

Status: working no-credit prototype; not a completed or submitted entry.

## Problem and intended user

Beginner Pokemon doubles players often choose favourite Pokemon without knowing
how to build legal sets, fill supporting roles or spot shared weaknesses.
DoublesCheck preserves their choices and builds an inspectable starting team.

Primary track: Reasoning Architecture. The key behaviour is constrained search,
remembered preferences, independent legality checking, refusal of invalid results
and explanations grounded in a consistent historical dataset.

## Working features to show

- One, three and six locked favourites; six locks are preserved and reviewed.
- Real Pokedex and historical ladder usage joined through local Zetaris.
- Meterless H-MEM remembers the first favourite and an avoided teammate across runs.
- Showdown checks sets, moves, abilities, items, EVs and full-team clauses.
- Member roles, selection rationale, shared weaknesses, example leads and four-of-six options.
- Copyable/exportable Showdown team and decision trace.
- Explicit offline sample mode and zero model calls in this version.

## Suggested 2–3 minute demo script

1. **0:00–0:20 — problem.** Explain the difficulty of building around a favourite
   without understanding legal moves and doubles support.
2. **0:20–0:55 — one favourite.** Enter Charizard, choose connected data, generate a
   report and show that six members are returned. Explain the historical format.
3. **0:55–1:25 — evidence.** Open Charizard's set and one partner's rationale;
   show the weakness table, legality result and Showdown export.
4. **1:25–1:55 — memory.** In a separate demo profile, save an avoided teammate,
   then run again without repeating it. Show the recalled record and its effect.
5. **1:55–2:20 — constraints.** Demonstrate three locked favourites or explain that
   six locks preserve the roster. Show a banned species producing an honest error.
6. **2:20–2:45 — architecture and limits.** Show the source/trace files, H-MEM test
   result, and distinguish a legal starting team from an optimized winning team.

This script currently demonstrates local planning. Do not describe it as a live
Nightshift LLM demonstration. Add the final Nightshift-powered feature only after
a genuinely free route has been configured and tested; retain honest failure modes.

## Sponsor explanation draft

**Zetaris:** serves separate Pokedex, historical VGC usage and reference snapshots;
the app joins Pokedex and usage through its SQL REST interface. Docker Compose
runs the supplied local platform.

**Meterless H-MEM:** captures explicit preferences with source/provenance, retrieves
them across processes, reinjects context and supplies enforced planning constraints.
The reference core, Apache license and passing conformance suite are included.

**Nightshift/NVIDIA:** the earlier prototype routed separate Builder and Evaluator
calls through Nightshift to NVIDIA Nemotron and recorded model identities. The
current no-credit product flow deliberately makes no model calls. Final integration
and reliable free-route demonstration remain open requirements.

**Development:** built with an AI coding assistant; Cursor is optional under the
updated guide. Declare the use of pre-existing Showdown and H-MEM implementations.

## Still required before final submission

Demo 1 source and documentation are published at
https://github.com/arhumamjad07/DoublesCheck (tag: demo-1). This is source
publication, not a deployed application or a completed hackathon entry.

Confirm the latest HackOS rules, finish the Nightshift feature without surprise
charges, review output quality with players, prepare the actual deck/video and
complete all HackOS fields. Do not present this draft as evidence that every
requirement is already met.
