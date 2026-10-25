# Real live weather-goal adaptation

Run `1c3663366e604c65b102de197a53cb09`, 25 October 2026: actual Zetaris,
H-MEM and `nvidia/nemotron-3.5-lightning-30b-a3b` through Nightshift. The user
locked Charizard, avoided Incineroar and requested exploration of a rain mode.

The local candidate did not support automatic rain. The real Critic required a
change for `missing_mode_rain`. The Planner searched real weather-partner data,
selected Pelipper and called the bounded local builder with that partner. The
changed legal team contains Pelipper/Drizzle, Archaludon, Basculegion, Amoonguss,
Porygon2 and the locked Charizard. New evidence resolves the named objective;
the Planner submits a rain plan and the Critic approves with the remaining
cautions. Independent full-team validation passes.

Six real requests, one revision round, no continuation, approximately 249 seconds.
The AI chose the partner; the local algorithm selected prepared sets and filled
the other slots. This does not mean the model independently optimized every set.
The report explicitly warns that rain weakens Fire attacks and does not activate
Charizard's Solar Power. Supported rain is not proof of an ideal competitive team.

Previous failed rain iterations remain in the acceptance summaries. This small
passing case is not a provider reliability or win-rate estimate. No response,
partner choice or final verdict was scripted in this live evaluation.

`report.html`, `report.json`, `team.txt` and `trace.jsonl` retain actual outcomes,
decisions, counters and times. Only synthetic memory labels/record IDs were
removed or replaced. No settings, keys, private reasoning or owner history appear.

Reproduce with your own services, making genuine new model requests:

```powershell
python team.py --ai --favourites Charizard --avoid-partner Incineroar --objective rain --profile rain-example
```
