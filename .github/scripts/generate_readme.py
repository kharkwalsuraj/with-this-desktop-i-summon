#!/usr/bin/env python3


import os


from html import escape
from pathlib import Path
from urllib.parse import quote
from PIL import Image


BADGE_BG = "30363d"
BADGE_ACCENT = "7c6ff7"
REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "kharkwalsuraj/wallpapers")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif", ".bmp", ".tif", ".tiff"}
ROOT = Path(__file__).resolve().parents[2]
README_DIR = ROOT / ".github"
README_FILE = README_DIR / "README.md"
COLUMNS = 2
FALLBACK_ASPECT_RATIO = 16 / 9


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
    logo = f"&amp;logo={quote(icon, safe='')}&amp;logoColor=white" if icon else ""

    return (
        f"<img src='https://img.shields.io/badge/"
        f"{label}-{message}-{BADGE_ACCENT}"
        f"?style=for-the-badge&amp;labelColor={BADGE_BG}{logo}' "
        f"alt='{escape(key)}: {escape(value, quote=True)}'>"
    )


def ensure_png(image_path: Path) -> Path:
    """Convert an image to PNG and return its final path."""
    image_path = Path(image_path)

    with Image.open(image_path) as image:
        if image.format == "PNG":
            return image_path

        image.load()
        has_alpha = ("A" in image.getbands() or "transparency" in image.info)
        converted = image.convert("RGBA" if has_alpha else "RGB")

    png_path = image_path.with_suffix(".png")

    if png_path.exists():
        raise FileExistsError(f"Cannot convert {image_path}: {png_path} already exists")

    converted.save(png_path, format="PNG")
    image_path.unlink()

    return png_path


def get_images() -> list[Path]:
    """Find repository images, convert them to PNG, and return their paths."""
    images = []

    for directory, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in {".git", ".github"}]

        for name in names:
            path = Path(directory) / name

            if path.suffix.lower() in IMAGE_EXTENSIONS:
                images.append(ensure_png(path))

    return images


def get_files() -> list[Path]:
    """List repository files excluding Git internals and .github."""
    files = []

    for directory, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in {".git", ".github"}]
        files.extend(Path(directory) / name for name in names)

    return files


def image_dimensions(path: Path) -> tuple[int, int]:
    """Return the image width and height."""
    with Image.open(path) as image:
        return image.size

def get_images() -> list[Path]:
    """Find all repository images, convert them to PNG, and return their paths."""
    images = []

    for directory, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in {".git", ".github"}]

        for name in names:
            path = Path(directory) / name

            if path.suffix.lower() in IMAGE_EXTENSIONS:
                images.append(ensure_png(path))

    return images

def preview_url(path: Path) -> str:
    """Return an image path relative to .github/README.md."""
    relative = os.path.relpath(path, start=README_DIR)
    return quote(relative.replace(os.sep, "/"), safe="/")


def download_url(path: Path) -> str:
    """Build a GitHub download URL."""
    image_path = quote(path.relative_to(ROOT).as_posix(), safe="/")
    branch = quote(BRANCH, safe="")
    return f"https://github.com/{REPOSITORY}/raw/refs/heads/{branch}/{image_path}?download=1"


def overview(files: list[Path], images: list[Path]) -> str:
    """Generate repository statistics."""
    size = sum(path.stat().st_size for path in files)

    return (
        "<div align='center'>"
        f"{badge('Repository Size', format_size(size), 'github')} "
        f"{badge('Wallpapers', str(len(images)), 'googlephotos')}"
        "</div>"
    )


def card(path: Path) -> str:
    """Generate a wallpaper card with stable image dimensions."""
    name = escape(path.name, quote=True)
    source = escape(preview_url(path), quote=True)
    download = escape(download_url(path), quote=True)
    size = format_size(path.stat().st_size)

    try:
        width, height = image_dimensions(path)
        if width <= 0 or height <= 0:
            raise ValueError("Invalid image dimensions")
        dimensions = f"{width:,} × {height:,}"
    except (OSError, ValueError):
        width, height = 1980, 1080
        dimensions = "Unknown dimensions"

    download_badge = badge("Download", "Original")

    return (
        f"<td width='50%' valign='top' align='center'>"
        f"<a href='{source}'><img src='{source}' alt='{name}' width='{width}' height='{height}'></a>"
        f"<div align='center'><div>{name}</div>"
        f"<div><code>{dimensions}</code>&nbsp;·&nbsp;<code>{size}</code></div>"
        f"<div><a href='{download}' title='Download {name}'>{download_badge}</a></div>"
        f"</div></td>"
    )


def gallery(images: list[Path]) -> str:
    """Generate a full-width, two-column gallery."""
    if not images:
        return "<p>No wallpapers found.</p>"

    rows = []

    for start in range(0, len(images), COLUMNS):
        batch = images[start:start + COLUMNS]
        cells = "".join(card(path) for path in batch)

        if len(batch) < COLUMNS:
            cells += "<td width='50%'></td>"

        rows.append(f"<tr>{cells}</tr>")

    return (
        "<table width='100%' cellpadding='0' cellspacing='0' "
        "style='width:100%;border-collapse:collapse;'>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def generate_readme() -> None:
    """Generate .github/README.md."""
    README_DIR.mkdir(parents=True, exist_ok=True)

    images = get_images()

    content = "\n\n".join((
        "<div align='center'>"
        "<h1>With This Desktop, I Summon...</h1>"
        "<p><i>The finest pixels across heaven and earth.</i></p>"
        "<p>A cursed collection of wallpapers capable of expanding domains, "
        "activating neurons, and destroying your disk space. "
        "Special grade backgrounds only. Nah, I'd touch grass.</p>"
        "</div>",
        overview(files, images),
        "<h2 align='center'>Domain Expansion: Wallpaper Gallery</h2>",
        gallery(images),
    ))

    README_FILE.write_text(content + "\n", encoding="utf-8")

if __name__ == "__main__":
    generate_readme()
