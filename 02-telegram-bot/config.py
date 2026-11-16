"""Настройки бота.

Токен и ID администратора берутся из переменных окружения,
чтобы не хранить секреты в коде и в git.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Service:
    code: str
    title: str
    price: int
    duration: int  # минуты


SERVICES: dict[str, Service] = {
    "manicure": Service("manicure", "Маникюр + покрытие", 2500, 90),
    "pedicure": Service("pedicure", "Педикюр", 3200, 120),
    "brows": Service("brows", "Коррекция бровей", 1500, 45),
    "lashes": Service("lashes", "Наращивание ресниц", 3500, 120),
}

WORK_START = 9      # первый слот
WORK_END = 19       # последний слот (включительно)
DAYS_AHEAD = 7      # на сколько дней вперёд показываем даты

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

ADMIN_IDS: list[int] = [
    int(value) for value in os.getenv("ADMIN_IDS", "").split(",") if value.strip().isdigit()
]

STUDIO_NAME = "Аура"
STUDIO_PHONE = "+7 999 123-45-67"
STUDIO_ADDRESS = "ул. Примерная, 12, 2 этаж"
