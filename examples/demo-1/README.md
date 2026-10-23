# Public Demo 1 example

This example was deliberately generated from the bundled public historical
catalogue with Charizard as the only locked favourite. It uses a new
`public-demo-1` profile in temporary memory storage. It is not copied from an
existing user's profile, private runs or `.env`.

| File | Purpose |
| --- | --- |
| `report.html` | Portable report; download the repository and open locally |
| `report.json` | Structured team, explanations, source references and limitations |
| `team.txt` | Pokémon Showdown import/export text |
| `trace.jsonl` | Actual events from this deliberately public fixture run |

The reported memory IDs and timestamps belong only to this public fixture.
The code made zero cloud model calls. Its stored result passed the local
historical Regulation H full-team validator.

The resulting six are Charizard, Electabuzz, Rillaboom, Torkoal, Gallade and
Maushold. This is a legal heuristic example, not a claim that these six constitute
the strongest possible competitive team.

To reproduce the behaviour in a fresh profile:

```powershell
python team.py --sample --favourites Charizard --profile public-example
```

Run IDs, timestamps and memory IDs naturally differ. Existing saved preferences
can also affect a reused profile, so use a fresh profile for comparisons.

HTML links to the adjacent JSON, trace and team files work after download. The
"Build another team" link expects a separately running local app on port 8765;
the public repository itself does not host a running application.
