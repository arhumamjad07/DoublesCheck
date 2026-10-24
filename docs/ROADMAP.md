> The table retains Demo 1 context. A new explicit Nightshift/Nemotron reasoning
> loop is implemented locally; see [AI reasoning](AI_REASONING.md) and verification
> notes for its actual test/live status. Final usefulness/video/deck work remains.

# Vision, roadmap and hackathon alignment

## Intended product

A beginner-friendly VGC doubles coach that preserves favourite Pokémon, builds
or reviews a legal team, explains its reasoning and helps a player choose four
after seeing the opposing six. The proposed distinction is favourite-first,
inspectable coaching with memory and checked evidence, rather than an unexplained
list of six Pokémon. Differentiation and usefulness still need user validation.

## Demo 1 position

| Capability | State |
| --- | --- |
| One to six favourites, preserved species, filled slots | Working |
| Real historical data and explicit format | Working; one historical ruleset |
| Local Zetaris join | Working and checked against the bundled snapshot |
| Genuine H-MEM preference feature | Working and conformance-tested |
| Full-team legality checks | Working through the scoped Showdown validator |
| Roles, stats, EV explanations, conditional Speed and interaction cautions | Working within documented limits |
| Lead and four-of-six guidance | Conditional heuristic practice plans |
| Nightshift as the main product's AI provider | Bounded explicit AI extension implemented; see current live-verification evidence |
| Opponent-aware team preview, damage simulation, optimized IVs | Unfinished |
| Player usefulness study, final video/deck/submission | Unfinished |

## Next priorities

1. Review fixed builds and explanations with experienced VGC players and actual
   beginners. Record concrete failures; do not assume passing tests prove good
   competitive recommendations.
2. Complete live acceptance of the explicit Nightshift/Nemotron coach. The new
   Planner/tool/Critic loop is implemented and regression-tested; provider errors
   and incompatible responses must remain visible. See the verification log.
3. Evaluate whether model-selected changes and explanations improve actual player
   understanding. Keep legality and preference enforcement independent of approval.
   Do not infer a free NVIDIA quota from ChatGPT/Codex allowance resets.
4. Add opponent-aware team-preview guidance and meaningful damage/stat benchmarks
   with independently checked mechanics before claiming specific matchups.
5. Improve interface clarity through user feedback. Visual browser testing is
   still needed in addition to the HTTP checks.
6. Prepare the actual demo video, slides, sponsor evidence and event submission.
   Verify the latest organizer requirements before submitting.

New data sources, current rulesets and larger replay/tournament corpora should
follow a scoped need. Different formats and generations must not be mixed without
explicit labels and legality checks.

## Track and rubric

The project targets **Track 3: Reasoning Architecture**. Its local pipeline
already demonstrates data retrieval, memory, constrained planning, independent
validation and factual explanations. The intended final AI feature should build
on that foundation rather than rename deterministic code as LLM agents.

The weights below are from the supplied event overview. They are planning notes,
not awarded/predicted scores or a certification of current eligibility.

| Criterion | Weight | Evidence now | Remaining evidence |
| --- | --- | --- | --- |
| Impact | 30 | Concrete beginner team-building problem | User feedback and measured understanding/usefulness |
| Technical | 20 | Working data/memory/search/validator pipeline; tests and traces | Reliable main-product AI feature and deeper battle evaluation |
| Innovation | 15 | Favourite-preserving, inspectable coach concept | Demonstrated differentiation from existing builders |
| Demo | 15 | Runnable sample, export and walkthrough | Actual concise video and presentation |
| Product & UX | 10 | Local GUI, progress and readable reports | Visual review and beginner usability testing |
| Sponsor Tech | 10 | Zetaris and Meterless H-MEM working | Final Nightshift/Nemotron feature and truthful evidence |

## Sponsor boundaries

- **Zetaris:** real local SQL join across separate public Dex and usage records;
  the platform runs in the event-supplied Docker Compose installation.
- **Meterless H-MEM:** actual reference engine with provenance, retrieval,
  persistence, corrections and enforced preferences.
- **Nightshift/NVIDIA:** current GUI/CLI has an explicitly selected, bounded
  Planner/tool/Critic mode pinned to the approved Nemotron model. The verification
  log distinguishes live results from scripted regression evidence. Local and
  sample modes remain model-free.
- **Coding tool:** development used AI coding assistance. Cursor was optional
  under the supplied organizer update; no event-provided Cursor credits are assumed.

Public source and a documented prototype are milestone evidence, not a complete
hackathon submission. The event's organizers determine eligibility and scoring.
