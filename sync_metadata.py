"""Sync artist-filled metadata template into per-work JSON files.

Parses the free-form template lines like:
    《圣像画》坦培拉 50x42cm 2023
    《宫》丙烯30x18.5cm 2020
    《静物写生》 30cmx40cm  <TAB> 布面丙烯 <TAB> 2020
    《拼贴》系列  2024
    素描随笔系列
and applies title / medium / dimensions / year to the matching work JSON.
Also imports new illustration images (1-6.png .. 1-9.png) and renumbers.
"""
from __future__ import annotations

import json
import re
import shutil
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "artwork-metadata-template.txt"
WORKS = ROOT / "content" / "works"
PICTURES = Path(r"C:/Users/Junch/Pictures/Megan")

DIM_RE = re.compile(r"(\d+(?:\.\d+)?\s*(?:cm\s*)?[x×]\s*\d+(?:\.\d+)?\s*cm?|尺寸可变)", re.I)
YEAR_RE = re.compile(r"((?:19|20)\d{2})")
TITLE_RE = re.compile(r"《(.+?)》")


def parse_line(line: str) -> dict:
    info: dict = {}
    text = " ".join(line.split())
    title_match = TITLE_RE.search(text)
    if title_match:
        info["title"] = title_match.group(1)
        text = text[: title_match.start()] + " " + text[title_match.end():]
    dim_match = DIM_RE.search(text)
    if dim_match:
        dims = " ".join(dim_match.group(1).split())
        info["dimensions"] = dims
        text = text.replace(dim_match.group(1), " ")
    year_match = YEAR_RE.search(text)
    if year_match:
        info["year"] = year_match.group(1)
        text = text.replace(year_match.group(1), " ")
    medium = text.replace("系列", " ").strip(" 　\t、，。/-")
    medium = " ".join(medium.split())
    if medium:
        info["medium"] = medium
    if "title" not in info and line.strip():
        info["title"] = " ".join(line.split())
    return info


def parse_template() -> dict[str, dict]:
    works: dict[str, dict] = {}
    current: str | None = None
    for raw in TEMPLATE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            works.setdefault(current, {})
            continue
        if line.startswith(("#", "系列", "相关链接")) or "模板" in line or line.startswith(("====", "填写说明")) or re.match(r"^\d\.", line):
            continue
        if current and not works[current]:
            works[current] = parse_line(line)
    return works


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    return struct.unpack(">II", header[16:24])


def import_new_illustrations() -> list[Path]:
    target = ROOT / "images" / "works" / "illustration"
    target.mkdir(parents=True, exist_ok=True)
    copied = []
    for index in range(6, 10):
        source = PICTURES / f"1-{index}.png"
        destination = target / f"1-{index}.png"
        if source.exists() and not destination.exists():
            shutil.copy2(source, destination)
            copied.append(destination)
    return copied


def main() -> None:
    metadata = parse_template()
    print(f"parsed metadata for {len(metadata)} files, {sum(1 for v in metadata.values() if v)} with content")

    copied = import_new_illustrations()
    print(f"imported {len(copied)} new illustrations: {[p.name for p in copied]}")

    # Load all existing works (source JSON files keep .png image paths).
    works = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(WORKS.glob("*.json"))]
    print(f"loaded {len(works)} existing works from {WORKS}")

    # Apply template metadata + strip placeholder text everywhere.
    # Works without template info keep only their placeholder title;
    # every other field is cleared so the site hides empty fields.
    for work in works:
        image_name = Path(work["image"]).name
        info = metadata.get(image_name, {})
        if info:
            work["title"] = info.get("title", work["title"])
        work["titleEn"] = ""
        work["medium"] = info.get("medium", "") if info else ""
        work["dimensions"] = info.get("dimensions", "") if info else ""
        work["year"] = info.get("year", "") if info else ""
        work["alt"] = work["title"]
        work["description"] = ""

    # Add the four new illustrations (no metadata yet), skipping any
    # that already exist so re-runs stay idempotent.
    existing_slugs = {work["slug"] for work in works}
    for index in range(6, 10):
        slug = f"illustration-{index:02d}"
        if slug in existing_slugs:
            continue
        filename = f"1-{index}.png"
        image_path = ROOT / "images" / "works" / "illustration" / filename
        if not image_path.exists():
            print(f"WARNING: {filename} missing from project images")
            continue
        width, height = png_size(image_path)
        ratio = height / width
        layout = "portrait" if ratio > 1.12 else ("landscape" if ratio < 0.89 else "square")
        works.append({
            "slug": slug,
            "title": f"插画 {index:02d}",
            "titleEn": "",
            "series": "illustration",
            "year": "",
            "medium": "",
            "dimensions": "",
            "image": f"/images/works/illustration/{filename}",
            "gallery": [],
            "alt": f"插画 {index:02d}",
            "description": "",
            "featured": False,
            "published": True,
            "order": 0,
            "layout": layout,
            "width": width,
            "height": height,
        })

    # Renumber: order by series then original image index, so new
    # illustrations 1-6..1-9 sit inside the illustration block.
    series_order = {"illustration": 1, "poster-design": 2, "acrylic-oil": 3, "watercolor": 4, "watercolor-portrait": 5, "printmaking": 6}

    def sort_key(work: dict):
        series = series_order[work["series"]]
        match = re.search(r"-(\d+)\.(png|webp)$", work["image"])
        index = int(match.group(1)) if match else 999
        return (series, index)

    works.sort(key=sort_key)
    for order, work in enumerate(works, 1):
        work["order"] = order
        work["featured"] = order == 1

    for old in WORKS.glob("*.json"):
        old.unlink()
    for work in works:
        destination = WORKS / f"{work['order']:02d}-{work['slug']}.json"
        destination.write_text(json.dumps(work, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    counts: dict[str, int] = {}
    for work in works:
        counts[work["series"]] = counts.get(work["series"], 0) + 1
    with_info = sum(1 for w in works if w["medium"] or w["year"] or w["dimensions"])
    print(f"total works: {len(works)} | with info: {with_info} | per series: {counts}")


if __name__ == "__main__":
    main()
