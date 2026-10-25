Place the complete installed pack's binary files here before publishing:

- `mods/`: 143 `.jar` files
- `shaderpacks/`: 6 `.zip` files
- `resourcepacks/`: 3 `.zip` files

Use `python3 scripts/extract_installed_instance.py /path/to/instance.zip` to
copy these from a ZIP of the installed instance. `prepare_direct_pack.py` will
hash each file and create Packwiz metadata with direct GitHub Pages URLs.
