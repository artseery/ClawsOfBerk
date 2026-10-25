#!/usr/bin/env python3
"""Import the bundled CurseForge manifest using packwiz's native importer."""

import json
import shutil
import subprocess
import tempfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    manifest_data = (ROOT / "source-manifest.json").read_bytes()
    manifest = json.loads(manifest_data)
    expected = {(entry["projectID"], entry["fileID"]) for entry in manifest["files"]}
    if len(expected) != len(manifest["files"]):
        raise ValueError("duplicate project/file pair in source manifest")

    with tempfile.TemporaryDirectory(prefix="clawsofberk-packwiz-") as temp:
        stage = Path(temp)
        source_zip = stage / "curseforge-source.zip"
        with zipfile.ZipFile(source_zip, "w") as archive:
            archive.writestr("manifest.json", manifest_data)
            archive.writestr("overrides/", b"")
        imported = stage / "imported"
        imported.mkdir()
        subprocess.run(["packwiz", "curseforge", "import", str(source_zip)],
                       cwd=imported, check=True)
        metafiles = sorted(imported.rglob("*.pw.toml"))
        found = set()
        for path in metafiles:
            entry = tomllib.loads(path.read_text(encoding="utf-8"))
            cf = entry.get("update", {}).get("curseforge", {})
            pair = (cf.get("project-id"), cf.get("file-id"))
            if pair not in expected or pair in found:
                raise ValueError(f"unexpected or duplicate Packwiz entry: {path.name} {pair}")
            if not entry.get("filename") or not entry.get("download", {}).get("hash"):
                raise ValueError(f"missing filename or hash: {path.name}")
            found.add(pair)
        if found != expected or len(metafiles) != len(expected):
            raise ValueError(f"Packwiz imported {len(found)}/{len(expected)} files; pack unchanged")

        pack = ROOT / "pack"
        for old in pack.rglob("*.pw.toml"):
            old.unlink()
        for source in metafiles:
            rel = source.relative_to(imported)
            # Packwiz currently emits this manifest's shader projects at the
            # pack root; Prism expects their ZIPs inside shaderpacks/.
            if len(rel.parts) == 1:
                rel = Path("shaderpacks") / rel
            target = pack / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    from refresh import main as refresh
    refresh()
    print(f"Imported {len(found)} CurseForge entries with Packwiz")


if __name__ == "__main__":
    main()
