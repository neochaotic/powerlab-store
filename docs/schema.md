# `x-powerlab` schema reference

Every `Apps/<id>/docker-compose.yml` MUST carry a top-level `x-powerlab` extension block. This document is the canonical specification consumed by:

- [`scripts/validate.py`](../scripts/validate.py) — CI gate in this repo
- PowerLab core's sync-catalog parser (`backend/sync-catalog/types.go`)
- PowerLab core's UI tile renderer

## Top-level structure

```yaml
services:
  # ... standard Compose services ...

x-powerlab:
  store_app_id: <kebab-case-id>          # REQUIRED, must match Apps/<id> dir name
  title: <string>                         # REQUIRED, displayed name (e.g. "Nextcloud")
  tagline: <string>                       # REQUIRED, one-line description (≤ 80 chars)
  category: <enum>                        # REQUIRED, see "Categories" below
  port_map: [...]                         # REQUIRED unless headless: true
  source: {...}                           # REQUIRED — image provenance
  icon: {...}                             # REQUIRED — icon file + attribution
  security: {...}                         # REQUIRED — image pin + audit notes
  headless: <bool>                        # OPTIONAL, default false
  arch: [...]                             # OPTIONAL, supported architectures
  resource_hints: {...}                   # OPTIONAL, surfaced in install UI
```

## Field reference

### `store_app_id` (required, string)

Kebab-case identifier, lowercase, `[a-z0-9-]+`. MUST equal the `Apps/<id>` directory name. This is the stable handle PowerLab uses for install state, audit logs, and update reconciliation. **Never renamed once published.**

### `title` (required, string)

Human-readable display name. Title-case, no marketing fluff. "Nextcloud", not "Nextcloud — Your Private Cloud Solution!".

### `tagline` (required, string, ≤ 80 chars)

One-line description shown under the title in the app tile. Active voice, present tense. "Your private cloud, in one container", not "A self-hosted cloud platform that..."

### `category` (required, enum)

One of:

- `AI & ML`
- `Database`
- `Developer`
- `Files & Sync`
- `Finance`
- `Media`
- `Network & VPN`
- `Productivity`
- `Smart home`
- `System`

Categories are CLOSED — adding a new category requires an ADR in `docs/adr/` plus a UI change in core. If your app doesn't fit, pick the closest match and explain in the PR.

### `port_map` (required unless `headless: true`, list)

List of `{container, host, protocol}` triples mapping container ports to host ports the operator can open in a browser.

```yaml
port_map:
  - container: 80
    host: 8080
    protocol: http        # http | https | tcp | udp
  - container: 443
    host: 8443
    protocol: https
```

`host` is the **default** suggestion; the installer remaps on collision. `protocol: http`/`https` makes PowerLab build the launch URL with the right scheme.

### `source` (required, object)

Image provenance. Used by the UI to show "from <upstream>" and by audit logs.

```yaml
source:
  registry: docker.io                    # docker.io | ghcr.io | lscr.io | quay.io | registry.k8s.io | gcr.io | mcr.microsoft.com
  image: nextcloud/all-in-one            # path within registry, NO tag, NO digest
  upstream_homepage: https://nextcloud.com
  upstream_repo: https://github.com/nextcloud/all-in-one   # OPTIONAL but recommended
```

The `registry` value MUST appear in the trusted-registry whitelist (see [`docs/curation-criteria.md`](curation-criteria.md)). `image` is the path; tag + digest live in the `services.<name>.image` field of the compose itself.

### `icon` (required, object)

```yaml
icon:
  file: icon.svg                         # relative to Apps/<id>/, MUST exist
  license: CC-BY-SA-4.0                  # license of THIS icon file
  attribution: Nextcloud GmbH            # who created the icon (org or person)
```

Acceptable `file` extensions: `.svg`, `.png`. Size cap: 100KB. See [`docs/icon-guidelines.md`](icon-guidelines.md).

`license` is the icon's actual license:

- `CC-BY-SA-4.0` — newly-created art (default for art generated for this repo)
- `CC-BY-4.0`, `Apache-2.0`, `MIT` — common upstream icon licenses
- `nominative-fair-use` — for trademarked vendor logos (Nginx, Postgres, etc.) where the icon is redistributed under fair use, not under a content license

### `security` (required, object)

```yaml
security:
  image_pin: pinned                      # pinned | REQUIRES-DIGEST-PIN (CI rejects the latter)
  audit_notes: |                         # free-form, what the reviewer checked
    Runs as non-root by default (UID 33).
    Single data volume; no host bind mounts.
    No capabilities added.
    s6-overlay scripts reviewed at <commit-sha> — no network fetches.
```

`image_pin` MUST be `pinned` for merge. The intermediate value `REQUIRES-DIGEST-PIN` exists so authors can run `scripts/pin-digests.sh` locally to fill it in before pushing. CI rejects PRs where it's still unfilled.

`audit_notes` is human prose summarising what the reviewer (you, the contributor) checked. Be specific. "Safe" is not an audit note. "Runs as UID 1000, mounts only the data volume, doesn't fetch anything at startup" is.

### `headless` (optional, bool, default `false`)

Set `true` for apps that legitimately have no web UI (e.g. a background worker, a Tailscale subnet router). Disables the `port_map` requirement and suppresses the "Open" button in the UI.

### `arch` (optional, list of strings)

Restrict supported architectures. If omitted, assumed `[amd64, arm64]`.

```yaml
arch: [amd64]              # x86-only, e.g. Plex media server with HW transcoding
```

The installer hides the tile on incompatible hosts.

### `resource_hints` (optional, object)

Surfaced in the install confirmation step. None of this is enforced — purely informational.

```yaml
resource_hints:
  ram_mb_min: 512
  ram_mb_recommended: 2048
  disk_gb_estimate: 5
  needs_gpu: false
```

## Full example

```yaml
services:
  app:
    image: nextcloud/all-in-one:latest-aio@sha256:abc123...
    container_name: ${POWERLAB_APP_NAME}
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - ${POWERLAB_APP_DATA}/data:/data
    environment:
      - APACHE_PORT=80

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
    license: nominative-fair-use
    attribution: Nextcloud GmbH (logo trademark)
  security:
    image_pin: pinned
    audit_notes: |
      Official Nextcloud all-in-one image (vendor-published).
      Runs as non-root. Single data volume. No host capabilities.
      Reviewed 2026-05-19.
  resource_hints:
    ram_mb_min: 1024
    ram_mb_recommended: 4096
    disk_gb_estimate: 20
```

## Versioning

This schema is `v1`. Breaking changes are an ADR in `docs/adr/` here + a coordinated bump of `min_powerlab_version` in `index.json` + a core PR updating the parser. Non-breaking additions (new optional fields) ship freely.

## Related

- [`docs/curation-criteria.md`](curation-criteria.md) — what's accepted/rejected
- [`docs/icon-guidelines.md`](icon-guidelines.md) — icon specifics
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — submission workflow
- PowerLab core [sync-catalog parser](https://github.com/neochaotic/powerlab/blob/main/backend/sync-catalog/types.go) — the consumer side of this contract
