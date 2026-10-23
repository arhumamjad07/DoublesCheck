# Security and private information

DoublesCheck Demo 1 is a local prototype. Keep it bound to loopback and do not
expose it through port forwarding, public hosting or a tunnel without a separate
security design and review. The app is not an authenticated multi-user service.

## Credentials and local data

Keep real Zetaris/Nightshift tokens only in local settings. `.env.example`
contains placeholders. `.env`, local profiles, audit memory, user runs, logs,
backups, virtual environments and dependencies are excluded from Git.

The public sample is deliberately generated from public catalogue data in an
isolated profile. It is not an export of the owner's memory or conversation.
Public base64-encoded dataset records are structured public Pokémon data, not a
place to hide credentials. Base64 provides no secrecy.

Before sharing a report, inspect its JSON and trace as well as the HTML. Local
traces can include profile names, preferences and memory identifiers. Local memory
is stored as plain files, not encrypted credentials or a secure personal vault.

Do not paste keys, passwords, `.env` contents or private logs into public issues.
If a secret is accidentally exposed, revoke/rotate it with the provider promptly;
removing a file in a later commit does not make the earlier value private again.

## Existing controls and limits

- GUI server binds to `127.0.0.1`, checks the Host header and requires a per-process
  local form token for builds.
- Requests have input-size and identifier restrictions; report text is escaped.
- Zetaris requests are restricted to loopback hosts, with redirects disabled.
- Node child processes receive an environment with token/key/password variables
  removed by the application adapters.
- The main app has no model transport path. Legacy transports are separately gated.
- Dependency versions/integrity and upstream source hashes are recorded.

These controls and passing tests are not an exhaustive security audit. Do not
weaken them to work around an installation or routing problem.

## Reporting a problem

For a non-sensitive defect, open a GitHub issue with a minimal sample-mode
reproduction and redacted output. For a sensitive vulnerability, use a private
maintainer contact channel available from the GitHub profile; do not publish the
exploit's private data or a credential in an issue. No response-time or production
support guarantee is provided for this prototype.
