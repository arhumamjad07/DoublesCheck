# Demo 1 - 24 October 2026

This milestone freezes a usable local team-planning and coaching prototype for
the larger DoublesCheck vision. The commit is named `demo 1`; tag `demo-1` identifies
the published milestone.

## Working flow

Choose a historical VGC doubles roster around one to six favourites, retrieve
real data, apply remembered preferences, search set/team options, independently
check legality and publish an inspectable report. Selecting all six preserves
that roster and selects/reviews its sets; the app does not force replacements.

The local GUI and CLI use the same orchestration. Offline sample mode runs
without credentials or service access. Connected mode uses a real local Zetaris
join. The main product makes zero cloud AI model calls.

## Changes captured in this milestone

- Real historical catalogue and explicit Regulation H scope.
- Richer sourced move/nature/item options with separate marginal evidence.
- Ten-candidate bounded search and full-set deduplication.
- Contextual scoring that avoids arbitrary rare-item ties and penalizes supported
  weather, terrain, seed and ally-hit conflicts.
- Independent full-team Showdown legality and refusal of invalid output.
- Actual level-50 stats and EV/nature descriptions without unverified benchmarks.
- Conditional Speed examples and explanations of Tailwind, Unburden and Trick Room.
- Concrete possible lead actions, back-pair rationale and four-of-six cautions.
- Genuine H-MEM persistence and deterministic enforcement of avoidance.
- Escaped HTML reports, structured JSON, Showdown export, trace-based progress
  and a project dashboard.
- A source-only public repository with setup, operational and architecture guides.

## Suggested walkthrough

1. Start `python app.py`, open the local page and choose **Offline sample**.
2. Lock Charizard. Build and show that it remains on a six-member legal roster.
3. Inspect its moves, EVs and level-50 stats. Explain that historical popularity
   is evidence of usage, not proof that the complete generated set won battles.
4. Show Torkoal supplying sun for Solar Power, alongside the HP-loss trade-off and
   Choice-lock caution. The sample's first opening is conditional, not guaranteed.
5. Inspect the Speed table and member-specific scenarios. Trick Room reverses
   order within priority brackets; it does not increase a Pokémon's Speed stat.
6. Show one possible group of four and its cautions. No opponent team has been
   supplied, so this is a practice plan rather than matchup solving.
7. Download `team.txt` and show the structured report/decision trace.
8. Optionally demonstrate the separate CLI memory example below.

Use a dedicated CLI profile for demonstrations so existing GUI preferences do
not influence the result:

```powershell
python team.py --sample --favourites Charizard --avoid-partner Incineroar --profile demo-memory
python team.py --sample --profile demo-memory
python team.py --sample --allow-all-partners --profile demo-memory
```

The second process recalls the first favourite and avoidance without repeating
them. The last explicitly clears the avoidance. Private generated files remain
local and are not part of the public example.

## Constraint examples

Three favourites:

```powershell
python team.py --sample --favourites Charizard Venusaur Blastoise --profile demo-three
```

The roster preserves all three. The report can explain that sun supports some
members while reducing ordinary Water-move damage; a lock is not an endorsement
of perfect synergy.

Six deliberately conflicting favourites:

```powershell
python team.py --sample --favourites Charizard Torkoal Pelipper Sneasler Indeedee-F Rillaboom --profile demo-six
```

The six species remain fixed. Expect competing weather/terrain and priority
cautions. These are strategic conditions, not necessarily legality failures.

`Miraidon`, `Flutter Mane` and Mega Charizard forms are examples rejected by this
historical Regulation H scope. Unsupported or misspelled names should produce
an error rather than invented moves.

## Verification and remaining work

73 application tests, 13/13 H-MEM conformance checks, full local Zetaris/sample
catalogue equality and connected end-to-end execution passed. The GUI HTTP
form/report/progress workflow passed. No visual browser test is claimed.

Demo 1 has no damage/turn simulation, optimized IVs, opponent-aware team preview,
current-2026 rules support, official tournament result corpus or guaranteed best
team. Its main flow is not yet a Nightshift-powered LLM feature. The prior
successful Nemotron experiment and later routing failure are historical work,
not proof that this milestone meets all event requirements.

The video, slide deck and final event submission remain future work. See
[roadmap](ROADMAP.md) and [submission preparation](../SUBMISSION-DRAFT.md).
