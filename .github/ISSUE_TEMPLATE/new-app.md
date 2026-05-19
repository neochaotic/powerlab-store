---
name: New app request
about: Propose a new self-hostable app for the curated catalog
title: "add: <app-id> — <one-line tagline>"
labels: ["new-app"]
---

<!-- Before opening this issue, please read:
     - docs/curation-criteria.md (what we accept / reject)
     - docs/schema.md (the x-powerlab block) -->

## App

- **Name**: <e.g. Nextcloud>
- **Upstream**: <https://link-to-upstream-project>
- **Image we'd use**: <e.g. `docker.io/nextcloud/all-in-one`>

## Source trust

- [ ] The image comes from a [trusted registry](../docs/curation-criteria.md#image-source-trust-matrix)
- [ ] If it's from a registry NOT on the default whitelist, here's why we should trust it:

<!-- Paragraph explaining trust. Skip if the image is in the default whitelist. -->

## Why this app

<!-- What problem does it solve for PowerLab operators? Is upstream actively
     maintained? Self-contained or does it need a Postgres+Redis cluster? -->

## Volunteer to author?

- [ ] I'll open the PR adding it
- [ ] I'm just suggesting it; happy for someone else to author

## Related catalogs

<!-- Does umbrel-apps, CasaOS-AppStore, or big-bear-casaos already ship this?
     Link to their entry for reference. Note: we don't ingest theirs;
     this is just for inspiration / sanity-check. -->
