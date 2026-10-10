#!/usr/bin/env python3

import os
from dataclasses import dataclass
from html import escape
from pathlib import Path
from urllib.parse import quote
from PIL import Image


BADGE_BG = "30363d"
BADGE_ACCENT = "7c6ff7"
COLUMNS = 2
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif", ".bmp", ".tif", ".tiff"}
ROOT = Path(__file__).resolve().parents[2]
README_DIR = ROOT / ".github"
README_FILE = README_DIR / "README.md"
REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "kharkwalsuraj/wallpapers")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")


@dataclass
class StructImg:
    name: str
    source: Path
    dimension: tuple[int, int]


def format_size(size: int) -> str:
    """Format a file size using binary units."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f}{unit}" if unit != "B" else f"{size}B"
        size /= 1024

    return f"{size:.1f}TB"


def badge(key: str, value: str, icon: str = "") -> str:
    """Generate a Shields.io badge."""
    label = quote(key.replace("-", "--"), safe="")
    message = quote(value.replace("-", "--"), safe="")
    logo = (f"&amp;logo={quote(icon, safe='')}&amp;logoColor=white" if icon else "")

    return (
        f"<img src='https://img.shields.io/badge/"
        f"{label}-{message}-{BADGE_ACCENT}"
        f"?style=for-the-badge&amp;labelColor={BADGE_BG}{logo}' "
        f"alt='{escape(key)}: {escape(value, quote=True)}'>"
    )


def preview_url(path: Path) -> str:
    """Return an image path relative to .github/README.md."""
    relative = os.path.relpath(path, start=README_DIR)
    return quote(relative.replace(os.sep, "/"), safe="/")


# TODO: individual downloads.
#
# def download_url(path: Path) -> str:
#     image_path = quote(path.relative_to(ROOT).as_posix(), safe="/")
#     branch = quote(BRANCH, safe="")
#     return (
#         f"https://github.com/{REPOSITORY}/raw/refs/heads/"
#         f"{branch}/{image_path}?download=1"
#     )


def card(image: StructImg) -> str:
    """Generate a wallpaper card that fills its column."""
    width, height = image.dimension
    dimensions = f"{width} × {height}"
    size = format_size(image.source.stat().st_size)
    name = escape(image.name, quote=True)
    source = preview_url(image.source)

    return (
        "<td width='50%' valign='top' "
        "style='width:50%;padding:0;'>"
        f"<a href='{source}'>"
        f"<img src='{source}' alt='{name}' "
        "width='100%' "
        "style='display:block;width:100%;height:auto;border:0;'>"
        "</a>"
        "<div align='center'>"
        f"<div>{name}</div>"
        f"<div><code>{dimensions}</code>&nbsp;·&nbsp;"
        f"<code>{size}</code></div>"
        "</div>"
        "</td>"
    )


def gallery(images: list[StructImg]) -> str:
    """Generate a full-width gallery with two equal columns."""
    if not images:
        return "<p>No wallpapers found.</p>"

    rows = []

    for start in range(0, len(images), COLUMNS):
        batch = images[start:start + COLUMNS]
        cells = "".join(card(image) for image in batch)

        if len(batch) < COLUMNS:
            cells += "<td width='50%' style='width:50%;padding:0;'></td>"

        rows.append(f"<tr>{cells}</tr>")

    return (
        "<table width='100%' cellpadding='0' cellspacing='0' border='0' "
        "style='width:100%;max-width:none;table-layout:fixed;"
        "border-collapse:collapse;margin:0;padding:0;'>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


# Find wallpapers.
images = []

for file in ROOT.rglob("*"):
    if not file.is_file():
        continue

    relative_parts = file.relative_to(ROOT).parts

    if any(part in {".git", ".github"} for part in relative_parts):
        continue

    if file.suffix.lower() not in IMAGE_EXTENSIONS:
        continue

    try:
        with Image.open(file) as image:
            dimensions = image.size
    except (OSError, ValueError):
        print(f"Skipping invalid image: {file}")
        continue

    images.append(StructImg(name=file.name, source=file, dimension=dimensions))


# Calculate repository content size, excluding .git and .github.
file_bytes = sum(
    file.stat().st_size
    for file in ROOT.rglob("*")
    if file.is_file()
    and not any(part in {".git", ".github"} for part in file.relative_to(ROOT).parts)
)

# Generate Readme
README_DIR.mkdir(parents=True, exist_ok=True)
repository_zip = (f"https://github.com/{REPOSITORY}/archive/refs/heads/" f"{quote(BRANCH, safe='')}.zip")
content = "\n\n".join((
    "<div align='center'>"
    "<h1>With This Desktop, I Summon...</h1>"
    "<p><i>The finest pixels across heaven and earth.</i></p>"
    "<p>A cursed collection of wallpapers capable of expanding domains, "
    "activating neurons, and destroying your disk space. "
    "Special grade backgrounds only. Nah, I'd touch grass.</p>"
    "</div>",

    "<div align='center'>"
    f"<a href='{repository_zip}'>"
    f"{badge('Repository Size', format_size(file_bytes), 'github')}"
    "</a> "
    f"<a href='{repository_zip}'>"
    f"{badge('Wallpapers', str(len(images)), 'googlephotos')}"
    "</a>"
    "</div>",

    "<h2 align='center'>Domain Expansion: Wallpaper Gallery</h2>",

    gallery(images),
))

README_DIR.mkdir(parents=True, exist_ok=True)
README_FILE.write_text(content + "\n", encoding="utf-8")

print(f"README generated: {README_FILE}")
print(f"Wallpapers: {len(images)}")
print(f"Repository content size: {format_size(file_bytes)}")
