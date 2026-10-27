#!/usr/bin/env python3
"""Build Packwiz metadata for binaries hosted on the same GitHub Pages site."""

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "pack"
ARTIFACTS = ROOT / "artifacts"
SOURCE_FILES = json.loads((ROOT / "scripts" / "source_files.json").read_text(encoding="utf-8"))
SERVER_MODS = set(json.loads((ROOT / "scripts" / "server_mods.json").read_text(encoding="utf-8")))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="GitHub Pages site URL")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    if not base_url.startswith("https://"):
        parser.error("--base-url must be HTTPS")
    if len(SERVER_MODS) != 116 or not SERVER_MODS <= set(SOURCE_FILES["mods"]):
        parser.error("server_mods.json must contain the 114 official server mods and the two Quark dependencies")

    planned = {}
    total_bytes = 0
    for folder, expected in SOURCE_FILES.items():
        directory = ARTIFACTS / folder
        files = sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in {".jar", ".zip"})
        actual = {p.name for p in files}
        missing = set(expected) - actual
        extra = actual - set(expected)
        if missing or extra:
            parser.error(f"{folder}: missing {sorted(missing)}, unexpected {sorted(extra)}")
        for file in files:
            if file.stat().st_size >= 100 * 1024 * 1024:
                parser.error(f"{file} exceeds GitHub's 100 MiB file limit")
            data = file.read_bytes()
            if hashlib.sha1(data).hexdigest() != expected[file.name]:
                parser.error(f"{file}: SHA-1 differs from original modpack")
            total_bytes += len(data)
            digest = hashlib.sha256(data).hexdigest()
            safe_name = re.sub(r"[^a-z0-9]+", "-", file.stem.lower()).strip("-")[:80]
            meta_name = f"{safe_name}-{digest[:12]}.pw.toml"
            relative = Path(folder) / meta_name
            url = f"{base_url}/artifacts/{folder}/{quote(file.name)}"
            planned[relative] = (f"name = {json.dumps(file.stem, ensure_ascii=False)}\n"
                                 f"filename = {json.dumps(file.name, ensure_ascii=False)}\n"
                                 f'side = "{"both" if folder == "mods" and file.name in SERVER_MODS else "client"}"\n\n'
                                 "[download]\n"
                                 f"url = {json.dumps(url, ensure_ascii=False)}\n"
                                 'hash-format = "sha256"\n'
                                 f'hash = "{digest}"\n')
    if total_bytes + sum(p.stat().st_size for p in PACK.rglob("*") if p.is_file()) >= 1024 ** 3:
        parser.error("Pack plus artifacts exceeds GitHub Pages' 1 GiB site limit")

    # Validate all input before replacing any metafiles.
    for old in PACK.rglob("*.pw.toml"):
        old.unlink()
    for relative, content in planned.items():
        target = PACK / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    from refresh import main as refresh
    refresh()
    print(f"Prepared {len(planned)} direct GitHub downloads ({total_bytes / 1024**2:.1f} MiB)")


if __name__ == "__main__":
    main()
