#!/usr/bin/env python3
"""Copy only the binary payloads from a complete installed-instance ZIP."""

import argparse
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {"mods": (".jar", 143), "shaderpacks": (".zip", 6),
            "resourcepacks": (".zip", 3)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("instance_zip", type=Path)
    args = parser.parse_args()
    selected = {folder: {} for folder in EXPECTED}
    with zipfile.ZipFile(args.instance_zip) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            parts = Path(info.filename).parts
            for folder, (extension, _) in EXPECTED.items():
                if folder not in parts:
                    continue
                pos = parts.index(folder)
                if len(parts) != pos + 2:
                    continue
                name = parts[-1]
                if name in {".", ".."} or not name.lower().endswith(extension):
                    continue
                if name in selected[folder]:
                    parser.error(f"duplicate {folder}/{name} in ZIP")
                selected[folder][name] = info
        for folder, (_, count) in EXPECTED.items():
            if len(selected[folder]) != count:
                parser.error(f"{folder}: found {len(selected[folder])}/{count} files; no files copied")
        for folder, files in selected.items():
            dest = ROOT / "artifacts" / folder
            dest.mkdir(parents=True, exist_ok=True)
            for name, info in files.items():
                with archive.open(info) as source, (dest / name).open("wb") as target:
                    shutil.copyfileobj(source, target)
    print("Copied 143 mods, 6 shaderpacks, and 3 resourcepacks")


if __name__ == "__main__":
    main()
