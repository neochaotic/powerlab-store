# Curation criteria

This document is the source of truth for "what gets into the catalog". The validators in [`scripts/`](../scripts/) enforce most of it mechanically; the parts that need human judgement are reviewed at PR time.

Policy lineage:

- PowerLab core [ADR-0039](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0039-powerlab-native-curated-catalog.md) — security-first curated catalog (the "what"; the "where" moved to ADR-0041)
- PowerLab core [ADR-0041](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0041-powerlab-store-separate-repo.md) — split-out as independent product
- Maintainer principle: **smaller-and-safer beats larger-and-warned**

---

## Image source trust matrix

Every `image:` in every catalog compose file MUST resolve to a registry on the **allowed** list AND to an image path under that registry that we consider trustworthy.

### Allowed registries (default)

| Registry prefix | Why trusted |
|---|---|
| `docker.io/library/*` | Docker Official Images — curated by Docker Inc. |
| `ghcr.io/<verified-org>/*` | GHCR images from the upstream project's own org (verified = matches `upstream_repo` in `x-powerlab.source`) |
| `docker.io/<vendor>/<image>` | Docker Hub when `<vendor>` is the upstream maintainer org (e.g. `nextcloud/`, `jellyfin/`, `homeassistant/`) |
| `lscr.io/linuxserver/*` | LinuxServer.io — community-published with extra scrutiny required (see "LinuxServer caveat" below) |
| `quay.io/<verified>/*` | Quay images from a verified upstream |
| `registry.k8s.io/*` | Kubernetes ecosystem official |
| `gcr.io/distroless/*` | Google distroless base images |
| `mcr.microsoft.com/*` | Microsoft Container Registry |

### LinuxServer caveat

LinuxServer.io images are tolerated but require:

1. Audit the s6-overlay startup scripts in the upstream `linuxserver/docker-<app>` repo at a specific commit
2. Record findings in `x-powerlab.security.audit_notes` (e.g. "s6 init at commit abc123: runs `chown -R abc:abc /config`, no network fetches at startup, no `curl|sh` patterns")
3. Re-audit when the image tag changes (which happens on every release)

The reason for the higher bar: LinuxServer wraps every image with their s6-overlay which DOES run bash at container startup. That bash can do arbitrary things. We need an explicit per-app human review noting it's not doing anything dangerous.

### Rejected (do not submit)

| Pattern | Reason |
|---|---|
| `getumbrel/*` | Umbrel-runtime-coupled. The image only makes sense inside umbrelOS. |
| `bigbearcasaos/*`, `bigbear*` | Fork-and-modify pattern. The build script changes upstream behavior; what's in the image today may not be what's in it tomorrow at the same tag. |
| `<single-username>/<image>` on Docker Hub | If the username is one community member redistributing an upstream image, that's a supply-chain hop we don't accept. Find the upstream's own image. |
| ANY `image:` ending in `:latest` (no `@sha256:`) | Digest-pinning is the security model. `latest` is by definition unpinned. |
| `casaos*` images | CasaOS-runtime-coupled. |

### How to handle "upstream hasn't published anywhere we trust"

Don't submit. The right path:

1. Open an issue in the upstream project's GitHub asking them to publish to GHCR or Docker Official
2. Wait for them to do so
3. Then submit here

OR:

1. Use a known-trusted base image with the app installed via standard package manager (e.g. `python:3.12-slim` + the app installed via pip in the compose — but this is the exception, requires explicit audit notes, and usually only justified for tiny apps)

---

## Compose hardening rules

Enforced by [`scripts/check-safety.sh`](../scripts/check-safety.sh):

| Rejected | Why |
|---|---|
| `privileged: true` | Full host access. |
| `/var/run/docker.sock` mount | Container can launch arbitrary host containers. |
| `network_mode: host` | Bypasses network namespace; can sniff/spoof host LAN. |
| `pid: host` | Sees all host processes. |
| `ipc: host` | Can attach to host shared memory. |
| `cap_add: ALL` or `cap_add: SYS_ADMIN` | Kernel-equivalent privileges. |
| Bind mounts of `/etc`, `/var/lib`, `/usr`, `/root`, `/home`, `/boot`, `/sys`, `/proc` | Container can read host secrets / write host configs. |
| `env_file:` directive | Indirect bash-via-env-injection vector (env files have historically carried `exports.sh`-style content). |

