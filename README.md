# ClawsOfBerk 3.2.7 — GitHub-hosted Packwiz pack

`pack/` is the Packwiz manifest and configuration tree. GitHub Pages serves
`pack/pack.toml` for the Prism prelaunch installer. Every mod, shader pack,
and resource pack binary is served directly from the same Pages site under
`artifacts/`; players do not download anything from CurseForge.

## Supply the actual game files

The provided `ClawsOfBerk-[3.2.7].zip` is a CurseForge export with 153 file
IDs and 552 overrides, but **zero JAR files**. To finish this repository,
provide a ZIP of a fully installed ClawsOfBerk instance containing its
`mods/`, `shaderpacks/`, and `resourcepacks/` directories. Then run:

```bash
python3 scripts/extract_installed_instance.py /path/to/installed-instance.zip
```

This requires 143 mod JARs, 6 shader ZIPs, and 3 resource-pack ZIPs. The
source archive already includes the map under `pack/saves/`, so its separate
CurseForge ZIP entry is unnecessary. Files are copied into `artifacts/` only
when all three categories have the expected counts. Check the files before
publishing to ensure they are the intended pack versions and may be shared.

## Publish

Push the contents of this directory to `main` in
`github.com/artseery/ClawsOfBerk`. GitHub Pages is configured to use GitHub
Actions. The workflow hashes the binaries, writes direct-download Packwiz
metadata, builds `ClawsOfBerk-prism.zip`, and publishes the manifest and
binary files together. It fails instead of publishing an incomplete build.

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
