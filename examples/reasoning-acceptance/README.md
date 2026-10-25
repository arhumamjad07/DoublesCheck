# Recorded reasoning acceptance, 25 October 2026

These are actual saved summaries, not fabricated expected results. Each contains
its own implementation fingerprint and actual case IDs. The cases and checks
are defined in `reasoning_cases.py` and `evaluate_reasoning.py` at the repository
root. These development iterations are separate; do not combine them into a
claimed reliability rate. An expected refusal is not an approved AI team.

| Recorded suite | Passed | Failed | Skipped | Model requests | Live team approvals |
| --- | --- | --- | --- | --- | --- |
| [first-live-repair](first-live-repair.json) | 1 | 0 | 0 | 7 | 1 |
| [core-live-cases](core-live-cases.json) | 9 | 0 | 0 | 13 | 4 |
| [extended-live-cases](extended-live-cases.json) | 3 | 1 | 0 | 17 | 3 |
| [final-live-goals](final-live-goals.json) | 1 | 1 | 0 | 14 | 1 |
| [live-rain-after-guidance](live-rain-after-guidance.json) | 1 | 0 | 0 | 6 | 1 |
| [offline-cases](offline-cases.json) | 12 | 0 | 1 | 0 | 0 |

The core suite includes four real approved reviews and five correct input
refusals with zero model requests. The extended suite includes a real repair,
an observed H-MEM preference changing the team, retained conflicting favourites,
and a rain case withheld after provider interruptions. Failed attempts remain
visible in the JSON. Offline checks make zero model requests; rain is skipped
there because it requires an AI objective decision.

The later rain run passed after weather-tool guidance was clarified: six real
requests, a source-backed Pelipper choice, a changed team and approved rain
support. It retains and discloses Charizard's rain trade-off. It is a separate
iteration, not a replacement for the recorded failures.

Full sanitized live examples: [named repair](../reasoning-repair/README.md) and
[interrupted review with continuation](../reasoning-recovery/README.md).
[Live weather adaptation](../reasoning-rain/README.md) shows the later rain result.
Full local case reports and traces are saved under their run IDs in the app's
private, Git-ignored `runs` directory. These public summaries contain no owner
memory, settings, keys, prompts or private reasoning. Source teams are historical
Regulation H; acceptance does not establish competitive strength or user impact.

See [verification](../../VERIFICATION.md) and
[reasoning architecture](../../docs/REASONING_ACCEPTANCE.md) for scope and limits.