### Allowed bind mounts

- `${POWERLAB_APP_DATA}/...` — the canonical per-app data path PowerLab manages
- `/DATA/PowerLabAppData/<app>/...` — production absolute path equivalent
- `/tmp/powerlab-data/...` — macOS dev mode equivalent
- Named volumes (no leading `/`)

Everything else triggers manual review.

---

## App-directory rules

Enforced by [`scripts/validate.py`](../scripts/validate.py):

| Rejected | Why |
|---|---|
| ANY `*.sh` file at ANY depth in `Apps/<id>/` | No bash from contributors lands in a curated app dir. Period. |
| `hooks/` directory | Same RCE class as `*.sh`; historical CasaOS/Umbrel pattern. |
| `exports.sh` | Same. |
| Missing `icon.svg` or `icon.png` | Every app must render a tile. |
| Icon > 100KB | UI responsiveness; if it's that big, it's wrong format. |
| Missing `description.md` | Every app must explain itself to operators. |
| Schema incomplete (`store_app_id` / `title` / `tagline` / `category` / `port_map` / `source` / `icon` / `security` missing) | UI can't render. See [`docs/schema.md`](schema.md). |

---

## Compose `command:` and `entrypoint:` rules

Enforced by [`scripts/validate.py`](../scripts/validate.py):

| Rejected | Why |
|---|---|
| `curl ... \| sh` or `curl ... \| bash` | Pipe-to-shell of remote content. Classic RCE vector. |
| `wget ... \| sh` / `... \| bash` | Same. |
| `bash -c '<inline>'`, `sh -c '<inline>'` | Inline shell execution. |
| `eval ...` | Indirect execution. |
| `echo '<base64>' \| base64 -d \| sh` | Obfuscated execution. |

| Allowed | Why |
|---|---|
| `command: ["postgres", "-c", "max_connections=200"]` | Direct CLI args to the image's entrypoint. |
| `command: serve --port 8080` | Same, shell-form. |
| `entrypoint: ["/app/myapp", "--config", "/data/conf"]` | Direct invocation. |

The rule of thumb: the value of `command:` / `entrypoint:` must be a direct invocation of the image's bundled binary OR its bundled scripts (the image author's, not a contributor's). It must NOT be a shell that does anything other than exec.

---

## App quality bar (judgement, not mechanical)

These are reviewed at PR time:

1. **Upstream is alive** — last release within ~18 months, issues responded to. Dead upstreams get rejected.
2. **Self-contained** — works without other apps installed. Apps that require an external Postgres+Redis+MinIO cluster don't fit a one-click catalog (yet).
3. **Sane defaults** — works out of the box without operator config. If first-run requires editing the compose, it doesn't belong in the curated set.
4. **Useful** — the catalog is for things people actually want. We don't add an app just to fill the count.

---

## Three upstream catalogs we DO look at

For inspiration only. **Never as ingestion.**

| Source | Use it for | Don't use it for |
|---|---|---|
| [umbrel-apps](https://github.com/getumbrel/umbrel-apps) | Discovering which self-hosted apps are popular this year | Their compose files (Umbrel-runtime-coupled, often have `hooks/` and `exports.sh`) |
| [CasaOS-AppStore](https://github.com/IceWhaleTech/CasaOS-AppStore) | Same | Their compose files (CasaOS-runtime-coupled) |
| [big-bear-casaos](https://github.com/bigbeartechworld/big-bear-casaos) | Same | Their images (`bigbearcasaos/*` rejected by registry policy) and compose files |

The workflow when inspired by one of these:

1. See app X in upstream catalog Y
2. Find the UPSTREAM project (not Y's fork) — usually a GitHub repo
3. Check if THE upstream publishes a trusted-registry image
4. If yes: author a NEW compose from scratch pointing at that image, with the `x-powerlab` block, and submit here
5. If no: skip the app — see "How to handle..." above

---

## Memory anchors

For agents working on this repo, the relevant memory entries are:

- `feedback_catalog_trust_policy` — this document's rules
- `feedback_security_is_priority` — parent principle
- `catalog_icons_rehosted_as_raw` — rehost policy for icons
- `project_powerlab_store_independent_product` — why this repo is its own product
- `project_enterprise_pivot` — why provenance auditability matters
