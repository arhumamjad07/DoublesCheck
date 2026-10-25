# Demo 1/2 history and Demo 3 release audit

Review date: 25 October 2026. **No confirmed credentials or confidential owner
information were detected in the reviewed Git history and selected release.**
This is a targeted audit, not a guarantee that every possible secret is detectable.

## Scope

- Refreshed the public remote and confirmed the checkout is not shallow.
- Checked all reachable contents of the two published commits, including 119
  unique blobs, both commit objects and both annotated tag objects. Deleted/older
  file versions and commit/tag metadata were included.
- Preserved `demo-1` at `7bde7243efb52707d68ae0375b7fa51d07c1f695` and `demo-2`
  at `f743e2848b3038a1873465ca45c31f679c9af0fc`.
- Checked the selected Demo 3 source against actual local service/GitHub
  credentials without printing their values, common token/private-key patterns,
  private owner contacts/paths, credential-bearing URLs and excluded file paths.
- Decoded all 1,776 public base64 records; scanned their contents as well as
  source files. Public examples use synthetic preferences, not owner memory.
- Checked that `.env`, memory, generated runs, logs, local editor settings,
  dependency folders, archives and key files remain outside the release.
- Checked intended public GitHub identity separately from private email/contact
  information in commit metadata.

## Dedicated scanner and reviewed false positives

[Gitleaks](https://github.com/gitleaks/gitleaks) 8.30.1 was obtained from its
official release and its published SHA-256 checksum verified. History and release
scans used recursive decoding and full redaction; no finding values were printed.

The raw scans each flagged eight generic-key candidates in Pokémon CSV data.
Each complete two-field record was decoded and verified as an exact projection
of the public catalogue. Some species names end in “key”, causing a generic
assignment rule to interpret the following encoded CSV field as a credential.
These are reviewed false positives, not ignored real credentials. A further
scan preserving every decoded field reported no leaks.

A separate URL-pattern check found the deliberately fake loopback credentials
inside a test that verifies rejection of credential-bearing URLs. Its location,
placeholder values and rejection assertion were verified through Python's AST.
No broad exclusion for test files or data folders was applied.

## Publication boundary

The final staged source is rechecked before commit; the resulting commit tree
must match the scanned tree. Only the new main commit and `demo-3` tag are pushed.
Earlier release tags are preserved. Audit helpers, scanner binaries and local
scan reports are kept outside the repository. No history rewrite or credential
rotation was necessary based on these findings.

If a real secret is discovered later, follow [SECURITY.md](../SECURITY.md): rotate
it promptly and address the historical exposure, rather than merely deleting it
in a later commit.
