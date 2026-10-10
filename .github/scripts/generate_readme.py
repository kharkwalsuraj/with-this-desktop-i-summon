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
    download_url: str
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
    logo = f"&amp;logo={quote(icon, safe='')}&amp;logoColor=white" if icon else ""

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


def download_url(path: Path) -> str:
    """Build a GitHub download URL."""
    image_path = quote(path.relative_to(ROOT).as_posix(), safe="/")
    branch = quote(BRANCH, safe="")
    return f"https://github.com/{REPOSITORY}/raw/refs/heads/{branch}/{image_path}?download=1"


def card(image: StructImg) -> str:
    """Generate a wallpaper gallery card."""
    dimensions = f"{image.dimension[0]} × {image.dimension[1]}"
    size = format_size(image.source.stat().st_size)
    name = escape(image.name, quote=True)
    source = preview_url(image.source)
    download = image.download_url
    download_badge = badge("download", "PNG", "github")

    return (
        f"<td width='50%' valign='top' align='center'>"
        f"<a href='{download}'><img src='{source}' alt='{name}' width='100%'></a>"
        f"<div align='center'><div>{name}</div>"
        f"<div><code>{dimensions}</code>&nbsp;·&nbsp;<code>{size}</code></div>"
        f"<div><a href='{download}' title='Download {name}'>{download_badge}</a></div>"
        f"</div></td>"
    )


def gallery(images: list[StructImg]) -> str:
    """Generate a full-width, two-column gallery."""
    if not images:
        return "<p>No wallpapers found.</p>"

    rows = []

    for start in range(0, len(images), COLUMNS):
        batch = images[start:start + COLUMNS]
        cells = "".join(card(image) for image in batch)

        if len(batch) < COLUMNS:
            cells += "<td width='50%'></td>"

        rows.append(f"<tr>{cells}</tr>")

    return (
        "<table width='100%' cellpadding='0' cellspacing='0' "
        "style='width:100%;border-collapse:collapse;'>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


png_images = []

for file in ROOT.rglob("*"):
    if not file.is_file():
        continue

    if any(part in {".git", ".github"} for part in file.relative_to(ROOT).parts):
        continue

    if file.suffix.lower() not in IMAGE_EXTENSIONS:
        continue

    try:
        # Keep existing PNGs.
        if file.suffix.lower() == ".png":
            with Image.open(file) as img:
                width, height = img.size

            png_images.append(StructImg(
                name=file.name,
                source=file,
                download_url=download_url(file),
                dimension=(width, height),
            ))
            continue

        # Convert non-PNG images to PNG.
        png_path = file.with_suffix(".png")

        if png_path.exists():
            print(f"Skipped {file.name}: {png_path.name} already exists")
            continue

        with Image.open(file) as img:
            img.load()

            if img.mode not in {"RGB", "RGBA"}:
                img = img.convert("RGBA" if "transparency" in img.info else "RGB")

            img.save(png_path, format="PNG")

        # Verify the converted PNG before deleting the original.
        with Image.open(png_path) as img:
            img.verify()

        with Image.open(png_path) as img:
            width, height = img.size

        # Delete the non-PNG file after successful conversion.
        file.unlink()

        png_images.append(StructImg(
            name=png_path.name,
            source=png_path,
            download_url=download_url(png_path),
            dimension=(width, height),
        ))

    except Exception as exc:
        print(f"Failed to process {file.name}: {exc}")


# Calculate the total repository content size after conversion.
file_bytes = sum(
    file.stat().st_size
    for file in ROOT.rglob("*")
    if file.is_file()
    and not any(part in {".git", ".github"} for part in file.relative_to(ROOT).parts)
)


# Generate Readme
content = "\n\n".join((
    "<div align='center'>"
    "<h1>With This Desktop, I Summon...</h1>"
    "<p><i>The finest pixels across heaven and earth.</i></p>"
    "<p>A cursed collection of wallpapers capable of expanding domains, "
    "activating neurons, and destroying your disk space. "
    "Special grade backgrounds only. Nah, I'd touch grass.</p>"
    "</div>",
    "<div align='center'>"
    f"{badge('Repository Size', format_size(file_bytes), 'github')} "
    f"{badge('Wallpapers', str(len(png_images)), 'googlephotos')}"
    "</div>",
    "<h2 align='center'>Domain Expansion: Wallpaper Gallery</h2>",
    gallery(png_images),
))

README_FILE.write_text(content + "\n", encoding="utf-8")

print(f"README generated: {README_FILE}")
print(f"Wallpapers: {len(png_images)}")
print(f"Repository content size: {format_size(file_bytes)}")
