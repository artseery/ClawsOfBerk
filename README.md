# ClawsOfBerk 3.2.7 — GitHub-hosted Packwiz pack

`pack/` is the Packwiz manifest and configuration tree. GitHub Pages serves
`pack/pack.toml` for the Prism prelaunch installer. Every mod, shader pack,
and resource pack binary is served directly from the same Pages site under
`artifacts/`; players do not download anything from CurseForge.

## Files in this repository

The source CurseForge export contains no mod JARs. `artifacts/` now contains
143 exact mod JARs, 6 shader ZIPs, and 3 resource-pack ZIPs. Their SHA-1
values are checked against `scripts/source_files.json`, which records the
original pack's file hashes. The map is already included under `pack/saves/`.

## Publish

Push the contents of this directory to `main` in
`github.com/artseery/ClawsOfBerk`. GitHub Pages is configured to use GitHub
Actions. The workflow verifies the binaries, writes direct-download Packwiz
metadata, builds `ClawsOfBerk-prism.zip`, and publishes the manifest and
binary files together. It fails if any required file is missing or changed.

The public Packwiz URL is:

```text
https://artseery.github.io/ClawsOfBerk/pack/pack.toml
```

Players import the Prism ZIP once. Each launch synchronizes this URL. For
Minecraft 1.18.2, select Java 17 in Prism.

After changing configs or scripts under `pack/`, run
`python3 scripts/refresh.py` and commit both `pack/index.toml` and
`pack/pack.toml`. World files under `pack/saves/` are marked `preserve = true`
so player progress is retained.
