from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "_site"


def read_collection(folder: Path) -> list[dict]:
    entries = [json.loads(path.read_text(encoding="utf-8")) for path in folder.glob("*.json")]
    return sorted((item for item in entries if item.get("published", True)), key=lambda item: item.get("order", 9999))


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
