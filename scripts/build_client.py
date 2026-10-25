#!/usr/bin/env python3
"""Build a Prism bootstrap whose prelaunch hook synchronizes the hosted pack."""

import argparse
import hashlib
import json
import tempfile
import tomllib
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_URL = ("https://github.com/packwiz/packwiz-installer-bootstrap/releases/"
                 "download/v0.0.3/packwiz-installer-bootstrap.jar")
BOOTSTRAP_SHA256 = "a8fbb24dc604278e97f4688e82d3d91a318b98efc08d5dbfcbcbcab6443d116c"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack-url", required=True,
                        help="public URL ending in /pack/pack.toml")
    parser.add_argument("--bootstrap", type=Path,
                        help="previously downloaded packwiz-installer-bootstrap.jar")
    args = parser.parse_args()
    if not args.pack_url.startswith("https://") or not args.pack_url.endswith("/pack/pack.toml"):
        parser.error("--pack-url must be a public HTTPS URL ending in /pack/pack.toml")
    expected = json.loads((ROOT / "source-manifest.json").read_text())["files"]
    mods = list((ROOT / "pack").rglob("*.pw.toml"))
    found = set()
    for path in mods:
        entry = tomllib.loads(path.read_text(encoding="utf-8"))
        cf = entry.get("update", {}).get("curseforge", {})
        found.add((cf.get("project-id"), cf.get("file-id")))
    wanted = {(f["projectID"], f["fileID"]) for f in expected}
    if found != wanted or len(mods) != len(wanted):
        parser.error(f"mod metadata incomplete: {len(found & wanted)}/{len(wanted)}; run scripts/import_with_packwiz.py")
    pack = tomllib.loads((ROOT / "pack" / "pack.toml").read_text())
    index_data = (ROOT / "pack" / pack["index"]["file"]).read_bytes()
    if hashlib.sha256(index_data).hexdigest() != pack["index"]["hash"]:
        parser.error("stale index hash; run scripts/refresh.py")
    index = tomllib.loads(index_data.decode())
    indexed = {entry["file"]: entry for entry in index["files"]}
    for path in (ROOT / "pack").rglob("*"):
        if not path.is_file() or path.name in {"pack.toml", "index.toml"}:
            continue
        rel = path.relative_to(ROOT / "pack").as_posix()
        if rel not in indexed or hashlib.sha256(path.read_bytes()).hexdigest() != indexed[rel]["hash"]:
            parser.error(f"stale index entry for {rel}; run scripts/refresh.py")
    if len(indexed) != len(index["files"]) or len(indexed) != sum(
            1 for path in (ROOT / "pack").rglob("*")
            if path.is_file() and path.name not in {"pack.toml", "index.toml"}):
        parser.error("index has missing or extra files; run scripts/refresh.py")
    if args.bootstrap:
        jar = args.bootstrap.read_bytes()
    else:
        with urllib.request.urlopen(BOOTSTRAP_URL, timeout=60) as response:
            jar = response.read()
    if hashlib.sha256(jar).hexdigest() != BOOTSTRAP_SHA256:
        parser.error("Packwiz bootstrap SHA-256 mismatch")
    instance = (ROOT / "client" / "instance.cfg").read_text()
    instance = (instance.replace("${PACK_NAME}", "ClawsOfBerk")
                .replace("${PACK_URL}", args.pack_url)
                .replace("${CLIENT_MIN_MEMORY_MB}", "4096")
                .replace("${CLIENT_MAX_MEMORY_MB}", "6144"))
    output = ROOT / "dist" / "ClawsOfBerk-prism.zip"
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        for name, data in [
            ("instance.cfg", instance.encode()),
            ("mmc-pack.json", (ROOT / "client" / "mmc-pack.json").read_bytes()),
            (".minecraft/packwiz-installer-bootstrap.jar", jar),
        ]:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    print(output)


if __name__ == "__main__":
    main()
