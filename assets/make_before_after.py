"""Картинка «до / после» для услуги правок сайта.

Показывает, что именно исправляется: кривая вёрстка → аккуратная.
Создаёт before-after.png (1200×675).
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
BAD = (196, 90, 80)
GOOD = (86, 160, 110)


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def dashed_rect(draw: ImageDraw.ImageDraw, box, dash: int = 10, gap: int = 8,
                fill=(120, 108, 96), width: int = 2) -> None:
    x1, y1, x2, y2 = box
    x = x1
    while x < x2:
        draw.line([(x, y1), (min(x + dash, x2), y1)], fill=fill, width=width)
        draw.line([(x, y2), (min(x + dash, x2), y2)], fill=fill, width=width)
        x += dash + gap
    y = y1
    while y < y2:
        draw.line([(x1, y), (x1, min(y + dash, y2))], fill=fill, width=width)
        draw.line([(x2, y), (x2, min(y + dash, y2))], fill=fill, width=width)
        y += dash + gap


def label(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, color) -> None:
    f = font("Arial Bold.ttf", 18)
    width = int(draw.textlength(text, font=f)) + 28
    draw.rounded_rectangle((x, y, x + width, y + 34), radius=17, fill=color)
    draw.text((x + 14, y + 7), text, font=f, fill=(255, 255, 255))


def main() -> None:
    w, h = 1200, 675
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)

    for x in range(0, w, 40):
        draw.line([(x, 0), (x, h)], fill=(30, 25, 21))
    for y in range(0, h, 40):
        draw.line([(0, y), (w, y)], fill=(30, 25, 21))

    draw.text((44, 34), "Правки сайта: было → стало", font=font("Arial Black.ttf", 34), fill=LIGHT)
    draw.text((44, 84), "пример: мобильная вёрстка и блоки", font=font("Arial Bold.ttf", 16), fill=MUTED)

    # ---------- ДО ----------
    lx, ly, lw, lh = 44, 150, 540, 430
    draw.rounded_rectangle((lx, ly, lx + lw, ly + lh), radius=18, fill=PANEL)
    draw.rectangle((lx, ly, lx + lw, ly + 36), fill=(232, 222, 212))
    draw.rounded_rectangle((lx, ly, lx + lw, ly + 36), radius=18, fill=(232, 222, 212))
    draw.rectangle((lx, ly + 18, lx + lw, ly + 36), fill=(232, 222, 212))

    # кривая вёрстка: разъехавшиеся блоки
    draw.rectangle((lx + 22, ly + 58, lx + 320, ly + 78), fill=(90, 76, 64))
    draw.rectangle((lx + 22, ly + 92, lx + 500, ly + 108), fill=(200, 188, 176))
    draw.rectangle((lx + 22, ly + 116, lx + 470, ly + 130), fill=(200, 188, 176))

    # блок «съехал» и наезжает
    draw.rounded_rectangle((lx + 200, ly + 150, lx + 470, ly + 250), radius=10, fill=(232, 208, 196))
    draw.rectangle((lx + 30, ly + 176, lx + 250, ly + 196), fill=(200, 96, 47))
    draw.rectangle((lx + 240, ly + 210, lx + 430, ly + 226), fill=(176, 128, 100))

    # кнопка не по размеру
    draw.rounded_rectangle((lx + 30, ly + 268, lx + 300, ly + 320), radius=26, fill=(200, 96, 47))
    draw.text((lx + 48, ly + 282), "Записаться", font=font("Arial Bold.ttf", 20), fill=(255, 255, 255))

    # текст вылезает за границы
    draw.text((lx + 30, ly + 340), "Текст вылезает за пределы блока и обрезается", font=font("Arial Bold.ttf", 17), fill=BAD)
    draw.rectangle((lx + 30, ly + 366, lx + 520, ly + 384), fill=(226, 216, 206))

    # «до» — горизонтальная прокрутка
    draw.rectangle((lx + 30, ly + 396, lx + 560, ly + 404), fill=(120, 108, 96))
    draw.ellipse((lx + 470, ly + 390, lx + 500, ly + 410), fill=(90, 76, 64))

    label(draw, lx + 18, ly + 12, "ДО", BAD)

    # ---------- ПОСЛЕ ----------
    rx = 616
    draw.rounded_rectangle((rx, ly, rx + lw, ly + lh), radius=18, fill=PANEL)
    draw.rectangle((rx, ly, rx + lw, ly + 36), fill=(232, 222, 212))
    draw.rounded_rectangle((rx, ly, rx + lw, ly + 36), radius=18, fill=(232, 222, 212))
    draw.rectangle((rx, ly + 18, rx + lw, ly + 36), fill=(232, 222, 212))

    draw.rectangle((rx + 22, ly + 60, rx + 300, ly + 78), fill=(60, 48, 38))
    draw.rectangle((rx + 22, ly + 94, rx + 500, ly + 108), fill=(196, 184, 172))
    draw.rectangle((rx + 22, ly + 118, rx + 460, ly + 132), fill=(196, 184, 172))

    # аккуратные блоки
    for i in range(2):
        bx = rx + 22 + i * 250
        draw.rounded_rectangle((bx, ly + 158, bx + 230, ly + 268), radius=12, fill=(240, 234, 226))
        draw.rectangle((bx + 18, ly + 178, bx + 150, ly + 192), fill=(90, 76, 64))
        draw.rectangle((bx + 18, ly + 206, bx + 200, ly + 218), fill=(196, 184, 172))
        draw.rectangle((bx + 18, ly + 230, bx + 170, ly + 242), fill=(196, 184, 172))

    # ровная кнопка
    draw.rounded_rectangle((rx + 22, ly + 292, rx + 190, ly + 334), radius=21, fill=ACCENT)
    draw.text((rx + 44, ly + 303), "Записаться", font=font("Arial Bold.ttf", 18), fill=(255, 255, 255))

    draw.rectangle((rx + 22, ly + 360, rx + 500, ly + 372), fill=(196, 184, 172))
    draw.rectangle((rx + 22, ly + 384, rx + 440, ly + 396), fill=(196, 184, 172))

    # отметка «всё влезает»
    draw.ellipse((rx + 22, ly + 408, rx + 46, ly + 432), fill=GOOD)
    draw.line([(rx + 28, ly + 420), (rx + 33, ly + 426), (rx + 41, ly + 414)], fill=(255, 255, 255), width=3)
    draw.text((rx + 56, ly + 412), "влезает в экран, без прокрутки", font=font("Arial Bold.ttf", 15), fill=(70, 120, 86))

    label(draw, rx + 18, ly + 12, "ПОСЛЕ", GOOD)

    # стрелка между панелями
    draw.line([(lx + lw + 8, 365), (rx - 8, 365)], fill=ACCENT, width=4)
    draw.polygon([(rx - 8, 365), (rx - 22, 357), (rx - 22, 373)], fill=ACCENT)

    path = HERE / "before-after.png"
    img.save(path)
    print("создано:", path.name)


if __name__ == "__main__":
    main()
