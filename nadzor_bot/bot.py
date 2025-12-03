import asyncio
import logging
import os
from typing import Dict, List

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from nadzor_bot.db import add_request, get_last_requests, get_request, init_db, update_request_status

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment variables")

ADMINS = {123456789, 987654321}

STATUS_LABELS: Dict[str, str] = {
    "NEW": "🟡 Новая",
    "SEARCHING": "🟠 Подбор мастера",
    "ASSIGNED": "🔵 Мастер назначен",
    "IN_WORK": "🟣 В работе",
    "INSPECT": "🟤 Проверка инспектором",
    "DONE": "🟢 Завершена",
}

STATUS_ORDER: List[str] = [
    "NEW",
    "SEARCHING",
    "ASSIGNED",
    "IN_WORK",
    "INSPECT",
    "DONE",
]


class RequestForm(StatesGroup):
    name = State()
    phone = State()
    district = State()
    address = State()
    area = State()
    comment = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMINS


def main_keyboard(is_admin_user: bool = False) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("📝 Оставить заявку", "ℹ️ Как это работает")
    if is_admin_user:
        keyboard.add("🛠 Админ-панель")
    return keyboard


def status_keyboard(request_id: int, current_status: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)
    for status in STATUS_ORDER:
        if status == current_status:
            continue
        keyboard.add(
            InlineKeyboardButton(
                text=STATUS_LABELS.get(status, status),
                callback_data=f"setstatus:{request_id}:{status}",
            )
        )
    return keyboard


def format_request_card(request_data) -> str:
    return (
        f"🧾 Заявка #{request_data['id']}\n\n"
        f"👤 Имя: {request_data['name']}\n"
        f"📞 Телефон: {request_data['phone']}\n"
        f"📍 Район: {request_data['district']}\n"
        f"🗺 Адрес: {request_data['address']}\n"
        f"📐 Площадь: {request_data['area']}\n"
        f"💬 Комментарий: {request_data['comment']}\n\n"
        f"🔖 Статус: {STATUS_LABELS.get(request_data['status'], request_data['status'])}"
    )


bot = Bot(token=BOT_TOKEN)
router = Router()


@router.message(Command("start"), StateFilter("*"))
async def cmd_start(message: Message) -> None:
    init_db()
    user_is_admin = is_admin(message.from_user.id)
    greeting = [
        "👋 Привет! Я бот платформы технадзора.",
        "Оставьте заявку или узнайте, как мы работаем.",
    ]
    if user_is_admin:
        greeting.append("Вы авторизованы как администратор.")
    await message.answer("\n".join(greeting), reply_markup=main_keyboard(user_is_admin))


@router.message(F.text == "ℹ️ Как это работает", StateFilter("*"))
async def how_it_works(message: Message) -> None:
    text = (
        "Оставляете заявку\n"
        "Мы подбираем мастера и подключаем техинспектора\n"
        "Инспектор проверяет смету/этапы\n"
        "Вы принимаете результат"
    )
    await message.answer(text)


@router.message(F.text == "📝 Оставить заявку", StateFilter("*"))
async def start_request_flow(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(RequestForm.name)
    await message.answer("Как вас зовут?", reply_markup=ReplyKeyboardRemove())


@router.message(RequestForm.name)
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await state.set_state(RequestForm.phone)
    await message.answer("Ваш номер телефона?")


@router.message(RequestForm.phone)
async def process_phone(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=message.text.strip())
    await state.set_state(RequestForm.district)
    await message.answer("Укажите район Ташкента")


@router.message(RequestForm.district)
async def process_district(message: Message, state: FSMContext) -> None:
    await state.update_data(district=message.text.strip())
    await state.set_state(RequestForm.address)
    await message.answer("Введите адрес или ориентир (ЖК, улица, дом/кв.)")


@router.message(RequestForm.address)
async def process_address(message: Message, state: FSMContext) -> None:
    await state.update_data(address=message.text.strip())
    await state.set_state(RequestForm.area)
    await message.answer("Примерная площадь стен (м²)?")


@router.message(RequestForm.area)
async def process_area(message: Message, state: FSMContext) -> None:
    await state.update_data(area=message.text.strip())
    await state.set_state(RequestForm.comment)
    await message.answer("Комментарий (что нужно сделать, сроки и т.п.)")


@router.message(RequestForm.comment)
async def process_comment(message: Message, state: FSMContext) -> None:
    await state.update_data(comment=message.text.strip())
    data = await state.get_data()

    request_id = add_request(
        tg_user_id=message.from_user.id,
        tg_username=message.from_user.username,
        name=data["name"],
        phone=data["phone"],
        district=data["district"],
        address=data["address"],
        area=data["area"],
        comment=data["comment"],
    )

    await message.answer(
        f"Заявка #{request_id} принята ✅\n"
        "Мы подберём мастера, подключим тех-инспектора и свяжемся.",
        reply_markup=main_keyboard(is_admin(message.from_user.id)),
    )
    await state.clear()

    for admin_id in ADMINS:
        try:
            await bot.send_message(
                admin_id,
                format_request_card({**data, "id": request_id, "status": "NEW"}),
                reply_markup=status_keyboard(request_id, "NEW"),
            )
        except Exception as exc:  # noqa: BLE001
            logging.exception("Failed to notify admin %s: %s", admin_id, exc)


@router.message(F.text == "🛠 Админ-панель", StateFilter("*"))
async def admin_panel(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа")
        return

    requests = get_last_requests()
    if not requests:
        await message.answer("Заявок пока нет")
        return

    lines = []
    keyboard = InlineKeyboardMarkup(row_width=1)
    for request in requests:
        line = f"#{request['id']} • {request['name']} • {STATUS_LABELS.get(request['status'], request['status'])}"
        lines.append(line)
        keyboard.add(
            InlineKeyboardButton(
                text=line,
                callback_data=f"details:{request['id']}",
            )
        )

    await message.answer("\n".join(lines), reply_markup=keyboard)


@router.callback_query(F.data.startswith("details:"))
async def request_details(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, request_id = callback.data.split(":", 1)  # type: ignore[union-attr]
    request = get_request(int(request_id))
    if not request:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    await callback.message.edit_text(  # type: ignore[union-attr]
        format_request_card(request),
        reply_markup=status_keyboard(request["id"], request["status"]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("setstatus:"))
async def set_status(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, request_id_str, status_code = callback.data.split(":", 2)  # type: ignore[union-attr]
    request_id = int(request_id_str)

    if not update_request_status(request_id, status_code):
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    updated_request = get_request(request_id)
    if updated_request:
        await callback.message.edit_text(  # type: ignore[union-attr]
            format_request_card(updated_request),
            reply_markup=status_keyboard(request_id, status_code),
        )
    await callback.answer("Статус обновлён")

    if updated_request and updated_request["tg_user_id"]:
        try:
            await bot.send_message(
                updated_request["tg_user_id"],
                "\n".join(
                    [
                        f"🔔 Статус вашей заявки #{request_id} обновлён:",
                        STATUS_LABELS.get(status_code, status_code),
                    ]
                ),
            )
        except Exception as exc:  # noqa: BLE001
            logging.exception("Failed to notify user %s: %s", updated_request["tg_user_id"], exc)


async def main() -> None:
    init_db()
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
