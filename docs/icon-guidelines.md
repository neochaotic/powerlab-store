# Icon guidelines

Every app in `Apps/<id>/` MUST ship an icon as a raw binary file in the app directory. Hot-linking to upstream CDNs is **not allowed** ([rationale](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0041-powerlab-store-separate-repo.md) — supply-chain pinning, air-gap support, enterprise audit posture).

## File requirements

| | Required | Notes |
|---|---|---|
| Path | `Apps/<id>/icon.svg` OR `Apps/<id>/icon.png` | Exactly one of the two. SVG preferred. |
| Size | ≤ 100KB | Enforced by `.github/workflows/icon-lint.yml`. |
| SVG specifics | Optimised (no editor metadata, no embedded raster) | Run through SVGO or equivalent before submitting. |
| PNG specifics | 512×512 minimum, transparent background where appropriate | Use only when SVG isn't available upstream. |
| Square aspect | The UI renders icons in a square tile | Non-square icons get letterboxed; not great-looking. |

## Sourcing an icon

In order of preference:

1. **Upstream's official logo** — from their website's press kit, brand assets page, or `LOGO.svg` in their main repo. Almost always the right answer for established projects (Nextcloud, Jellyfin, Postgres, etc.).
2. **Upstream's published icon in their catalog/manifest** — e.g. the icon they ship in a `helm` chart, `flatpak` manifest, or APK icon.
3. **A community-recognised representation** — when no official logo exists, find what most third-party reviews and docs use.
4. **Newly-created icon** — last resort, for apps with no visual identity. See "Creating an icon" below.

## Attribution

The `x-powerlab.icon.license` and `x-powerlab.icon.attribution` fields in `docker-compose.yml` MUST reflect the icon's actual source:

| Icon source | `license` value | `attribution` value |
|---|---|---|
| Upstream's logo (trademarked) | `nominative-fair-use` | `<Project Name>` (e.g. `Nextcloud GmbH (logo trademark)`) |
| Upstream's logo, explicitly licensed | The upstream license (e.g. `CC-BY-4.0`, `MIT`) | `<Project Name>` |
| Community icon under explicit license | The actual license | The creator's name + license URL |
| Newly-created for this repo | `CC-BY-SA-4.0` | `PowerLab Store contributors` |

## Creating an icon (when nothing upstream exists)

> **Status (2026-05-19): art generation is deferred.** The repo bootstrap leaves placeholder slots — a dedicated agent or designer fills these in later. The guidelines below are the spec for that work, not a contributor expectation today.

Style targets when this happens:

- **Monoline / geometric** — consistent stroke width, minimal detail at small sizes
- **2-3 colour palette** — works on light and dark UI backgrounds
- **Recognisable at 32×32** — the smallest size we render at
- **Subject-evocative** — for a Postgres-style DB app, an elephant silhouette is more useful than the letter "P" on a tile
- **Not a screenshot** — never crop a UI screenshot down to icon size; it always looks bad

Default license for created art: **CC-BY-SA-4.0**. Record in `x-powerlab.icon.license`.

## What to do RIGHT NOW

If you're submitting an app and the upstream has a logo:

1. Grab it from their press kit / brand page / main repo
2. Drop in `Apps/<id>/icon.svg` (or `.png`)
3. Fill `x-powerlab.icon.{license,attribution}` honestly

If the upstream has NO logo:

1. Open the PR anyway with a placeholder `icon.svg` (a simple 64×64 SVG with the app's first letter is fine for now)
2. Note in the PR description that the icon needs replacement
3. The catalog maintainer or a future art-pass agent will commission/create a real one before the next release tag

Don't block a security-good catalog addition on icon perfection.

## Related

- [`docs/schema.md`](schema.md) — full `x-powerlab.icon` field spec
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — submission flow
- Memory: `catalog_icons_rehosted_as_raw` (anchor file `feedback_umbrel_icons_as_is.md`) — rehost policy origin
