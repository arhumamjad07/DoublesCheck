# Demo 4 release security audit

Review date: 27 October 2026. No confirmed credentials or confidential owner
information were detected in the reviewed history or exact Demo 4 release files.
This is a targeted scan, not a guarantee that every possible secret is detectable.

## Checks

- Refreshed remote heads/tags, then inspected all reachable Git contents and
  commit/tag metadata, including older file versions and previous demo milestones.
- Scanned the exact staged release against actual locally available service and
  GitHub credentials without printing their values, common token/private-key
  patterns, private owner contacts/paths and credential-bearing URLs.
- Confirmed `.env`, local memory, generated user runs, logs, editor settings,
  installed dependencies, archives and private audit helpers remain excluded.
- Decoded all 1,776 public base64 records and scanned their contents too.
- Independently scanned the full release and history with Gitleaks 8.30.1, then
  rescanned a copy preserving all decoded fields alongside the normalised tables.
- Verified the release-label changes affect documentation only. Application
  source and the pinned historical data remain the already-tested upgrade.

## Reviewed scanner matches

The raw history and release scans each flagged eight generic-key matches in
encoded public Pokemon CSV rows. Each complete row was decoded and checked as
an exact projection of the pinned catalogue. These are reviewed false positives,
not broad exclusions for data or test files. The independently scanned decoded
release had zero findings.

A separate pattern check verifies the deliberately fake credentials inside the
loopback URL-rejection test using its AST and rejection assertion. No real
credential value, private path or confidential owner contact was detected.

## Publication boundary

The committed release tree must match the scanned index. Commit and annotated
tag metadata are checked again before publishing `main` and `demo-4`. Existing
`demo-1`, `demo-2` and `demo-3` tags are preserved, including Demo 3 at
`acc708bf565d786e1d1d1bcde3903fe8229b7192`. No history rewrite or credential rotation
was indicated by these findings. Private scanner output remains outside Git.

See the [earlier milestone audit](SECURITY_AUDIT.md), [security policy](../SECURITY.md)
and [Demo 4 guide](DEMO_4.md).
