"""Генерация обложек для карточек на Kwork/FL.ru и аватара профиля.

Запуск:
    python make_covers.py

Создаёт в этой папке:
    avatar.png        400×400  — аватар профиля
    cover-landing.png 760×480  — обложка «Лендинг под ключ»
    cover-bot.png     760×480  — обложка «Telegram-бот записи»
    cover-report.png  760×480  — обложка «Отчёт по продажам в Excel»
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent

BG = (23, 19, 16)
BG_SOFT = (36, 29, 24)
ACCENT = (200, 96, 47)
LIGHT = (243, 236, 228)
MUTED = (185, 169, 155)

FONT_DIR = Path("/System/Library/Fonts/Supplemental")
FONT_BLACK = FONT_DIR / "Arial Black.ttf"
FONT_BOLD = FONT_DIR / "Arial Bold.ttf"


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def draw_tracked(draw: ImageDraw.ImageDraw, xy, text: str, fnt, fill, tracking: int = 2) -> None:
    """Текст с увеличенным межбуквенным интервалом (для плашек)."""
    x, y = xy
    for char in text:
        draw.text((x, y), char, font=fnt, fill=fill)
        x += draw.textlength(char, font=fnt) + tracking


def rounded(draw: ImageDraw.ImageDraw, box, radius: int, fill=None, outline=None, width: int = 1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def base_canvas(w: int = 760, h: int = 480) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)

    # мягкое свечение справа
    for radius in range(340, 0, -8):
        alpha = int(38 * (1 - radius / 340))
        colour = (
            min(255, BG[0] + alpha // 2),
            min(255, BG[1] + alpha // 3),
            min(255, BG[2] + alpha // 5),
        )
        draw.ellipse(
            (w - radius - 40, -radius + 60, w + radius - 40, radius + 60),
            fill=colour,
        )

    # тонкая сетка
    for x in range(0, w, 40):
        draw.line([(x, 0), (x, h)], fill=(30, 25, 21), width=1)
    for y in range(0, h, 40):
        draw.line([(0, y), (w, y)], fill=(30, 25, 21), width=1)

    return img, draw


def header(draw: ImageDraw.ImageDraw, label: str) -> None:
    f_label = font(FONT_BOLD, 12)
    rounded(draw, (44, 38, 44 + 22 + int(draw.textlength(label, font=f_label)) + 22, 38 + 26), 13, outline=ACCENT, width=1)
    draw_tracked(draw, (57, 44), label, f_label, ACCENT, tracking=2)


def footer_chips(draw: ImageDraw.ImageDraw, items: list[str]) -> None:
    f_chip = font(FONT_BOLD, 15)
    x, y = 44, 408
    for item in items:
        width = int(draw.textlength(item, font=f_chip)) + 34
        rounded(draw, (x, y, x + width, y + 38), 19, fill=BG_SOFT, outline=(60, 50, 42), width=1)
        draw.text((x + 17, y + 10), item, font=f_chip, fill=LIGHT)
        x += width + 10


# --------------------------------------------------------------------------
# Иллюстрации
# --------------------------------------------------------------------------

def art_browser(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    """Окно браузера."""
    rounded(draw, (x, y, x + 300, y + 250), 18, fill=(250, 246, 241))
    rounded(draw, (x, y, x + 300, y + 40), 18, fill=(232, 222, 212))
    draw.rectangle((x, y + 24, x + 300, y + 40), fill=(232, 222, 212))
    for i, color in enumerate([(220, 120, 100), (230, 190, 110), (140, 190, 140)]):
        draw.ellipse((x + 16 + i * 18, y + 14, x + 26 + i * 18, y + 24), fill=color)
    draw.rectangle((x + 24, y + 62, x + 170, y + 78), fill=(60, 48, 38))
    draw.rectangle((x + 24, y + 92, x + 260, y + 104), fill=(196, 184, 172))
    draw.rectangle((x + 24, y + 112, x + 220, y + 124), fill=(196, 184, 172))
    rounded(draw, (x + 24, y + 146, x + 120, y + 180), 17, fill=ACCENT)
    rounded(draw, (x + 140, y + 146, x + 236, y + 180), 17, outline=(196, 184, 172), width=2)
    for i in range(3):
        rounded(draw, (x + 24 + i * 84, y + 200, x + 92 + i * 84, y + 232), 8, fill=(226, 216, 206))


def art_chat(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    """Диалог в мессенджере."""
    rounded(draw, (x + 10, y + 10, x + 250, y + 90), 20, fill=BG_SOFT, outline=(70, 58, 48), width=1)
    draw.polygon([(x + 40, y + 90), (x + 40, y + 112), (x + 70, y + 90)], fill=BG_SOFT)
    draw.rectangle((x + 34, y + 36, x + 180, y + 48), fill=MUTED)
    draw.rectangle((x + 34, y + 58, x + 210, y + 70), fill=(120, 104, 90))

    rounded(draw, (x + 70, y + 140, x + 310, y + 228), 20, fill=ACCENT)
    draw.polygon([(x + 280, y + 228), (x + 280, y + 252), (x + 250, y + 228)], fill=ACCENT)
    draw.rectangle((x + 94, y + 166, x + 250, y + 178), fill=(255, 245, 238))
    draw.rectangle((x + 94, y + 190, x + 200, y + 202), fill=(255, 220, 200))

    for i, label in enumerate(["Записаться", "Мои записи"]):
        rounded(draw, (x + 20 + i * 130, y + 268, x + 130 + i * 130, y + 304), 18, fill=BG_SOFT, outline=(80, 66, 54), width=1)
        draw.text((x + 36 + i * 130, y + 280), label, font=font(FONT_BOLD, 14), fill=LIGHT)


def art_chart(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    """Таблица с графиком."""
    rounded(draw, (x, y, x + 320, y + 250), 16, fill=(248, 244, 238))

    # шапка таблицы
    rounded(draw, (x, y, x + 320, y + 34), 16, fill=(32, 26, 22))
    draw.rectangle((x, y + 18, x + 320, y + 34), fill=(32, 26, 22))

    for i in range(4):
        draw.rectangle((x + 18 + (i % 2) * 120, y + 46 + (i // 2) * 22, x + 118 + (i % 2) * 120, y + 58 + (i // 2) * 22), fill=(120, 108, 96))

    # столбцы диаграммы
    heights = [56, 84, 68, 104, 88]
    for i, height in enumerate(heights):
        left = x + 30 + i * 50
        draw.rectangle((left, y + 210 - height, left + 30, y + 210), fill=ACCENT if i == 3 else (214, 198, 186))

    # линия тренда
    points = [(x + 45 + i * 50, y + 210 - h) for i, h in enumerate(heights)]
    draw.line(points, fill=(90, 74, 60), width=3, joint="curve")
    for point in points:
        draw.ellipse((point[0] - 4, point[1] - 4, point[0] + 4, point[1] + 4), fill=BG)


def art_edit(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    """Макет с выделенным блоком и курсором — про правки."""
    rounded(draw, (x, y, x + 320, y + 250), 18, fill=(250, 246, 241))
    rounded(draw, (x, y, x + 320, y + 38), 18, fill=(232, 222, 212))
    draw.rectangle((x, y + 22, x + 320, y + 38), fill=(232, 222, 212))

    draw.rectangle((x + 26, y + 62, x + 150, y + 76), fill=(60, 48, 38))
    draw.rectangle((x + 26, y + 90, x + 280, y + 102), fill=(196, 184, 172))

    # блок, который «правят»
    rounded(draw, (x + 26, y + 126, x + 200, y + 200), 12, fill=(240, 214, 198))
    for i in range(4):
        for dash in range(0, 174, 12):
            draw.rectangle((x + 26 + dash, y + 126 + i * 22 if i < 4 else 0, x + 34 + dash, y + 130 + i * 22), fill=(0,0,0,0))

    draw.rectangle((x + 40, y + 144, x + 170, y + 156), fill=(200, 96, 47))
    draw.rectangle((x + 40, y + 166, x + 140, y + 176), fill=(176, 128, 100))

    # курсор
    cx, cy = x + 206, y + 178
    draw.polygon([(cx, cy), (cx + 26, cy + 12), (cx + 15, cy + 15), (cx + 20, cy + 30), (cx + 13, cy + 33), (cx + 8, cy + 18), (cx, cy + 24)], fill=(36, 29, 24))

    draw.rectangle((x + 240, y + 62, x + 296, y + 74), fill=(200, 96, 47))
    for i in range(3):
        rounded(draw, (x + 26 + i * 92, y + 216, x + 100 + i * 92, y + 236), 8, fill=(226, 216, 206))


def art_markup(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    """Макет → код: два слоя."""
    # макет
    rounded(draw, (x, y + 30, x + 190, y + 200), 14, fill=(240, 234, 226))
    draw.rectangle((x + 18, y + 52, x + 120, y + 64), fill=(120, 104, 90))
    draw.rectangle((x + 18, y + 78, x + 160, y + 88), fill=(180, 168, 156))
    draw.rectangle((x + 18, y + 98, x + 140, y + 108), fill=(180, 168, 156))
    rounded(draw, (x + 18, y + 126, x + 96, y + 158), 14, fill=(200, 96, 47))

    # код
    rounded(draw, (x + 130, y + 90, x + 330, y + 260), 14, fill=(28, 24, 20))
    for i in range(6):
        width = [110, 80, 140, 60, 120, 90][i]
        color = (200, 96, 47) if i in (0, 3) else (150, 140, 130)
        draw.rectangle((x + 152, y + 112 + i * 22, x + 152 + width, y + 120 + i * 22), fill=color)


# --------------------------------------------------------------------------
# Обложки
# --------------------------------------------------------------------------

def make_cover(name: str, label: str, title_lines: list[str], bullets: list[str],
               chips: list[str], art) -> None:
    img, draw = base_canvas()
    header(draw, label)

    f_title = font(FONT_BLACK, 40)
    y = 96
    for line in title_lines:
        draw.text((44, y), line, font=f_title, fill=LIGHT)
        y += 48

    f_bullet = font(FONT_BOLD, 16)
    y += 14
    for item in bullets:
        draw.ellipse((46, y + 7, 54, y + 15), fill=ACCENT)
        draw.text((68, y), item, font=f_bullet, fill=MUTED)
        y += 30

    art(draw, 400, 150)
    footer_chips(draw, chips)

    path = HERE / f"{name}.png"
    img.save(path)
    print("создано:", path.name)


def make_avatar() -> None:
    size = 400
    img = Image.new("RGB", (size, size), BG)
    draw = ImageDraw.Draw(img)

    for radius in range(200, 0, -6):
        alpha = int(60 * (1 - radius / 200))
        draw.ellipse(
            (size // 2 - radius, size // 2 - radius, size // 2 + radius, size // 2 + radius),
            fill=(23 + alpha, 19 + alpha // 2, 16 + alpha // 4),
        )

    rounded(draw, (110, 110, 290, 290), 44, fill=ACCENT)
    f_mono = font(FONT_BLACK, 120)
    text = "П"
    width = draw.textlength(text, font=f_mono)
    draw.text(((size - width) / 2, 128), text, font=f_mono, fill=LIGHT)

    path = HERE / "avatar.png"
    img.save(path)
    print("создано:", path.name)


def make_portfolio_cover() -> None:
    """Обложка для профиля (показывает все три услуги)."""
    img, draw = base_canvas(1200, 630)
    header(draw, "ПОРТФОЛИО · IT-УСЛУГИ")

    f_title = font(FONT_BLACK, 62)
    draw.text((44, 96), "Сайты, боты", font=f_title, fill=LIGHT)
    draw.text((44, 168), "и автоматизация", font=f_title, fill=ACCENT)

    f_sub = font(FONT_BOLD, 20)
    draw.text((46, 268), "для малого бизнеса — под ключ", font=f_sub, fill=MUTED)

    items = [
        ("01", "Лендинги", "адаптив, формы, анимации"),
        ("02", "Telegram-боты", "запись, магазин, уведомления"),
        ("03", "Автоматизация", "Excel-отчёты, парсинг, таблицы"),
    ]

    f_num = font(FONT_BLACK, 22)
    f_item = font(FONT_BOLD, 22)
    f_desc = font(FONT_BOLD, 15)

    y = 340
    for num, title, desc in items:
        rounded(draw, (44, y, 560, y + 76), 16, fill=BG_SOFT, outline=(58, 48, 40), width=1)
        draw.text((64, y + 24), num, font=f_num, fill=ACCENT)
        draw.text((116, y + 12), title, font=f_item, fill=LIGHT)
        draw.text((116, y + 44), desc, font=f_desc, fill=MUTED)
        y += 88

    art_browser(draw, 700, 120)
    art_chart(draw, 830, 380)

    path = HERE / "cover-profile.png"
    img.save(path)
    print("создано:", path.name)


if __name__ == "__main__":
    make_avatar()
    make_cover(
        "cover-landing",
        "WEB · ЛЕНДИНГ",
        ["Лендинг", "под ключ"],
        ["адаптив под телефон", "форма с проверкой", "без конструкторов"],
        ["HTML · CSS · JS", "адаптив 3 разрешения"],
        art_browser,
    )
    make_cover(
        "cover-bot",
        "TELEGRAM · БОТ",
        ["Бот записи", "клиентов"],
        ["выбор услуги и времени", "база записей", "уведомления вам"],
        ["Python · aiogram", "SQLite · уведомления"],
        art_chat,
    )
    make_cover(
        "cover-report",
        "EXCEL · ОТЧЁТЫ",
        ["Отчёт", "по продажам"],
        ["выручка и средний чек", "графики и срезы", "запуск по кнопке"],
        ["pandas · XlsxWriter", "графики в Excel"],
        art_chart,
    )
    make_cover(
        "cover-edits",
        "САЙТ · ПРАВКИ",
        ["Правки", "и доработки"],
        ["тексты и цвета", "фото и кнопки", "мобильная версия"],
        ["HTML · CSS", "мобильная версия"],
        art_edit,
    )
    make_cover(
        "cover-markup",
        "ВЁРСТКА · МАКЕТ",
        ["Вёрстка", "по макету"],
        ["HTML и CSS", "адаптив под телефон", "pixel perfect"],
        ["Figma / PSD", "pixel perfect"],
        art_markup,
    )
    make_portfolio_cover()
