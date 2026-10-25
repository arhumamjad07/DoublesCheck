# Real live Critic → Planner → Critic repair

This is deliberate evaluation `9e375830601240a5a2ea5d590bb2e9cd`, 25 October
2026. The historically legal input contains a sourced Sneasler Psychic Seed /
Unburden set without an automatic Psychic Terrain setter. It is a declared
synthetic fixture, not an owner team or a spontaneous default-builder failure.

The user objective is to repair unsupported item/weather plans while keeping
Charizard and Sneasler and avoiding Incineroar. No model answer is scripted.

The actual `nvidia/nemotron-3.5-lightning-30b-a3b` model:

1. Requested inspection as the Critic.
2. Required a change to the named missing-seed-terrain issue.
3. Investigated prepared alternatives as the Planner.
4. Selected Focus Sash + Poison Touch for Sneasler.
5. Requested inspection of the changed version and submitted it.
6. Approved the new version as the Critic after local checks.

Seven model requests, one Critic revision round, one actual set mutation, no
continuation in this run. Approximately 271 seconds including local work.
The named condition was independently checked as absent in version 2 and the
full team passed the historical validator. This does not establish competitive
strength or a provider reliability guarantee. Other failed iterations are recorded
in the root verification log.

`input-team.json` was reconstructed from the actual recorded before/after set
changes and checked against the original input fingerprint. The team/report/trace
retain actual decisions, model identities, counters and event times. Only the
synthetic memory profile and record identifiers were replaced/removed. No prompts,
private reasoning, settings, keys, owner memory or personal run history are shared.

Open `report.html` locally. `report.json`, `team.txt` and `trace.jsonl` provide the
structured result, Showdown export and decision audit.

To reproduce with your own local services and runtime token:

```powershell
python team.py --ai --favourites Charizard Sneasler --avoid-partner Incineroar --objective reliable --review-team examples/reasoning-repair/input-team.json --profile repair-example
```

That command makes genuine new requests; it does not replay this saved answer.
The CLI accepts exact prepared source sets, not arbitrary imported builds.
