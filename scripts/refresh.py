#!/usr/bin/env python3
"""Rebuild Packwiz's SHA-256 index and pack pointer from the local pack tree."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "pack"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    entries = []
    for path in sorted(PACK.rglob("*")):
        if not path.is_file() or path.name in {"pack.toml", "index.toml"}:
            continue
        rel = path.relative_to(PACK).as_posix()
        item = ["[[files]]", f"file = {json.dumps(rel, ensure_ascii=False)}",
                f'hash = "{sha256(path.read_bytes())}"']
        if rel.endswith(".pw.toml"):
            item.append("metafile = true")
        if rel.startswith("saves/"):
            item.append("preserve = true")
        entries.append("\n".join(item))
    index = 'hash-format = "sha256"\n\n' + "\n\n".join(entries) + "\n"
    (PACK / "index.toml").write_text(index, encoding="utf-8")
    manifest = json.loads((ROOT / "source-manifest.json").read_text())
    version = manifest.get("version") or "3.2.7"
    pack = (f'name = "ClawsOfBerk"\nversion = "{version}"\n'
            'pack-format = "packwiz:1.1.0"\n\n[index]\n'
            f'file = "index.toml"\nhash-format = "sha256"\nhash = "{sha256(index.encode())}"\n\n'
            '[versions]\nforge = "40.3.12"\nminecraft = "1.18.2"\n')
    (PACK / "pack.toml").write_text(pack, encoding="utf-8")
    print(f"Indexed {len(entries)} files")


if __name__ == "__main__":
    main()
