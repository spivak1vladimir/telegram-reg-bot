import os
import json
import logging
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8541958280:AAHHq0zmw0J1bRnxj8XI3wS9PDa3SGkYzLg"
ADMIN_CHAT_ID = 194614510
MAX_SLOTS = 20
DATA_FILE = "registered_users.json"

RUN_DATETIME = datetime(2025, 12, 28, 11, 0)

RUN_DATE_TEXT = "28.12.25"
RUN_TITLE_TEXT = "Бежим под Новый год"

START_POINT = "Кафе «Человек и пароход»"
START_MAP_LINK_6KM = "https://yandex.ru/maps/-/CLHfEEpb"
START_MAP_LINK_12KM = "https://yandex.ru/maps/-/CLHfYV2G"

# ---------- ЗАГРУЗКА ДАННЫХ ----------
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        registered_users = json.load(f)
else:
    registered_users = {
        "6km": [],
        "12km": [],
        "waiting": []
    }

# ---------- ВСПОМОГАТЕЛЬНЫЕ ----------
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(registered_users, f, ensure_ascii=False, indent=2)

def format_users(dist):
    if not registered_users[dist]:
        return "— пока нет участников"
    return "\n".join(
        f"{i + 1}. {u['name']}" for i, u in enumerate(registered_users[dist])
    )

def all_participants():
    return registered_users["6km"] + registered_users["12km"]

# ---------- /START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"{RUN_DATE_TEXT}\n"
        f"{RUN_TITLE_TEXT}\n\n"
        "Рад, что ты присоединился к воскресной пробежке с Spivak Run.\n\n"
        "Условия участия:\n"
        "Я принимаю личную ответственность за свою жизнь и здоровье.\n"
        "Я принимаю ответственность за сохранность своих вещей.\n"
        "Я даю согласие на обработку персональных данных.\n"
        "Я даю согласие на фото и видео съемку с публикацией материалов.\n\n"
        "Если согласен — нажми кнопку ниже."
    )
    keyboard = [
        [InlineKeyboardButton("Согласен, выбрать дистанцию", callback_data="agree")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ---------- МЕНЮ ДИСТАНЦИЙ ----------
async def choose_distance_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        f"{RUN_DATE_TEXT}\n"
        f"{RUN_TITLE_TEXT}\n\n"
        f"Старт: {START_POINT}\n"
        "Сбор: 10:30\n"
        "Старт: 11:00\n\n"
        "Дистанции:\n"
        "6 км — темп 7:00\n"
        "12 км — 6 км + дополнительно ещё 6 км в темпе 6:30\n\n"
        "Выбери дистанцию:"
    )

    keyboard = [
        [
            InlineKeyboardButton("6 км — темп 7:00", callback_data="dist_6km"),
            InlineKeyboardButton("Маршрут 6 км", url=START_MAP_LINK_6KM)
        ],
        [
            InlineKeyboardButton("12 км — 6 + 6 км (6:30)", callback_data="dist_12km"),
            InlineKeyboardButton("Маршрут 12 км", url=START_MAP_LINK_12KM)
        ]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ---------- РЕГИСТРАЦИЯ ----------
async def choose_distance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = str(user.id)
    dist_key = "6km" if query.data == "dist_6km" else "12km"

    user_data = {
        "id": user_id,
        "name": user.first_name,
        "username": user.username or ""
    }

    if any(u["id"] == user_id for u in all_participants()):
        await query.edit_message_text("Ты уже зарегистрирован.")
        return

    if len(all_participants()) >= MAX_SLOTS:
        registered_users["waiting"].append({**user_data, "distance": dist_key})
        save_data()

        await context.bot.send_message(
            ADMIN_CHAT_ID,
            f"Добавлен в лист ожидания\n"
            f"Имя: {user.first_name}\n"
            f"Username: @{user.username}\n"
            f"Дистанция: {dist_key}"
        )

        await query.edit_message_text("Основные места заняты. Ты в листе ожидания.")
        return

    registered_users[dist_key].append(user_data)
    save_data()

    await context.bot.send_message(
        ADMIN_CHAT_ID,
        f"Новый участник\n"
        f"Имя: {user.first_name}\n"
        f"Username: @{user.username}\n"
        f"ID: {user_id}\n"
        f"Дистанция: {dist_key}"
    )

    keyboard = [
        [InlineKeyboardButton("Отменить запись", callback_data=f"cancel_{dist_key}")]
    ]

    await query.edit_message_text(
        f"Ты зарегистрирован на {dist_key}\n\n"
        f"Участники:\n{format_users(dist_key)}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------- ОТМЕНА ----------
async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = str(user.id)
    dist_key = query.data.split("_")[1]

    for u in registered_users[dist_key]:
        if u["id"] == user_id:
            registered_users[dist_key].remove(u)

            await context.bot.send_message(
                ADMIN_CHAT_ID,
                f"Участник отменил регистрацию\n"
                f"Имя: {u['name']}\n"
                f"Username: @{u['username']}\n"
                f"ID: {u['id']}\n"
                f"Дистанция: {dist_key}"
            )
            break

    save_data()
    await query.edit_message_text("Регистрация отменена.")

# ---------- /INFO ----------
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"{RUN_DATE_TEXT}\n"
        f"{RUN_TITLE_TEXT}\n\n"
        f"Старт: {START_POINT}\n"
        "Сбор: 10:30\n"
        "Старт: 11:00\n\n"
        f"Маршрут 6 км: {START_MAP_LINK_6KM}\n"
        f"Маршрут 12 км: {START_MAP_LINK_12KM}\n\n"
        f"6 км ({len(registered_users['6km'])} чел):\n"
        f"{format_users('6km')}\n\n"
        f"12 км ({len(registered_users['12km'])} чел):\n"
        f"{format_users('12km')}"
    )
    await update.message.reply_text(text)

# ---------- НАПОМИНАНИЕ ЗА 24 ЧАСА ----------
async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"{RUN_DATE_TEXT}\n"
        f"{RUN_TITLE_TEXT}\n\n"
        f"Завтра пробежка\n\n"
        f"Старт: {START_POINT}\n"
        "Сбор: 10:30\n"
        "Старт: 11:00\n\n"
        f"Маршрут 6 км: {START_MAP_LINK_6KM}\n"
        f"Маршрут 12 км: {START_MAP_LINK_12KM}"
    )

    for u in all_participants():
        try:
            await context.bot.send_message(chat_id=int(u["id"]), text=text)
        except Exception:
            pass

    await context.bot.send_message(
        ADMIN_CHAT_ID,
        f"Напоминание отправлено\n"
        f"Всего участников: {len(all_participants())}"
    )

# ---------- ЗАПУСК ----------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CallbackQueryHandler(choose_distance_menu, pattern="^agree$"))
    app.add_handler(CallbackQueryHandler(choose_distance, pattern="^dist_"))
    app.add_handler(CallbackQueryHandler(cancel_registration, pattern="^cancel_"))

    reminder_time = RUN_DATETIME - timedelta(hours=24)
    app.job_queue.run_once(send_reminder, when=reminder_time)

    logger.info("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
