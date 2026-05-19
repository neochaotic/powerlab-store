# PowerLab Store

> **A curated, security-vetted catalog of self-hostable apps.** Independent product, designed to integrate cleanly with [PowerLab](https://github.com/neochaotic/powerlab) — and usable by any compatible runtime that speaks the `x-powerlab` schema.

[![License: AGPL-3.0](https://img.shields.io/badge/code%20license-AGPL--3.0-blue.svg)](LICENSE)
[![Content License: CC-BY-SA-4.0](https://img.shields.io/badge/content%20license-CC--BY--SA--4.0-lightgrey.svg)](LICENSE-CONTENT)
[![Schema](https://img.shields.io/badge/schema-x--powerlab-purple.svg)](docs/schema.md)
[![PowerLab](https://img.shields.io/badge/built%20for-PowerLab-emerald.svg)](https://github.com/neochaotic/powerlab)

---

## What this is

A small, hand-curated registry of self-hostable apps distributed as an independent product. Versioned on its own track. Released on its own cadence. Integrates with the [PowerLab](https://github.com/neochaotic/powerlab) panel through a documented compatibility protocol — and is structured so any other runtime that understands the `x-powerlab` schema (see [`docs/schema.md`](docs/schema.md)) can consume it without modification.

Every app in this catalog:

- **Ships as a single `docker-compose.yml`** with a `x-powerlab` extension block carrying metadata (title, category, port mapping, security audit trail, provenance)
- **Passes a strict security gate before merging** — no `hooks/`, no `exports.sh`, no `env_file`, no `privileged: true`, no `docker.sock` mount, no `network_mode: host`, no `ipc:host`, no `pid:host`, no `cap_add: ALL|SYS_ADMIN`, no `getumbrel/*` image
- **Pins its image to an immutable `@sha256:` digest** so supply-chain drift is impossible
- **Carries a self-hosted icon** (we don't hot-link to upstream CDNs)

This catalog is consumed by PowerLab in one of two integration modes:

| Mode | When | How |
|---|---|---|
| **Bundled** (PowerLab default) | Fresh PowerLab installs, air-gapped operators | PowerLab fetches the latest release tarball at build time |
| **External** (PowerLab operator opt-in) | Bleeding-edge catalog OR an operator's private fork | PowerLab `Settings → Catalog → Use external store URL` + periodic polling |

Other runtimes consume releases the same way: download the published `powerlab-store-vX.Y.Z.tar.gz`, read `index.json`, render apps using the `x-powerlab` block in each `docker-compose.yml`. No PowerLab-specific dependency required.

> **End users — don't clone this repo.** Install [PowerLab](https://github.com/neochaotic/powerlab) (or another compatible runtime) and the catalog comes with it. This repo is for **app maintainers**, **catalog contributors**, and **operators running private forks or alternative runtimes**.

---

## Quick links

| If you want to… | Go to… |
|---|---|
| **Install PowerLab** + use the apps | [neochaotic/powerlab](https://github.com/neochaotic/powerlab) → README |
| **Add a new app** to the store | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| Understand the **`x-powerlab` schema** | [`docs/schema.md`](docs/schema.md) |
| Read the **curation criteria** (what's accepted, what's rejected) | [`docs/curation-criteria.md`](docs/curation-criteria.md) |
| Learn the **icon style guide** | [`docs/icon-guidelines.md`](docs/icon-guidelines.md) |
| Report a **vulnerability** in a catalog app | [`SECURITY.md`](SECURITY.md) |
| Understand **why this is a separate repo** | PowerLab core [ADR-0041](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0041-powerlab-store-separate-repo.md) |
| See the **architectural intent** behind curation | PowerLab core [ADR-0039](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0039-powerlab-native-curated-catalog.md) + [ADR-0040](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0040-proportional-engineering-hygiene-baseline.md) |
| Read the **store's own ADRs** | [`docs/adr/`](docs/adr/) |

---

## Repo layout

```
powerlab-store/
├── README.md                     # you are here
├── LICENSE                       # AGPL-3.0 (code + compose)
├── LICENSE-CONTENT               # CC-BY-SA-4.0 (prose + icons + docs)
├── CONTRIBUTING.md               # app submission manual
├── SECURITY.md                   # vulnerability disclosure
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md                  # per-release notes
├── docs/
│   ├── schema.md                 # x-powerlab spec
│   ├── curation-criteria.md      # what we accept / reject
│   ├── icon-guidelines.md        # SVG style, size, attribution
│   └── adr/                      # store-specific architectural decisions
├── Apps/
│   └── <app-id>/
│       ├── docker-compose.yml    # compose + x-powerlab block, digest-pinned
│       ├── icon.svg              # rehosted, ≤ 100KB
│       └── description.md        # long-form description (operator-facing)
├── scripts/
│   ├── validate.py               # schema + safety gate (runs on every PR)
│   ├── check-safety.sh           # mirror of PowerLab core's safety lint
│   ├── pin-digests.sh            # resolves image:tag → image:tag@sha256
│   └── build-index.sh            # emits index.json + tarball on release
├── .github/
│   ├── workflows/
│   │   ├── validate.yml          # all gates on every PR
│   │   ├── release.yml           # tag → tarball + index.json release asset
│   │   └── icon-lint.yml         # SVG/PNG sanity + size cap
│   ├── ISSUE_TEMPLATE/
│   │   ├── new-app.md
│   │   └── app-bug.md
│   └── PULL_REQUEST_TEMPLATE.md
└── index.json                    # autogenerated catalog manifest
```

---

## Security posture (enforced, not aspirational)

| Check | Where it fails | Source |
|---|---|---|
| `hooks/` dir present | `scripts/validate.py` | Catalog must not execute upstream bash. PowerLab core PR [#441](https://github.com/neochaotic/powerlab/pull/441) blocks at sync; we block at submission. |
| `exports.sh` file present | `scripts/validate.py` | Same RCE class. |
| `env_file:` directive | `scripts/validate.py` | Indirect bash-via-env-injection vector. |
| `privileged: true` | `scripts/check-safety.sh` | Mirrors PowerLab core PR [#447](https://github.com/neochaotic/powerlab/pull/447). |
| `docker.sock` mount | `scripts/check-safety.sh` | Container can spawn arbitrary host containers. |
| `network_mode: host` | `scripts/check-safety.sh` | Bypasses network namespace. |
| `ipc: host` | `scripts/check-safety.sh` | Bypasses IPC namespace (memory bus access). |
| `pid: host` | `scripts/check-safety.sh` | Process namespace bypass. |
| `cap_add: ALL` / `SYS_ADMIN` | `scripts/check-safety.sh` | Capability escalation. |
| `getumbrel/*` image | `scripts/validate.py` | Runtime-coupled to Umbrel infra. We require independent images. |
| Unrewritten upstream volume paths (`/DATA/AppData`, `$AppID`) | `scripts/validate.py` | Indicates a partial import that won't work on PowerLab. |
| `image:` without `@sha256:` digest | `scripts/validate.py` (strict day 1) | Supply-chain drift prevention. Memory anchor `feedback_security_is_priority`. |
| Missing `icon.svg` / `icon.png` | `.github/workflows/icon-lint.yml` | Operators expect every app to render a tile. |
| Schema completeness (`x-powerlab.{store_app_id,title,tagline,category,port_map,source,icon,security}`) | `scripts/validate.py` | Required for PowerLab UI rendering. |

**No warn-only ratchets.** Unlike PowerLab core's lint + govuln gates ([ADR-0040](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0040-proportional-engineering-hygiene-baseline.md)) which started warn-only because the legacy codebase carried unpinned debt, this store starts **strict from day 1** because it starts clean.

---

## How a release works

1. Maintainer (or contributor via PR) lands changes on `main`
2. Maintainer runs `./scripts/cut-release.sh <X.Y.Z>` (vendored from PowerLab core's pattern — see [`feedback_always_run_prepare_release_before_tag`](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0041-powerlab-store-separate-repo.md#cross-reference-strategy))
3. `git push origin v<X.Y.Z>` triggers `.github/workflows/release.yml`
4. CI:
   - Runs all gates one last time
   - Generates `index.json` (catalog manifest with sha256 of every compose file)
   - Packs `Apps/`, `icons/`, `index.json` into `powerlab-store-v<X.Y.Z>.tar.gz`
   - Publishes GitHub release with the tarball + a `latest.json` manifest pointer
5. PowerLab core's next build picks up the release in bundled mode

Operators running **external mode** poll `index.json` periodically and see "Catalog update available" in PowerLab Settings → Catalog independent of PowerLab core upgrades.

---

## Compat with PowerLab core

This repo's releases declare a `min_powerlab_version` in `index.json`. PowerLab core releases declare a `compatible_store_version_range` in their `manifest.json`. Mismatch surfaces a clear "store too new / too old for this PowerLab" warning, never an opaque install error.

The full contract lives in [ADR-0041](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0041-powerlab-store-separate-repo.md#contract-with-powerlab-core).

---

## Status

| | |
|---|---|
| **Version track** | independent — first release tagged `v0.1.0` |
| **Current phase** | 0 — bootstrap (this README, LICENSE, CONTRIBUTING, scripts/, workflows/) |
| **Apps available** | 0 — `v0.1.0` ships with a single reference app to validate the pipeline |
| **Roadmap** | import the 138 vetted apps from the 2026-05-19 curation pipeline (less `openwebui` — rejected for `ipc:host`) |

The full migration plan lives in PowerLab core [ADR-0041](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0041-powerlab-store-separate-repo.md) (that ADR is a **core** decision — to split the catalog out — and stays in core). Store-specific architectural decisions (schema changes, format changes, contract revisions) will land in [`docs/adr/`](docs/adr/) here.

---

## License

This repo uses a **hybrid licensing model** ([rationale in ADR-0041 § Licensing](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0041-powerlab-store-separate-repo.md#licensing)):

| Surface | License |
|---|---|
| `scripts/` (validate.py, pin-digests.sh, build-index.sh) | **AGPL-3.0** ([LICENSE](LICENSE)) |
| `Apps/<id>/docker-compose.yml` | **AGPL-3.0** (configuration coupled to PowerLab core) ([LICENSE](LICENSE)) |
| `Apps/<id>/description.md` | **CC-BY-SA-4.0** (prose) ([LICENSE-CONTENT](LICENSE-CONTENT)) |
| `Apps/<id>/icon.svg` / `icon.png` | **CC-BY-SA-4.0** by default; upstream icons retain their original license, recorded per app in `x-powerlab.icon.license` ([LICENSE-CONTENT](LICENSE-CONTENT)) |
| `docs/` | **CC-BY-SA-4.0** ([LICENSE-CONTENT](LICENSE-CONTENT)) |
| `index.json` | **AGPL-3.0** (generated, derives from `Apps/`) ([LICENSE](LICENSE)) |

Reference pattern: Kubernetes ecosystem (code Apache-2.0, docs CC-BY-4.0, assets per-creator) — adapted to PowerLab's AGPL stack.

---

## Companion repos

- 🚀 **PowerLab core**: [neochaotic/powerlab](https://github.com/neochaotic/powerlab)
- 📦 **PowerLab Store** (you are here): [neochaotic/powerlab-store](https://github.com/neochaotic/powerlab-store)
- 📋 **Issue tracker**: app bugs + new-app requests live here; PowerLab core bugs (installer, gateway, UI shell) live in [the core tracker](https://github.com/neochaotic/powerlab/issues)
