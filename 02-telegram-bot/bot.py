"""Telegram-бот записи в студию красоты «Аура».

Сценарий:
    /start → меню → услуга → дата → время → имя → телефон → подтверждение
    → запись сохраняется в SQLite, администратор получает уведомление.

Запуск:
    export BOT_TOKEN="123456:ABC..."
    export ADMIN_IDS="123456789"
    pip install -r requirements.txt
    python bot.py
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import (
    ADMIN_IDS,
    DAYS_AHEAD,
    SERVICES,
    STUDIO_ADDRESS,
    STUDIO_NAME,
    STUDIO_PHONE,
    WORK_END,
    WORK_START,
    BOT_TOKEN,
)
from db import BookingStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("aura-bot")

router = Router()
store = BookingStore()


class Booking(StatesGroup):
    service = State()
    visit_date = State()
    visit_time = State()
    name = State()
    phone = State()
    confirm = State()


# --------------------------------------------------------------------------
# Клавиатуры
# --------------------------------------------------------------------------

def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🗓 Записаться", callback_data="book:start")
    builder.button(text="💅 Услуги и цены", callback_data="info:services")
    builder.button(text="📋 Мои записи", callback_data="my:list")
    builder.button(text="📞 Контакты", callback_data="info:contacts")
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()


def services_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, service in SERVICES.items():
        builder.button(
            text=f"{service.title} — {service.price} ₽",
            callback_data=f"svc:{code}",
        )
    builder.button(text="← Назад", callback_data="menu:main")
    builder.adjust(1)
    return builder.as_markup()


def dates_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    today = date.today()

    for offset in range(DAYS_AHEAD):
        day = today + timedelta(days=offset)
        if offset == 0:
            label = "Сегодня"
        elif offset == 1:
            label = "Завтра"
        else:
            label = day.strftime("%d.%m")
        builder.button(text=label, callback_data=f"date:{day.isoformat()}")

    builder.button(text="← Назад", callback_data="menu:main")
    builder.adjust(3)
    return builder.as_markup()


def times_kb(day: str, booked: set[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for hour in range(WORK_START, WORK_END + 1):
        slot = f"{hour:02d}:00"
        if slot in booked:
            continue
        builder.button(text=slot, callback_data=f"time:{day}:{slot}")

    builder.button(text="← Назад", callback_data="book:start")
    builder.adjust(4)
    return builder.as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm:yes")
    builder.button(text="✖️ Отменить", callback_data="confirm:no")
    builder.adjust(2)
    return builder.as_markup()


def phone_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить номер", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


# --------------------------------------------------------------------------
# Вспомогательные функции
# --------------------------------------------------------------------------

def human_date(iso_date: str) -> str:
    day = datetime.fromisoformat(iso_date).date()
    today = date.today()
    if day == today:
        return "сегодня"
    if day == today + timedelta(days=1):
        return "завтра"
    months = (
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря",
    )
    return f"{day.day} {months[day.month - 1]}"


def normalize_phone(raw: str) -> str | None:
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) == 11 and digits[0] in "78":
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    if len(digits) == 10:
        return f"+7 ({digits[0:3]}) {digits[3:6]}-{digits[6:8]}-{digits[8:10]}"
    return None


async def notify_admins(bot: Bot, text: str) -> None:
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text)
        except Exception as exc:  # админ мог не нажать /start
            log.warning("Не удалось отправить уведомление %s: %s", admin_id, exc)


# --------------------------------------------------------------------------
# Старт и меню
# --------------------------------------------------------------------------

@router.message(CommandStart())
@router.message(Command("menu"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        f"Здравствуйте! Это студия <b>{STUDIO_NAME}</b> 💫\n\n"
        "Здесь можно записаться на услугу за минуту — выберите, что нужно.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer("Что вас интересует?", reply_markup=main_menu_kb())


@router.callback_query(F.data == "menu:main")
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Что вас интересует?", reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "info:services")
async def info_services(callback: CallbackQuery) -> None:
    lines = ["<b>Услуги и цены</b>\n"]
    for service in SERVICES.values():
        lines.append(f"• {service.title} — <b>{service.price} ₽</b> ({service.duration} мин)")
    lines.append(f"\nРаботаем ежедневно с {WORK_START}:00 до {WORK_END}:00.")
    await callback.message.edit_text("\n".join(lines), reply_markup=services_kb())
    await callback.answer()


@router.callback_query(F.data == "info:contacts")
async def info_contacts(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        f"<b>{STUDIO_NAME}</b>\n\n"
        f"📍 {STUDIO_ADDRESS}\n"
        f"📞 {STUDIO_PHONE}\n"
        f"🕘 ежедневно с {WORK_START}:00 до {WORK_END}:00\n\n"
        "Нажмите «Записаться», чтобы выбрать удобное время.",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


# --------------------------------------------------------------------------
# Запись: услуга → дата → время
# --------------------------------------------------------------------------

@router.callback_query(F.data == "book:start")
async def book_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(Booking.service)
    await callback.message.edit_text(
        "Выберите услугу:", reply_markup=services_kb()
    )
    await callback.answer()


@router.callback_query(Booking.service, F.data.startswith("svc:"))
async def choose_service(callback: CallbackQuery, state: FSMContext) -> None:
    code = (callback.data or "").split(":", maxsplit=1)[1]
    service = SERVICES.get(code)

    if not service:
        await callback.answer("Услуга не найдена", show_alert=True)
        return

    await state.update_data(service=code)
    await state.set_state(Booking.visit_date)
    await callback.message.edit_text(
        f"<b>{service.title}</b> — {service.price} ₽\n\n"
        "На какой день записать?",
        reply_markup=dates_kb(),
    )
    await callback.answer()


@router.callback_query(Booking.visit_date, F.data.startswith("date:"))
async def choose_date(callback: CallbackQuery, state: FSMContext) -> None:
    day = (callback.data or "").split(":", maxsplit=1)[1]
    await state.update_data(visit_date=day)

    booked = await store.booked_times(day)
    if len(booked) >= (WORK_END - WORK_START + 1):
        await callback.answer("На этот день всё занято, выберите другой", show_alert=True)
        return

    await state.set_state(Booking.visit_time)
    await callback.message.edit_text(
        f"Дата: <b>{human_date(day)}</b>\n\nСвободное время:",
        reply_markup=times_kb(day, booked),
    )
    await callback.answer()


@router.callback_query(Booking.visit_time, F.data.startswith("time:"))
async def choose_time(callback: CallbackQuery, state: FSMContext) -> None:
    _, day, slot = (callback.data or "").split(":")
    await state.update_data(visit_time=slot)
    await state.set_state(Booking.name)

    await callback.message.edit_text(
        f"Отлично: <b>{human_date(day)} в {slot}</b>.\n\n"
        "Как к вам обращаться? Напишите имя."
    )
    await callback.answer()


# --------------------------------------------------------------------------
# Запись: имя и телефон
# --------------------------------------------------------------------------

@router.message(Booking.name)
async def enter_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()

    if len(name) < 2 or len(name) > 40:
        await message.answer("Напишите имя (от 2 до 40 символов).")
        return

    await state.update_data(name=name)
    await state.set_state(Booking.phone)
    await message.answer(
        "Оставьте номер телефона — по нему свяжемся, если что-то изменится.\n"
        "Можно нажать кнопку ниже или написать вручную.",
        reply_markup=phone_kb(),
    )


@router.message(Booking.phone, F.contact)
async def phone_from_contact(message: Message, state: FSMContext) -> None:
    await save_phone(message, state, message.contact.phone_number)


@router.message(Booking.phone)
async def phone_from_text(message: Message, state: FSMContext) -> None:
    await save_phone(message, state, message.text or "")


async def save_phone(message: Message, state: FSMContext, raw: str) -> None:
    phone = normalize_phone(raw)

    if not phone:
        await message.answer(
            "Не получилось распознать номер. Напишите в формате +7 999 123-45-67 "
            "или нажмите кнопку «Отправить номер»."
        )
        return

    await state.update_data(phone=phone)
    await state.set_state(Booking.confirm)

    data = await state.get_data()
    service = SERVICES[data["service"]]

    await message.answer(
        "<b>Проверьте запись:</b>\n\n"
        f"Услуга: {service.title}\n"
        f"Дата: {human_date(data['visit_date'])}\n"
        f"Время: {data['visit_time']}\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {phone}\n"
        f"Стоимость: {service.price} ₽",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer("Всё верно?", reply_markup=confirm_kb())


# --------------------------------------------------------------------------
# Подтверждение
# --------------------------------------------------------------------------

@router.callback_query(Booking.confirm, F.data == "confirm:yes")
async def confirm_booking(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    service = SERVICES[data["service"]]

    booking_id = await store.add(
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        name=data["name"],
        phone=data["phone"],
        service=service.title,
        price=service.price,
        visit_date=data["visit_date"],
        visit_time=data["visit_time"],
    )

    await state.clear()

    await callback.message.edit_text(
        "✅ <b>Готово, вы записаны!</b>\n\n"
        f"Услуга: {service.title}\n"
        f"Дата: {human_date(data['visit_date'])}\n"
        f"Время: {data['visit_time']}\n"
        f"Стоимость: {service.price} ₽\n\n"
        f"Адрес: {STUDIO_ADDRESS}\n"
        "Если планы изменятся — напишите нам или отмените запись в меню.",
    )
    await callback.answer("Запись создана")

    await notify_admins(
        callback.bot,
        "🆕 <b>Новая запись</b>\n\n"
        f"№{booking_id}\n"
        f"{service.title} — {human_date(data['visit_date'])} в {data['visit_time']}\n"
        f"Клиент: {data['name']}, {data['phone']}\n"
        f"@{callback.from_user.username or '—'} (id {callback.from_user.id})",
    )


@router.callback_query(Booking.confirm, F.data == "confirm:no")
async def cancel_booking(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "Запись отменена. Если передумаете — вы всегда можете выбрать другое время.",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


# --------------------------------------------------------------------------
# Мои записи
# --------------------------------------------------------------------------

@router.callback_query(F.data == "my:list")
async def my_bookings(callback: CallbackQuery) -> None:
    bookings = await store.by_user(callback.from_user.id)

    if not bookings:
        await callback.message.edit_text(
            "У вас пока нет активных записей.\n\nЗапишитесь — это займёт минуту.",
            reply_markup=main_menu_kb(),
        )
        await callback.answer()
        return

    builder = InlineKeyboardBuilder()
    lines = ["<b>Ваши записи:</b>\n"]

    for item in bookings:
        lines.append(
            f"• {item['service']} — {human_date(item['visit_date'])} в {item['visit_time']}"
        )
        builder.button(
            text=f"Отменить {item['visit_date'][5:]} {item['visit_time']}",
            callback_data=f"cancel:{item['id']}",
        )

    builder.button(text="← В меню", callback_data="menu:main")
    builder.adjust(1)

    await callback.message.edit_text("\n".join(lines), reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("cancel:"))
async def cancel_existing(callback: CallbackQuery) -> None:
    booking_id = int((callback.data or "").split(":")[1])
    ok = await store.cancel(booking_id, callback.from_user.id)

    if ok:
        await callback.answer("Запись отменена", show_alert=True)
        await notify_admins(
            callback.bot,
            f"❌ Клиент отменил запись №{booking_id} "
            f"(@{callback.from_user.username or callback.from_user.id})",
        )
    else:
        await callback.answer("Не удалось отменить запись", show_alert=True)

    await my_bookings(callback)


# --------------------------------------------------------------------------
# Админ: записи на сегодня
# --------------------------------------------------------------------------

@router.message(Command("admin"))
async def admin_today(message: Message) -> None:
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Команда доступна только администратору.")
        return

    today = date.today().isoformat()
    bookings = await store.by_date(today)

    if not bookings:
        await message.answer("На сегодня записей нет.")
        return

    lines = [f"<b>Записи на {human_date(today)}:</b>\n"]
    total = 0
    for item in bookings:
        lines.append(
            f"{item['visit_time']} — {item['service']}, {item['name']}, {item['phone']}"
        )
        total += item["price"]

    lines.append(f"\nВсего записей: {len(bookings)} на {total} ₽")
    await message.answer("\n".join(lines))


@router.message()
async def fallback(message: Message) -> None:
    await message.answer(
        "Не понял сообщение 🙂\nВыберите действие в меню или нажмите /start.",
        reply_markup=main_menu_kb(),
    )


# --------------------------------------------------------------------------
# Точка входа
# --------------------------------------------------------------------------

async def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit(
            "Не задан BOT_TOKEN. Выполните: export BOT_TOKEN='123456:ABC...'"
        )

    await store.init()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    log.info("Бот запущен")
    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Бот остановлен")
