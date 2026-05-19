---
name: App bug
about: Report a bug in a catalog app (install fails, container won't start, etc.)
title: "bug: <app-id> — <one-line summary>"
labels: ["app-bug"]
---

## App

- **Which app**: <Apps/<id>>
- **Store version**: <git tag or commit you installed from>
- **PowerLab core version**: <output of `curl http://localhost:8765/v1/sys/version/current`>

## What happened

<!-- Steps to reproduce. -->

## What you expected

## Logs / output

```
<paste relevant logs here>
```

## Environment

- **Distro**: <e.g. Ubuntu 24.04 arm64>
- **Hardware**: <e.g. Raspberry Pi 5 8GB>
- **Docker version**: <output of `docker version`>

## Note

If the bug is in PowerLab core (the installer, the gateway, the UI tile, the catalog parser) rather than in the app itself, please file at [github.com/neochaotic/powerlab/issues](https://github.com/neochaotic/powerlab/issues) instead.
