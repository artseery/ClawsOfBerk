# ClawsOfBerk 3.2.7 — Packwiz source

This is the client distribution layout adapted from `atfc-main`: `pack/` is
hosted as static files, and a one-time Prism archive runs Packwiz Installer
before every launch. The source is the provided CurseForge export
`ClawsOfBerk-[3.2.7].zip` (Minecraft 1.18.2, Forge 40.3.12).

## Import the 153 mod entries

The CurseForge export contains project/file IDs, but **not** the filenames or
hashes Packwiz needs. The GitHub Actions workflow runs Packwiz's native
`curseforge import` command to resolve these records. You do not need to
provide a CurseForge API key. For a local import with Packwiz installed:

```bash
python3 scripts/import_with_packwiz.py
```

The wrapper checks every imported project/file ID and hash before copying the
metafiles into `pack/`, then refreshes the index. It aborts without changing
the pack if metadata is incomplete. The original export does not specify
server/client sides, so use this as a client pack.

## Publish on GitHub Pages

Push the **contents of this directory** to the root of a GitHub repository on
the `main` branch. In repository Settings → Pages, select **GitHub Actions**
as the build and deployment source. The included `.github/workflows/pages.yml`
installs Packwiz, imports all 153 files, publishes `pack/`, builds the Prism
archive with the actual Pages URL, and places it at the Pages homepage. It
refuses to deploy if mod metadata or Packwiz hashes are invalid.

For a local build, provide the expected public URL manually:

```bash
python3 scripts/build_client.py \
  --pack-url 'https://YOUR_NAME.github.io/YOUR_REPO/pack/pack.toml'
```

Players download `ClawsOfBerk-prism.zip` from the Pages homepage and import it
into Prism once. Subsequent launches read the hosted `pack.toml` and
synchronize changes. The player needs Java 17 for Minecraft 1.18.2.

After editing files under `pack/`, run `python3 scripts/refresh.py`, then
publish `pack/index.toml` and `pack/pack.toml` together with the changed
files. The world under `pack/saves/` has `preserve = true` in the index so
player progress is not overwritten on later launches.

Some mod authors may block automatic third-party JAR downloads; those files
can require manual download through Packwiz Installer. Do not republish their
binaries without permission.
