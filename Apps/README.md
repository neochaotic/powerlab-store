# Apps/

This is where catalog apps live. Each app is a directory:

```
Apps/<store-app-id>/
├── docker-compose.yml    # required — includes x-powerlab block
├── icon.svg              # required — or icon.png, ≤ 100KB
└── description.md        # required — operator-facing long-form description
```

See:

- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — submission flow
- [`../docs/schema.md`](../docs/schema.md) — the `x-powerlab` block
- [`../docs/curation-criteria.md`](../docs/curation-criteria.md) — what's accepted
- [`../docs/icon-guidelines.md`](../docs/icon-guidelines.md) — icon spec

The catalog starts empty in `v0.1.0`. Phase 1 of the [migration plan](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0041-powerlab-store-separate-repo.md) imports 1-3 reference apps to validate the pipeline.
