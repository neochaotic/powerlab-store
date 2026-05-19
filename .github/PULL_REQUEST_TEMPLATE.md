<!-- Thanks for contributing to powerlab-store.
     Pick ONE of the two checklists below based on what your PR does.
     Leave the unused checklist in place so reviewers can confirm at a glance.
-->

## What this PR does

<!-- 1-2 sentences. -->

## Type

- [ ] Add a new app
- [ ] Fix / update an existing app
- [ ] Catalog tooling / docs / CI

---

## Checklist — adding or updating an app

- [ ] App lives under `Apps/<store-app-id>/` (kebab-case, lowercase)
- [ ] `docker-compose.yml` present with full `x-powerlab` block ([schema](../docs/schema.md))
- [ ] `icon.svg` OR `icon.png` present, ≤ 100KB
- [ ] `description.md` present
- [ ] Image is from a [trusted registry](../docs/curation-criteria.md#image-source-trust-matrix); justification below if non-obvious
- [ ] Image is digest-pinned (`@sha256:...`) — ran `./scripts/pin-digests.sh`
- [ ] Zero `*.sh` files anywhere in `Apps/<id>/`
- [ ] No `privileged`, `docker.sock`, `network_mode:host`, `pid:host`, `ipc:host`, `cap_add: ALL|SYS_ADMIN`, `env_file`
- [ ] `x-powerlab.security.audit_notes` is specific (not just "safe")
- [ ] `x-powerlab.icon.{license,attribution}` reflects actual icon source
- [ ] `./scripts/validate.py Apps/` passes locally
- [ ] `./scripts/check-safety.sh` passes locally
- [ ] Added a changie fragment under `.changes/unreleased/`

### Image source justification

<!-- If the image is from a registry NOT in the default whitelist
     (or a borderline case like LinuxServer.io), explain why we should
     trust it. Link to upstream's release/publish policy if relevant. -->

### Audit notes summary

<!-- One paragraph describing what you checked. Be specific.
     "Runs as UID 1000, only data volume mounted, doesn't fetch
     anything at startup" beats "looks safe". -->

---

## Checklist — catalog tooling / docs / CI

- [ ] Added a changie fragment under `.changes/unreleased/`
- [ ] If touching validators: added a fixture under `scripts/test-fixtures/` exercising the new check
- [ ] If touching docs: kept the [cross-link strategy](../README.md#quick-links) consistent
- [ ] If touching workflows: tested locally (act, or by opening a draft PR)

---

## Related

<!-- Link to PowerLab core ADRs / issues / PRs if this PR is downstream
     of a core decision. e.g. "Implements part of
     https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0041-powerlab-store-separate-repo.md" -->
