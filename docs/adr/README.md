# Architectural Decision Records — `powerlab-store`

Store-specific ADRs live here. Decisions that affect this product's own architecture (schema revisions, contract changes with consumers, format migrations) belong in this directory.

The **decision to split the catalog out of PowerLab core** is a core-side decision and lives there:

- [PowerLab core ADR-0041 — Split community catalog into separate `powerlab-store` repo](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0041-powerlab-store-separate-repo.md)

Related core decisions providing context:

- [PowerLab core ADR-0039 — Native curated catalog (security-first)](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0039-powerlab-native-curated-catalog.md)
- [PowerLab core ADR-0040 — Proportional engineering hygiene baseline](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0040-proportional-engineering-hygiene-baseline.md)

## ADR template

Use the same format as PowerLab core ([example](https://github.com/neochaotic/powerlab/blob/main/docs/decisions/0040-proportional-engineering-hygiene-baseline.md)):

```markdown
# 0001 — <Short decision title>

- **Status:** proposed | accepted | superseded by NNNN
- **Date:** YYYY-MM-DD

## Context
## Decision
## Consequences
## Alternatives considered
## References
```

Numbering starts at `0001`. Sequential. Renumbering is forbidden (preserve audit trail).
