"""Generate a fictitious colour "scan" for the MRC compression demo.

The pages mix what MRC is designed for: black and coloured text, a photo-like
picture, flat colour areas and a slightly tinted, noisy paper background. Each
page is a single JPEG image (like the output of an office scanner in colour
mode), so the PDF has no text layer.

Every name and figure is invented.

Usage:
    python generate_color_scan.py [output.pdf]
"""

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

DPI = 200
PAGE_W, PAGE_H = int(8.5 * DPI), int(11 * DPI)  # US Letter
M = int(0.75 * DPI)
INK = (28, 30, 36)
ACCENT = (0, 98, 155)
WARM = (214, 92, 40)

FONTS = {
    "regular": ["/System/Library/Fonts/Supplemental/Georgia.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf", "C:/Windows/Fonts/georgia.ttf"],
    "bold": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"],
    "sans": ["/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
             "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "C:/Windows/Fonts/arial.ttf"],
}

TEXT = [
    "The coastal trail opened in spring after two years of work by local volunteers. It follows the shoreline for "
    "twenty-three kilometres, from the old harbour to the lighthouse at the northern point, and is marked every five "
    "hundred metres with a small wooden post.",
    "Most walkers complete the route in two days, with a night in the village halfway along. The path is level for "
    "most of its length, but the section below the cliffs can be closed at high tide. Check the tide table at the "
    "information point before you set off.",
    "Along the way you will pass three sandy beaches, a nature reserve where seabirds nest from April to July, and "
    "the ruins of a nineteenth-century fishing station. Benches and drinking water are available at each beach.",
    "Dogs are welcome on a lead. Please take your litter home and keep to the marked path, as the dunes are fragile "
    "and protected. Cycling is not allowed on the cliff section.",
]


def font(kind, pt):
    size = int(pt * DPI / 72)
    for p in FONTS[kind]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size=size)


def wrap(d, text, f, width):
    lines, line = [], ""
    for w in text.split():
        t = (line + " " + w).strip()
        if d.textlength(t, font=f) > width:
            lines.append(line)
            line = w
        else:
            line = t
    return lines + [line] if line else lines


def landscape(w, h, rng):
    """A photo-like picture: sky gradient, sun, hills, sea and grain."""
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        t = y / h
        sky = (int(70 + 120 * t), int(130 + 90 * t), int(200 + 40 * t))
        for x in range(w):
            px[x, y] = sky
    d = ImageDraw.Draw(img)
    d.ellipse([w * 0.68, h * 0.12, w * 0.82, h * 0.12 + w * 0.14], fill=(255, 214, 120))
    for layer, (col, base, amp) in enumerate([((70, 120, 90), 0.55, 0.10), ((45, 95, 70), 0.65, 0.08)]):
        pts = [(0, h)]
        for x in range(0, w + 20, 20):
            pts.append((x, h * base - amp * h * math.sin(x / w * (3 + layer) + layer)))
        pts.append((w, h))
        d.polygon(pts, fill=col)
    d.rectangle([0, h * 0.78, w, h], fill=(40, 110, 160))
    for i in range(14):
        y = h * 0.8 + i * h * 0.014
        d.line([(rng.uniform(0, w * 0.3), y), (rng.uniform(w * 0.5, w), y)], fill=(170, 210, 230), width=2)
    noise = Image.effect_noise((w, h), 18).convert("RGB")
    return Image.blend(img, noise, 0.08).filter(ImageFilter.GaussianBlur(1.2))


def page_one(rng):
    img = Image.new("RGB", (PAGE_W, PAGE_H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, PAGE_W, int(1.05 * DPI)], fill=ACCENT)
    d.text((M, int(0.25 * DPI)), "EXAMPLE COAST", font=font("bold", 28), fill=(255, 255, 255))
    d.text((M, int(0.72 * DPI)), "Visitor guide  |  Fictitious sample for a Nutrient demo", font=font("sans", 10),
           fill=(210, 230, 245))
    y = int(1.35 * DPI)
    d.text((M, y), "A new trail along the coast", font=font("bold", 22), fill=INK)
    y += int(0.5 * DPI)
    photo_h = int(3.2 * DPI)
    img.paste(landscape(PAGE_W - 2 * M, photo_h, rng), (M, y))
    y += photo_h + int(0.08 * DPI)
    d.text((M, y), "View from the northern point at sunrise.", font=font("sans", 8.5), fill=(90, 95, 105))
    y += int(0.35 * DPI)
    col_w = (PAGE_W - 2 * M - int(0.3 * DPI)) // 2
    f = font("regular", 10.5)
    lh = int(10.5 * DPI / 72 * 1.45)
    cols = [TEXT[:2], TEXT[2:]]
    for c, paras in enumerate(cols):
        x, yy = M + c * (col_w + int(0.3 * DPI)), y
        for p in paras:
            for line in wrap(d, p, f, col_w):
                d.text((x, yy), line, font=f, fill=INK)
                yy += lh
            yy += lh // 2
    box_y = PAGE_H - int(2.3 * DPI)
    d.rounded_rectangle([M, box_y, PAGE_W - M, box_y + int(1.4 * DPI)], radius=30, fill=(253, 236, 222))
    d.text((M + 40, box_y + 30), "Practical information", font=font("bold", 13), fill=WARM)
    info = ["Length: 23 km, about 7 hours of walking", "Start: Old harbour car park, Exampleton",
            "Information point: open daily 9:00 to 17:00"]
    for i, line in enumerate(info):
        d.text((M + 40, box_y + 95 + i * 62), line, font=font("sans", 11), fill=INK)
    return img


