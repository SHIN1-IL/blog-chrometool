#!/usr/bin/env python3
"""Generate Chrome extension icons (16, 48, 128). Requires: pip install pillow"""

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow required: pip install pillow")
    raise SystemExit(1)

ICONS_DIR = Path(__file__).parent.parent / "extension" / "icons"
SIZES = [16, 48, 128]
BG = "#03c75a"
FG = "#ffffff"


def make_icon(size: int) -> Image.Image:
    img = Image.new("RGB", (size, size), BG)
    draw = ImageDraw.Draw(img)
    margin = size // 6
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=size // 8,
        fill="#02a84a",
    )
    text = "AB"
    font_size = max(size // 3, 8)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, (size - th) / 2 - 1), text, fill=FG, font=font)
    return img


def main():
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    for size in SIZES:
        path = ICONS_DIR / f"icon{size}.png"
        make_icon(size).save(path)
        print(f"Created {path}")


if __name__ == "__main__":
    main()
