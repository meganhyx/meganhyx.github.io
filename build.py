from __future__ import annotations

import json
import shutil
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "_site"


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return (0, 0)
    width, height = struct.unpack(">II", header[16:24])
    return (width, height)


def read_collection(folder: Path) -> list[dict]:
    entries = [json.loads(path.read_text(encoding="utf-8")) for path in folder.glob("*.json")]
    items = sorted((item for item in entries if item.get("published", True)), key=lambda item: item.get("order", 9999))
    for item in items:
        image_ref = item.get("image", "")
        image_path = ROOT / image_ref.lstrip("/") if image_ref else None
        if image_path and image_path.is_file():
            width, height = png_size(image_path)
            item.setdefault("width", width)
            item.setdefault("height", height)
    return items


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()

    shutil.copy2(ROOT / "index.html", OUTPUT / "index.html")
    shutil.copytree(ROOT / "assets", OUTPUT / "assets")
    shutil.copytree(ROOT / "images", OUTPUT / "images")

    output_content = OUTPUT / "content"
    output_content.mkdir()
    shutil.copy2(ROOT / "content" / "site.json", output_content / "site.json")
    series_manifest = json.dumps(read_collection(ROOT / "content" / "series"), ensure_ascii=False, indent=2) + "\n"
    works_manifest = json.dumps(read_collection(ROOT / "content" / "works"), ensure_ascii=False, indent=2) + "\n"
    (output_content / "series.json").write_text(series_manifest, encoding="utf-8")
    (output_content / "works.json").write_text(works_manifest, encoding="utf-8")

    # Keep branch-based GitHub Pages compatible with the same data manifests.
    (ROOT / "content" / "series.json").write_text(series_manifest, encoding="utf-8")
    (ROOT / "content" / "works.json").write_text(works_manifest, encoding="utf-8")
    (OUTPUT / ".nojekyll").touch()
    print(f"Built static portfolio at {OUTPUT}")


if __name__ == "__main__":
    main()
