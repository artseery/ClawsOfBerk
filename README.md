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

`scripts/server_mods.json` records the 114 JARs in the matching official
ClawsOfBerk 3.2.7 server archive. The generated metadata marks the other 29
mods as client-side, so Packwiz `-s server` installs only the server set.
The server needs Forge 40.3.12 for Minecraft 1.18.2 and Java 17.

## Install the dedicated server

The server scripts target `/home/seery/minecraft/clawsofberk`. They prepare a
separate runtime and start it on loopback port 25566 while the existing ATFC
server keeps running. The test runtime uses the Isle of Berk map included in
this pack. After the test server reaches the Minecraft `Done` state, run
`server/switch.sh` to move ClawsOfBerk to port 25565. The old ATFC runtime
and world remain in place for rollback.

```bash
cd ~/minecraft/clawsofberk
./server/install.sh
systemctl --user status minecraft-clawsofberk.service
journalctl --user -u minecraft-clawsofberk.service -f
```

Once the test server has reached `Done`, stop following its live log with
Ctrl+C and activate the new server:

```bash
./server/switch.sh
```

For later pack updates, pull the repository and run `./server/update.sh`. It
stops the server before syncing and restarts it only after a successful sync.
The old ATFC world was made for Minecraft 1.20.1; this pack is Minecraft
1.18.2. The switch retains the ATFC world in its existing runtime and starts
the included Isle of Berk map as the separate ClawsOfBerk world.

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
