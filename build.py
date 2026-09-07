from __future__ import annotations

import json
import shutil
import struct
from pathlib import Path

MAX_EDGE = 2560
WEBP_QUALITY = 92

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "_site"


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return (0, 0)
    return struct.unpack(">II", header[16:24])


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


def optimize_work_images() -> bool:
    """Generate WebP display copies (max 2000px edge) next to the PNG sources.

    Returns True when Pillow was available and every PNG has a WebP copy.
    """
    try:
        from PIL import Image
    except ImportError:
        print("Pillow not installed - deploying original PNG files")
        return False

    works_source = ROOT / "images" / "works"
    optimized = 0
    for png_path in sorted(works_source.rglob("*.png")):
        webp_path = png_path.with_suffix(".webp")
        if webp_path.exists() and webp_path.stat().st_mtime >= png_path.stat().st_mtime:
            optimized += 1
            continue
        with Image.open(png_path) as image:
            image = image.convert("RGB")
            edge = max(image.size)
            if edge > MAX_EDGE:
                scale = MAX_EDGE / edge
                image = image.resize(
                    (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
                    Image.LANCZOS,
                )
            image.save(webp_path, format="WEBP", quality=WEBP_QUALITY, method=6)
        optimized += 1
    print(f"optimized {optimized} work images to WebP (max edge {MAX_EDGE}px)")
    return True


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()

    optimized = optimize_work_images()

    shutil.copy2(ROOT / "index.html", OUTPUT / "index.html")
    shutil.copytree(ROOT / "assets", OUTPUT / "assets")

    # Top-level images (e.g. the artist portrait) live beside the works tree.
    (OUTPUT / "images").mkdir(parents=True, exist_ok=True)
    for image_file in (ROOT / "images").iterdir():
        if image_file.is_file():
            shutil.copy2(image_file, OUTPUT / "images" / image_file.name)

    # Deploy lightweight WebP copies; fall back to PNGs only without Pillow.
    works_source = ROOT / "images" / "works"
    works_target = OUTPUT / "images" / "works"
    works_target.parent.mkdir(parents=True, exist_ok=True)
    if optimized:
        for webp_path in sorted(works_source.rglob("*.webp")):
            destination = works_target / webp_path.relative_to(works_source)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(webp_path, destination)
    else:
        shutil.copytree(works_source, works_target)
    shutil.copytree(ROOT / "images" / "placeholders", OUTPUT / "images" / "placeholders")

    output_content = OUTPUT / "content"
    output_content.mkdir()
    shutil.copy2(ROOT / "content" / "site.json", output_content / "site.json")

    suffix = ".webp" if optimized else ".png"
    series_entries = read_collection(ROOT / "content" / "series")
    work_entries = read_collection(ROOT / "content" / "works")
    for item in work_entries:
        image_ref = item.get("image", "")
        if image_ref.endswith(".png"):
            candidate = ROOT / image_ref.lstrip("/")
            candidate = candidate.with_suffix(suffix)
            if candidate.is_file():
                item["image"] = str(candidate.relative_to(ROOT)).replace("\\", "/")
                item["image"] = "/" + item["image"]

    series_manifest = json.dumps(series_entries, ensure_ascii=False, indent=2) + "\n"
    works_manifest = json.dumps(work_entries, ensure_ascii=False, indent=2) + "\n"
    (output_content / "series.json").write_text(series_manifest, encoding="utf-8")
    (output_content / "works.json").write_text(works_manifest, encoding="utf-8")

    # Keep branch-based GitHub Pages compatible with the same data manifests.
    (ROOT / "content" / "series.json").write_text(series_manifest, encoding="utf-8")
    (ROOT / "content" / "works.json").write_text(works_manifest, encoding="utf-8")
    (OUTPUT / ".nojekyll").touch()
    print(f"Built static portfolio at {OUTPUT}")


if __name__ == "__main__":
    main()
