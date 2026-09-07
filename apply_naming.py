"""Apply artist naming updates exported from name-editor.html.

Accepts either format:
1. naming-updates.json  -> [{"slug": ..., "file": ..., "oldTitle": ..., "newTitle": ...}, ...]
2. plain text lines     -> 2-5.png = 新名字   (separators: = : ：, flexible spacing)

Usage: python apply_naming.py <path-to-file>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKS = ROOT / "content" / "works"


def parse_text(path: Path) -> dict[str, str]:
    updates: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([\w.-]+\.(?:png|jpg|jpeg|webp))\s*[=:：]\s*(.+)$", line, re.I)
        if match:
            updates[match.group(1).lower()] = match.group(2).strip()
        else:
            print(f"SKIP (unrecognized): {line}")
    return updates


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    source = Path(sys.argv[1])
    if not source.exists():
        print(f"file not found: {source}")
        sys.exit(1)

    if source.suffix.lower() == ".json":
        entries = json.loads(source.read_text(encoding="utf-8"))
        updates = {entry["file"].lower(): entry["newTitle"].strip() for entry in entries}
    else:
        updates = parse_text(source)

    if not updates:
        print("no naming updates found in the file")
        sys.exit(1)

    applied = 0
    skipped = []
    for json_path in sorted(WORKS.glob("*.json")):
        work = json.loads(json_path.read_text(encoding="utf-8"))
        image_name = Path(work["image"]).name.lower()
        if image_name in updates:
            new_title = updates[image_name]
            if new_title and new_title != work["title"]:
                work["title"] = new_title
                work["alt"] = new_title
                json_path.write_text(json.dumps(work, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                applied += 1
                print(f"renamed {image_name}: {work['title']}")
            else:
                skipped.append(image_name)
        else:
            skipped.append(image_name)

    unmatched = sorted(set(updates) - {Path(w["image"]).name.lower() for w in
                                        (json.loads(p.read_text(encoding="utf-8")) for p in WORKS.glob("*.json"))})
    if unmatched:
        print(f"WARNING: {len(unmatched)} filenames not matched: {unmatched}")
    print(f"applied {applied} renames, {len(skipped)} untouched. Next: python build.py")
    if applied:
        print("remember to rebuild and let the artist verify before pushing.")


if __name__ == "__main__":
    main()
