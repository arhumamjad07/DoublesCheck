# Data and rules

## One historical format

Demo 1 uses Scarlet/Violet VGC Regulation H and November 2024 ladder statistics.
All recommendations belong to this scoped snapshot. The app does not transfer
teams from another year into the selected format or certify current-event rules.

| Source | Role | Pinned identity |
| --- | --- | --- |
| [Pokémon Showdown](https://github.com/smogon/pokemon-showdown) | Dex, types, moves, abilities, items, stat reference and local validator | npm `pokemon-showdown@0.11.11`, MIT |
| [Historical Showdown rules](https://github.com/smogon/pokemon-showdown/blob/9fa4647eb5967fe59a0d18ec63f5b23f6e231cff/config/formats.ts) | Historical Regulation H format definition | commit `9fa4647eb5967fe59a0d18ec63f5b23f6e231cff` |
| [Smogon November 2024 aggregate](https://www.smogon.com/stats/2024-11/chaos/gen9vgc2024regh-1500.json) | Weighted usage, teammate associations and marginal set choices | `gen9vgc2024regh`, 1500 cutoff; SHA-256 in the manifest |
| [Official Regulation H announcement](https://sv-news.pokemon.co.jp/en/page/245.html) | Official historical context | Linked in the source manifest and reports |

The source archive reports **965,304 ladder battles**. This project has not
downloaded those individual battles or millions of replays. It has not ingested
official championship results, videos or a live PokéAPI service.

## Snapshot inventory

- 1,417 species/form records; these are not 1,417 unique Pokédex species.
- 358 historical usage rows.
- 357 species/forms with at least one generated, individually validated option.
- 11,376 build options in schema 2.
- 18 ordinary attack types. Tera decisions and Stellar effects are not simulated.

Unsupported species can exist in the Dex while having no usable build in this
snapshot. They are not assigned invented moves or exposed as supported automatic
choices. The full-team validator is run again after set selection.

## How candidate sets are generated

`showdown-bridge.cjs` derives options from separate marginal distributions:

1. Keep the most reported ability and, when sufficiently represented, a second.
2. Keep the top reported nature/EV spread and a sufficiently represented spread
   with a different nature when available.
3. Consider ranked item choices and up to twelve ranked source moves.
4. Retain distinct move combinations, including protection and alternatives to
   ally-hitting moves when available. Filter status moves from the generated
   Choice/Assault Vest options.
5. Combine the options with a sourced Tera type, level 50 and default 31 IVs.
6. Validate each candidate set against the scoped Showdown rules.

Item, ability and move shares are separate historical rates. Spread shares are
among reported spreads. Their combination is **not a jointly observed complete
set**. The rates do not prove compatibility, optimality, causation or a win rate.
The builder adds explicit usability and team-context checks after generation.

EVs are sourced investments. Explaining the resulting stats does not establish
that a spread survives a particular attack or secures a knockout. All-31 IVs are
defaults, including Speed and Attack where a specialized build may prefer less.

## Zetaris representation

The preserved Demo 3 `DOUBLES_CHECK` database contains:

| Table | Rows | Contents |
| --- | --- | --- |
| `pokedex` | 1,417 | Name and encoded species/type/stat records |
| `vgc_usage` | 358 | Name and encoded usage, teammate and set-option records |
| `reference` | 1 | Format, move/item/ability descriptions and snapshot metadata |

The application retrieves a real `LEFT JOIN` of `pokedex` and `vgc_usage`, then
the reference row. It checks record count, identifiers, format and schema before
reconstructing the catalogue. Base64 is an encoding used to transport structured
public records through CSV; it is not encryption.

Full connected/sample equality was verified locally for Demo 1. The runtime
adapter's structural checks do not constitute a cryptographic verification of
every live database value on every request.

The submission upgrade supplements these tables with five queryable tables in
`DOUBLES_CHECK_LENS`. It does not replace or expand the underlying source snapshot.
The connected builder now uses a favourite-specific SQL shortlist for automatic
partner slots. See [Evidence Lens](ZETARIS_EVIDENCE_LENS.md) for table grains, hashes,
registration and precise validation boundaries. Offline mode preserves the original
builder, so default team outputs across modes need not be identical.

## Reproduce and refresh

```powershell
python refresh-data.py
python register-data.py --compose-dir C:/zetaris-platform
python zetaris_schema.py
python register-evidence.py --compose-dir C:/zetaris-platform
```

The refresh script downloads only the pinned public aggregate, checks its expected
SHA-256, regenerates the catalogue with the pinned Showdown dependency and prepares
the CSVs/manifest. A different upstream hash stops the process for review rather
than silently accepting new data. Registration then refreshes DoublesCheck's
dedicated local files; it does not drop unrelated datasets.

`usage-original.json` is a reproducible intermediate and is excluded from Git.
Prepared public snapshots are committed so an offline sample can run without
downloading external data. `data/sources.json` records hashes for the prepared
files. Git attributes preserve those bytes across checkouts.

## Interpretation and rights

Original-type weakness tables ignore Tera, items, abilities, weather and terrain.
A resistant teammate does not automatically intercept an attack aimed at its
ally. Separately supported interaction warnings have narrower explicit scopes.

Third-party data remains attributable to its owners. This project does not claim
ownership or grant broader data/franchise rights. See
[third-party notices](../THIRD-PARTY-NOTICES.md).
