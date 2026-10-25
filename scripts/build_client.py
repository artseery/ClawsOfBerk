#!/usr/bin/env python3
"""Build a Prism bootstrap whose prelaunch hook synchronizes the hosted pack."""

import argparse
import hashlib
import json
import tomllib
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import quote

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
    mods = list((ROOT / "pack").rglob("*.pw.toml"))
    source_files = json.loads((ROOT / "scripts" / "source_files.json").read_text(encoding="utf-8"))
    expected = {folder: len(files) for folder, files in source_files.items()}
    if not (ROOT / "artifacts" / "mods" / "Fastquit-3.0.2+1.18.2forge.jar").is_file():
        expected["mods"] -= 1
    found = {folder: 0 for folder in expected}
    base_url = args.pack_url.removesuffix("/pack/pack.toml")
    for path in mods:
        entry = tomllib.loads(path.read_text(encoding="utf-8"))
        folder = path.relative_to(ROOT / "pack").parts[0]
        if folder not in found:
            parser.error(f"unexpected metadata path: {path}")
        found[folder] += 1
        filename = entry.get("filename", "")
        if not filename or Path(filename).name != filename:
            parser.error(f"invalid asset filename in {path}")
        binary = ROOT / "artifacts" / folder / filename
        download = entry.get("download", {})
        expected_url = f"{base_url}/artifacts/{folder}/{quote(binary.name)}"
        if (not binary.is_file() or download.get("url") != expected_url
                or download.get("hash-format") != "sha256"
                or download.get("hash") != hashlib.sha256(binary.read_bytes()).hexdigest()):
            parser.error(f"invalid direct download metadata: {path}; run scripts/prepare_direct_pack.py")
    if found != expected:
        parser.error(f"asset metadata incomplete: {found}; expected {expected}")
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
