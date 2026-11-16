"""Генератор демо-данных для отчёта.

Создаёт data/sales.csv — выгрузку заказов за 6 месяцев с сезонностью,
чтобы отчёт было интересно смотреть.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

random.seed(42)

CATEGORIES = {
    "Кофе": ["Эспрессо", "Капучино", "Флэт уайт", "Фильтр V60", "Раф"],
    "Десерты": ["Чизкейк", "Тирамису", "Брауни", "Медовик", "Круассан"],
    "Завтраки": ["Сырники", "Овсянка", "Омлет", "Авокадо-тост", "Гранола"],
    "Напитки": ["Матча", "Какао", "Лимонад", "Чай", "Смузи"],
}

PRICES = {
    "Эспрессо": 180, "Капучино": 260, "Флэт уайт": 280, "Фильтр V60": 300, "Раф": 320,
    "Чизкейк": 380, "Тирамису": 350, "Брауни": 280, "Медовик": 300, "Круассан": 220,
    "Сырники": 390, "Овсянка": 250, "Омлет": 350, "Авокадо-тост": 420, "Гранола": 290,
    "Матча": 300, "Какао": 240, "Лимонад": 220, "Чай": 190, "Смузи": 320,
}

CHANNELS = ["зал", "на вынос", "доставка", "онлайн-заказ"]
CHANNEL_WEIGHTS = [0.45, 0.3, 0.15, 0.1]

START = date(2026, 1, 1)
DAYS = 180
ROWS_TARGET = 1200


def season_factor(day: date) -> float:
    """Лёгкая сезонность: зимой кофе пьют чаще, летом — лимонады."""
    month = day.month
    if month in (12, 1, 2):
        return 1.25
    if month in (6, 7, 8):
        return 0.9
    return 1.0


def main() -> None:
    rows = []
    order_id = 10_000

    for offset in range(DAYS):
        day = START + timedelta(days=offset)
        weekday_factor = 1.35 if day.weekday() >= 5 else 1.0
        orders_today = max(2, int(random.gauss(7, 2) * weekday_factor * season_factor(day)))

        for _ in range(orders_today):
            order_id += 1
            category = random.choices(
                list(CATEGORIES), weights=[0.42, 0.24, 0.2, 0.14]
            )[0]
            product = random.choice(CATEGORIES[category])
            qty = random.choices([1, 2, 3], weights=[0.7, 0.24, 0.06])[0]
            channel = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0]

            rows.append(
                {
                    "date": day.isoformat(),
                    "order_id": order_id,
                    "category": category,
                    "product": product,
                    "qty": qty,
                    "price": PRICES[product],
                    "channel": channel,
                }
            )

    # добираем до целевого объёма
    while len(rows) < ROWS_TARGET:
        day = START + timedelta(days=random.randrange(DAYS))
        order_id += 1
        category = random.choice(list(CATEGORIES))
        product = random.choice(CATEGORIES[category])
        rows.append(
            {
                "date": day.isoformat(),
                "order_id": order_id,
                "category": category,
                "product": product,
                "qty": random.choice([1, 2]),
                "price": PRICES[product],
                "channel": random.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0],
            }
        )

    df = pd.DataFrame(rows).sort_values("date")
    path = Path(__file__).parent / "data" / "sales.csv"
    path.parent.mkdir(exist_ok=True)
    df.to_csv(path, index=False)

    print(f"Создано {len(df)} строк → {path}")
    print(f"Выручка: {(df['qty'] * df['price']).sum():,.0f} ₽".replace(",", " "))


if __name__ == "__main__":
    main()