def page_two(rng):
    img = Image.new("RGB", (PAGE_W, PAGE_H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, PAGE_W, int(0.35 * DPI)], fill=ACCENT)
    y = int(0.75 * DPI)
    d.text((M, y), "Trail sections", font=font("bold", 20), fill=INK)
    y += int(0.55 * DPI)
    rows = [("Section", "Distance", "Time", "Difficulty"),
            ("Old harbour to Sandy Bay", "6.5 km", "2 h", "Easy"),
            ("Sandy Bay to the village", "5.0 km", "1 h 30", "Easy"),
            ("Village to the cliffs", "6.0 km", "2 h", "Moderate"),
            ("Cliffs to the lighthouse", "5.5 km", "1 h 45", "Moderate")]
    widths = [int(3.3 * DPI), int(1.2 * DPI), int(1.0 * DPI), int(1.4 * DPI)]
    rh = int(0.42 * DPI)
    for r, row in enumerate(rows):
        x = M
        if r == 0:
            d.rectangle([M, y, M + sum(widths), y + rh], fill=ACCENT)
        elif r % 2 == 0:
            d.rectangle([M, y, M + sum(widths), y + rh], fill=(232, 241, 248))
        for c, cell in enumerate(row):
            d.text((x + 20, y + rh * 0.25), cell, font=font("bold" if r == 0 else "sans", 11),
                   fill=(255, 255, 255) if r == 0 else INK)
            x += widths[c]
        y += rh
    y += int(0.4 * DPI)
    # Simple bar chart of visitors per month.
    d.text((M, y), "Visitors per month (thousands)", font=font("bold", 13), fill=INK)
    y += int(0.45 * DPI)
    values = [3.2, 4.1, 6.8, 9.5, 12.4, 14.9, 13.6, 9.8]
    months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov"]
    chart_h = int(2.2 * DPI)
    bw = int(0.55 * DPI)
    for i, (v, m) in enumerate(zip(values, months)):
        x = M + int(0.2 * DPI) + i * int(0.85 * DPI)
        h = int(chart_h * v / 16)
        d.rectangle([x, y + chart_h - h, x + bw, y + chart_h], fill=WARM if v == max(values) else ACCENT)
        d.text((x, y + chart_h + 12), m, font=font("sans", 9.5), fill=INK)
        d.text((x, y + chart_h - h - 40), f"{v:.1f}", font=font("sans", 9), fill=INK)
    d.line([M, y + chart_h, PAGE_W - M, y + chart_h], fill=INK, width=3)
    y += chart_h + int(0.6 * DPI)
    f = font("regular", 10.5)
    for p in TEXT[2:]:
        for line in wrap(d, p, f, PAGE_W - 2 * M):
            d.text((M, y), line, font=f, fill=INK)
            y += int(10.5 * DPI / 72 * 1.45)
        y += int(0.1 * DPI)
    return img


def scanned(img, rng):
    """Paper tint, slight rotation, blur and sensor noise, like a colour office scan."""
    paper = Image.new("RGB", img.size, (250, 246, 236))
    img = Image.blend(img, paper, 0.12)
    img = img.rotate(rng.uniform(-0.6, 0.6), resample=Image.BICUBIC, fillcolor=(250, 246, 236))
    noise = Image.effect_noise(img.size, 10).convert("RGB")
    img = Image.blend(img, noise, 0.04)
    return img.filter(ImageFilter.GaussianBlur(0.6))


def build(out: Path):
    rng = random.Random(7)
    pages = [scanned(page_one(rng), rng), scanned(page_two(rng), rng)]
    pages[0].save(out, save_all=True, append_images=pages[1:], resolution=DPI, quality=80)
    print(f"Wrote {out} ({len(pages)} pages, {out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("color-scan-sample.pdf"))
