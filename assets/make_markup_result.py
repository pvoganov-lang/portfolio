"""Иллюстрация «макет → готовая вёрстка» для услуги вёрстки.

Создаёт markup-result.png (1200×675).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
FONT_DIR = Path("/System/Library/Fonts/Supplemental")

BG = (23, 19, 16)
PANEL = (250, 246, 241)
ACCENT = (200, 96, 47)
LIGHT = (243, 236, 228)
MUTED = (150, 138, 126)
LINE = (120, 108, 96)


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def badge(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, color) -> None:
    f = font("Arial Bold.ttf", 18)
    width = int(draw.textlength(text, font=f)) + 28
    draw.rounded_rectangle((x, y, x + width, y + 34), radius=17, fill=color)
    draw.text((x + 14, y + 7), text, font=f, fill=(255, 255, 255))


def specs(draw: ImageDraw.ImageDraw, x: int, y: int, box) -> None:
    """Размерные линии, как в Figma."""
    x1, y1, x2, y2 = box
    draw.line([(x1, y1 - 14), (x2, y1 - 14)], fill=ACCENT, width=1)
    draw.line([(x1, y1 - 18), (x1, y1 - 10)], fill=ACCENT, width=1)
    draw.line([(x2, y1 - 18), (x2, y1 - 10)], fill=ACCENT, width=1)
    text = f"{x2 - x1}"
    f = font("Arial Bold.ttf", 12)
    tw = draw.textlength(text, font=f)
    draw.rectangle((x1 + (x2 - x1) / 2 - tw / 2 - 6, y1 - 26, x1 + (x2 - x1) / 2 + tw / 2 + 6, y1 - 6), fill=BG)
    draw.text((x1 + (x2 - x1) / 2 - tw / 2, y1 - 24), text, font=f, fill=ACCENT)


def main() -> None:
    w, h = 1200, 675
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)

    for x in range(0, w, 40):
        draw.line([(x, 0), (x, h)], fill=(30, 25, 21))
    for y in range(0, h, 40):
        draw.line([(0, y), (w, y)], fill=(30, 25, 21))

    draw.text((44, 34), "Макет → готовая вёрстка", font=font("Arial Black.ttf", 34), fill=LIGHT)
    draw.text((44, 84), "адаптив, pixel perfect, чистый HTML/CSS", font=font("Arial Bold.ttf", 16), fill=MUTED)

    # ---------- Макет ----------
    lx, ly, lw, lh = 44, 150, 520, 430
    draw.rounded_rectangle((lx, ly, lx + lw, ly + lh), radius=16, fill=(236, 232, 226))
    draw.rectangle((lx, ly, lx + lw, ly + 30), fill=(214, 206, 196))
    draw.text((lx + 14, ly + 6), "Frame 1440 · Desktop", font=font("Arial Bold.ttf", 14), fill=(90, 76, 64))

    # wireframe
    draw.rectangle((lx + 24, ly + 52, lx + 300, ly + 70), fill=(160, 148, 136))
    draw.rectangle((lx + 24, ly + 86, lx + 470, ly + 100), fill=(190, 180, 168))
    draw.rectangle((lx + 24, ly + 108, lx + 430, ly + 120), fill=(190, 180, 168))
    specs(draw, lx + 24, ly + 52, (lx + 24, ly + 52, lx + 300, ly + 70))

    for i in range(3):
        bx = lx + 24 + i * 160
        draw.rectangle((bx, ly + 156, bx + 144, ly + 252), fill=(220, 212, 202))
        draw.rectangle((bx + 12, ly + 170, bx + 100, ly + 180), fill=(160, 148, 136))
        draw.rectangle((bx + 12, ly + 196, bx + 128, ly + 204), fill=(190, 180, 168))

    draw.rounded_rectangle((lx + 24, ly + 286, lx + 150, ly + 326), radius=20, fill=(180, 168, 156))
    draw.text((lx + 46, ly + 296), "Кнопка", font=font("Arial Bold.ttf", 16), fill=(255, 255, 255))

    # сетка колонок
    for col in range(12):
        x = lx + 24 + col * 38
        draw.line([(x, ly + 350), (x, ly + 404)], fill=(206, 196, 186), width=6)

    badge(draw, lx + lw - 110, ly + 12, "МАКЕТ", (120, 108, 96))

    # ---------- Стрелка ----------
    draw.line([(lx + lw + 10, 365), (lx + lw + 46, 365)], fill=ACCENT, width=4)
    draw.polygon([(lx + lw + 46, 365), (lx + lw + 32, 357), (lx + lw + 32, 373)], fill=ACCENT)

    # ---------- Вёрстка ----------
    rx = lx + lw + 56
    rw = w - rx - 44
    draw.rounded_rectangle((rx, ly, rx + rw, ly + lh), radius=16, fill=PANEL)
    draw.rectangle((rx, ly, rx + rw, ly + 30), fill=(232, 222, 212))
    for i, color in enumerate([(220, 120, 100), (230, 190, 110), (140, 190, 140)]):
        draw.ellipse((rx + 14 + i * 16, ly + 10, rx + 24 + i * 16, ly + 20), fill=color)

    # готовый сайт
    draw.rectangle((rx + 24, ly + 52, rx + 330, ly + 74), fill=(40, 32, 26))
    draw.rectangle((rx + 24, ly + 88, rx + rw - 30, ly + 100), fill=(196, 184, 172))
    draw.rectangle((rx + 24, ly + 110, rx + rw - 90, ly + 122), fill=(196, 184, 172))

    for i in range(3):
        bx = rx + 24 + i * 146
        draw.rounded_rectangle((bx, ly + 152, bx + 132, ly + 254), radius=10, fill=(240, 234, 226))
        draw.rectangle((bx + 14, ly + 168, bx + 96, ly + 178), fill=(90, 76, 64))
        draw.rectangle((bx + 14, ly + 194, bx + 118, ly + 204), fill=(196, 184, 172))
        draw.rectangle((bx + 14, ly + 212, bx + 104, ly + 222), fill=(196, 184, 172))

    draw.rounded_rectangle((rx + 24, ly + 284, rx + 160, ly + 328), radius=22, fill=ACCENT)
    draw.text((rx + 48, ly + 295), "Записаться", font=font("Arial Bold.ttf", 17), fill=(255, 255, 255))

    draw.rectangle((rx + 24, ly + 348, rx + rw - 40, ly + 360), fill=(196, 184, 172))
    draw.rectangle((rx + 24, ly + 372, rx + rw - 90, ly + 384), fill=(196, 184, 172))

    badge(draw, rx + rw - 130, ly + 12, "ВЁРСТКА", (86, 160, 110))

    # ---------- подписи снизу ----------
    f = font("Arial Bold.ttf", 17)
    draw.text((44, 600), "Figma / PSD", font=f, fill=MUTED)
    draw.text((rx, 600), "HTML + CSS + JS", font=f, fill=MUTED)
    draw.text((44, 628), "3 разрешения: 360 / 768 / 1440", font=font("Arial Bold.ttf", 15), fill=(110, 100, 90))

    path = HERE / "markup-result.png"
    img.save(path)
    print("создано:", path.name)


if __name__ == "__main__":
    main()
