# Security policy

## Scope: this repo (`powerlab-store`)

This repository ships:

- Compose YAML files for self-hostable apps (`Apps/<id>/docker-compose.yml`)
- Per-app icons and descriptions
- Validation scripts (`scripts/validate.py`, `scripts/check-safety.sh`, etc.)
- CI workflows

**Vulnerabilities relevant here**:

- An app's `docker-compose.yml` requests an unsafe capability we didn't catch (e.g. a `cap_add` that escapes the container, a bind-mount path that leaks host data, an unpinned image we forgot to digest-pin)
- An app's pinned image, while pinned correctly, points to a known-vulnerable upstream release
- A validation script has a bypass that lets a malicious PR slip through CI
- A workflow misconfiguration grants excessive `GITHUB_TOKEN` scopes

**File these here** — see "How to report" below.

## Out of scope (file at PowerLab core)

If the vulnerability is in:

- The PowerLab gateway, install path, JWT/auth, sync-catalog parser, app-management orchestration
- The PowerLab UI rendering of catalog tiles
- The bundled install scripts (`install.sh`, `install-mac.sh`)
- The `x-powerlab` schema parser itself

File at [github.com/neochaotic/powerlab → SECURITY.md](https://github.com/neochaotic/powerlab/blob/main/SECURITY.md) instead. That codebase has its own disclosure flow.

## How to report

**Do NOT file public GitHub issues for security vulnerabilities.**

Email the maintainer (address on the [maintainer's GitHub profile](https://github.com/neochaotic)) with subject line `[powerlab-store security]` and include:

- Affected app (`Apps/<id>`) or script
- What the issue is (capability escape, image with CVE, validator bypass, etc.)
- Proof-of-concept if available
- Suggested mitigation if you have one

Expect a first response within 7 days. We disclose via a coordinated process: fix is committed + released, then the vulnerability is described in a GitHub Security Advisory.

## Hardening posture

This catalog enforces, on every PR, via [`scripts/validate.py`](scripts/validate.py) and [`scripts/check-safety.sh`](scripts/check-safety.sh):

- No `hooks/` directory, no `exports.sh`, no `*.sh` file anywhere in `Apps/<id>/`
- No `privileged: true`, no `docker.sock` mount, no `network_mode: host`, no `ipc: host`, no `pid: host`, no `cap_add: ALL|SYS_ADMIN`
- No `env_file:` directives, no unrewritten upstream volume paths (`/DATA/AppData`, `$AppID`)
- No images from `getumbrel/*` or `bigbear*/` (runtime-coupled or fork-derived)
- Every `image:` MUST be digest-pinned (`@sha256:...`)
- Every app MUST ship an icon ≤ 100KB

See [`docs/curation-criteria.md`](docs/curation-criteria.md) for the full policy and rationale.

## Related

- PowerLab core [ADR-0039](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0039-powerlab-native-curated-catalog.md) — security-first curation rationale
- PowerLab core [ADR-0041](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0041-powerlab-store-separate-repo.md) — why this is a separate repo
