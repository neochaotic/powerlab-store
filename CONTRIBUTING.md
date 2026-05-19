# Contributing to PowerLab Store

Thanks for considering a contribution. This repo is the curated app catalog consumed by [PowerLab](https://github.com/neochaotic/powerlab) (and any other compatible runtime). It is an **independent product** on its own version cadence — separate from PowerLab core.

Three things to read first:

1. [`docs/schema.md`](docs/schema.md) — the `x-powerlab` block your `docker-compose.yml` MUST carry
2. [`docs/curation-criteria.md`](docs/curation-criteria.md) — what's accepted, what's rejected, and **why**
3. [`docs/icon-guidelines.md`](docs/icon-guidelines.md) — icon size, format, attribution

## Two kinds of contribution

| | What it is | Where it lives |
|---|---|---|
| **Add an app** | A new `Apps/<id>/` directory with `docker-compose.yml` + `icon.svg`/`png` + `description.md` | This repo |
| **Catalog tooling / docs** | Changes to `scripts/`, `docs/`, `.github/`, validators, workflows | This repo |

Bug in PowerLab core (gateway, install path, UI shell, schema parser) → file at [github.com/neochaotic/powerlab/issues](https://github.com/neochaotic/powerlab/issues), not here.

---

## Adding an app — the 7-step path

### 1. Confirm the upstream image is from a trusted source

Trusted registries (default-allow):

- ✅ `docker.io/library/<name>` — Docker Official Images
- ✅ `ghcr.io/<verified-org>/...` — GitHub Container Registry, when the org IS the upstream project (not a third-party fork)
- ✅ Docker Hub `<vendor>/<image>` where `<vendor>` IS the upstream maintainer (e.g. `nextcloud/all-in-one`, `jellyfin/jellyfin`, `homeassistant/home-assistant`)
- ✅ `lscr.io/linuxserver/*` — LinuxServer.io community images, accepted with extra scrutiny (audit their s6-overlay use per-app, note findings in `x-powerlab.security.audit_notes`)
- ✅ `quay.io/<verified>`, `registry.k8s.io/*`, `gcr.io/distroless/*`, `mcr.microsoft.com/*`

Rejected on submission (do not bother opening a PR):

- ❌ `getumbrel/*` — Umbrel-runtime-coupled, no independent upstream
- ❌ `bigbearcasaos/*`, `bigbear*` — fork-and-modify pattern, the build can change underneath us
- ❌ `<single-username>/<image>` on Docker Hub where the username is one community member, not the upstream project
- ❌ ANY image with the `latest` tag — digest-pinning is the security model

If your app's upstream maintainer hasn't published an image to a trusted registry yet, the answer is "not yet" — the right path is to ask the upstream project to publish to GHCR or Docker Official, not to submit a third-party-built image here.

### 2. Confirm there are no `.sh` files in the app dir

Hard rule: **zero** `.sh` files anywhere under `Apps/<id>/`. Not `hooks/pre-start.sh`, not `exports.sh`, not `setup.sh`, not `post-install.sh`. If the upstream needs a shell script to initialise, it doesn't belong in the catalog — that's an RCE class we don't accept ([feedback memory anchor](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0039-powerlab-native-curated-catalog.md)). The compose `command:` and `entrypoint:` keys can pass inline CLI flags to the image; they CANNOT contain `curl | sh`, `wget | sh`, `bash -c '<inline>'`, or any pipe-to-shell pattern.

### 3. Create the app directory

```
Apps/<store-app-id>/
├── docker-compose.yml         # required
├── icon.svg                   # required, ≤ 100KB (icon.png also acceptable)
└── description.md             # required, long-form description (operator-facing)
```

`<store-app-id>` is kebab-case, lowercase, no spaces. It MUST match the `x-powerlab.store_app_id` field in the compose file.

### 4. Author the compose file

Start from this skeleton and adapt:

```yaml
services:
  app:
    image: nextcloud/all-in-one@sha256:<resolve-with-scripts/pin-digests.sh>
    container_name: ${POWERLAB_APP_NAME}
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - ${POWERLAB_APP_DATA}/data:/data

x-powerlab:
  store_app_id: nextcloud
  title: Nextcloud
  tagline: Your private cloud, in one container
  category: Files & Sync
  port_map:
    - container: 80
      host: 8080
      protocol: http
  source:
    registry: docker.io
    image: nextcloud/all-in-one
    upstream_homepage: https://nextcloud.com
    upstream_repo: https://github.com/nextcloud/all-in-one
  icon:
    file: icon.svg
    license: CC-BY-SA-4.0   # or upstream original — record their license
    attribution: Nextcloud GmbH
  security:
    image_pin: pinned       # set by scripts/pin-digests.sh
    audit_notes: |
      Runs as non-root by default. Mounts a single data volume.
      No host capabilities granted.
```

Full schema reference: [`docs/schema.md`](docs/schema.md).

### 5. Pin the digest

Run from the repo root:

```bash
./scripts/pin-digests.sh Apps/<store-app-id>/
```

This resolves every `image: foo:tag` to `image: foo:tag@sha256:<digest>` and rewrites the file in place. CI **will reject** unpinned images.

### 6. Run validators locally

```bash
./scripts/validate.py Apps/
./scripts/check-safety.sh Apps/<store-app-id>/docker-compose.yml
```

Both must exit 0. CI runs the same gates on every PR.

### 7. Add a changie fragment + open the PR

```bash
# Manually create the file (or install changie: go install github.com/miniscruff/changie@latest)
cat > .changes/unreleased/Added-$(date +%Y%m%d)-<store-app-id>.yaml <<EOF
kind: Added
body: |
  <Store-app-title> (<one-line>). Image: <registry>/<image>.
EOF
```

PR title format: `add: <store-app-id> — <one-line tagline>`.

The [PR template](.github/PULL_REQUEST_TEMPLATE.md) checklist covers everything above; CI re-verifies.

---

## Catalog tooling / docs PRs

Standard fork → branch → PR flow. Tests for `scripts/validate.py` live alongside the script — if you add a new check, add a fixture under `scripts/test-fixtures/` that exercises it (a pass case and a fail case).

For docs (`docs/`, `README.md`, `CONTRIBUTING.md`, `SECURITY.md`), markdownlint runs in CI — keep lines wrapped sensibly, follow the surrounding style.

---

## What gets you a fast-merge vs. a back-and-forth

**Fast-merge** (typical: under 24h):

- Trusted registry (per the matrix above), digest pinned, schema complete
- Icon present, ≤ 100KB, with attribution recorded
- No `.sh` files, no privileged capabilities, no system-path bind mounts
- Changie fragment added
- CI all green

**Back-and-forth** (will request changes):

- Image from an unfamiliar registry → we'll ask for justification + may add the registry to the whitelist in a separate PR
- LinuxServer.io image → we'll ask you to document the s6-overlay audit in `x-powerlab.security.audit_notes`
- Schema fields missing or under-specified → we'll point at `docs/schema.md`

**Rejected** (closed):

- `getumbrel/*` / `bigbear*` image, or any image we have to reverse-engineer to trust
- Any `.sh` file in the app dir
- Privileged / host-namespace / system-path bind requests
- Catalog spam (apps that already exist; trivial wrappers; abandoned upstreams)

We aim for a small, vetted catalog. **Smaller-and-safer beats larger-and-warned** — this is policy, not preference.

---

## License

By contributing, you agree that your contributions are licensed:

- `scripts/`, `docker-compose.yml`, `index.json` → AGPL-3.0 (see [`LICENSE`](LICENSE))
- `description.md`, icons, `docs/` → CC-BY-SA-4.0 (see [`LICENSE-CONTENT`](LICENSE-CONTENT))

See the README "License" section for the full per-surface mapping and rationale.

---

## Related

- PowerLab core [README](https://github.com/neochaotic/powerlab) — installs the panel that consumes this catalog
- PowerLab core [CONTRIBUTING](https://github.com/neochaotic/powerlab/blob/main/CONTRIBUTING.md) — for core (non-catalog) contributions
- [ADR-0039](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0039-powerlab-native-curated-catalog.md) — why curation is security-first
- [ADR-0041](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0041-powerlab-store-separate-repo.md) — why this catalog lives in its own repo
