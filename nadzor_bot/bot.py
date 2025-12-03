import logging
import os
from typing import Dict, List

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

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


storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message) -> None:
    init_db()
    user_is_admin = is_admin(message.from_user.id)
    greeting = [
        "👋 Привет! Я бот платформы технадзора.",
        "Оставьте заявку или узнайте, как мы работаем.",
    ]
    if user_is_admin:
        greeting.append("Вы авторизованы как администратор.")
    await message.answer("\n".join(greeting), reply_markup=main_keyboard(user_is_admin))


@dp.message_handler(lambda message: message.text == "ℹ️ Как это работает")
async def how_it_works(message: types.Message) -> None:
    text = (
        "Оставляете заявку\n"
        "Мы подбираем мастера и подключаем техинспектора\n"
        "Инспектор проверяет смету/этапы\n"
        "Вы принимаете результат"
    )
    await message.answer(text)


@dp.message_handler(lambda message: message.text == "📝 Оставить заявку", state="*")
async def start_request_flow(message: types.Message, state: FSMContext) -> None:
    await state.finish()
    await message.answer("Как вас зовут?", reply_markup=types.ReplyKeyboardRemove())
    await RequestForm.name.set()


@dp.message_handler(state=RequestForm.name)
async def process_name(message: types.Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await message.answer("Ваш номер телефона?")
    await RequestForm.phone.set()


@dp.message_handler(state=RequestForm.phone)
async def process_phone(message: types.Message, state: FSMContext) -> None:
    await state.update_data(phone=message.text.strip())
    await message.answer("Укажите район Ташкента")
    await RequestForm.district.set()


@dp.message_handler(state=RequestForm.district)
async def process_district(message: types.Message, state: FSMContext) -> None:
    await state.update_data(district=message.text.strip())
    await message.answer("Введите адрес или ориентир (ЖК, улица, дом/кв.)")
    await RequestForm.address.set()


@dp.message_handler(state=RequestForm.address)
async def process_address(message: types.Message, state: FSMContext) -> None:
    await state.update_data(address=message.text.strip())
    await message.answer("Примерная площадь стен (м²)?")
    await RequestForm.area.set()


@dp.message_handler(state=RequestForm.area)
async def process_area(message: types.Message, state: FSMContext) -> None:
    await state.update_data(area=message.text.strip())
    await message.answer("Комментарий (что нужно сделать, сроки и т.п.)")
    await RequestForm.comment.set()


@dp.message_handler(state=RequestForm.comment)
async def process_comment(message: types.Message, state: FSMContext) -> None:
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
    await state.finish()

    for admin_id in ADMINS:
        try:
            await bot.send_message(
                admin_id,
                format_request_card({**data, "id": request_id, "status": "NEW"}),
                reply_markup=status_keyboard(request_id, "NEW"),
            )
        except Exception as exc:  # noqa: BLE001
            logging.exception("Failed to notify admin %s: %s", admin_id, exc)


@dp.message_handler(lambda message: message.text == "🛠 Админ-панель")
async def admin_panel(message: types.Message) -> None:
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


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("details:"))
async def request_details(callback: types.CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, request_id = callback.data.split(":", 1)
    request = get_request(int(request_id))
    if not request:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    await callback.message.edit_text(
        format_request_card(request),
        reply_markup=status_keyboard(request["id"], request["status"]),
    )
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("setstatus:"))
async def set_status(callback: types.CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, request_id_str, status_code = callback.data.split(":", 2)
    request_id = int(request_id_str)

    if not update_request_status(request_id, status_code):
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    updated_request = get_request(request_id)
    if updated_request:
        await callback.message.edit_text(
            format_request_card(updated_request),
            reply_markup=status_keyboard(request_id, status_code),
        )
    await callback.answer("Статус обновлён")

    if updated_request and updated_request["tg_user_id"]:
        try:
            await bot.send_message(
                updated_request["tg_user_id"],
                f"🔔 Статус вашей заявки #{request_id} обновлён:\n"
                f"{STATUS_LABELS.get(status_code, status_code)}",
            )
        except Exception as exc:  # noqa: BLE001
            logging.exception("Failed to notify user %s: %s", updated_request["tg_user_id"], exc)


if __name__ == "__main__":
    init_db()
    executor.start_polling(dp, skip_updates=True)
