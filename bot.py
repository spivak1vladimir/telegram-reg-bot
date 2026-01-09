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

TOKEN = "8541958280:AAHH0z0JFb1R4-zv25VDVeZvytxxYVn42HY"
ADMIN_CHAT_ID = 194614510
MAX_SLOTS = 20
DATA_FILE = "registered_users.json"

RUN_DATETIME = datetime(2026, 1, 11, 11, 30)

RUN_DATE_TEXT = "11.01.26"
RUN_TITLE_TEXT = "YCP"

START_POINT = "Кафе «YCP» Мясницкая улица, 13с21"
START_MAP_LINK_6KM = "https://yandex.ru/maps/-/CLXtaXnr"
START_MAP_LINK_12KM = "https://yandex.ru/maps/-/CLXtFDpf"

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        registered_users = json.load(f)
else:
    registered_users = {
        "6km": [],
        "12km": [],
        "waiting": []
    }

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

async def choose_distance_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        f"{RUN_DATE_TEXT}\n"
        f"{RUN_TITLE_TEXT}\n\n"
        f"Старт: {START_POINT}\n"
        "Сбор: 11:00\n"
        "Старт: 11:30\n\n"
        "Дистанции:\n"
        "6 км — темп 7:30\n"
        "12 км — 6 км + дополнительно ещё 6 км в темпе 7:00\n\n"
        "Выбери дистанцию:"
    )

    keyboard = [
        [
            InlineKeyboardButton("6 км — темп 7:30", callback_data="dist_6km"),
            InlineKeyboardButton("Маршрут 6 км", url=START_MAP_LINK_6KM)
        ],
        [
            InlineKeyboardButton("12 км — 6 + 6 км (7:00)", callback_data="dist_12km"),
            InlineKeyboardButton("Маршрут 12 км", url=START_MAP_LINK_12KM)
        ]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

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
        [
            InlineKeyboardButton("Информация", callback_data="my_info"),
            InlineKeyboardButton("Отменить регистрацию", callback_data=f"cancel_{dist_key}")
        ]
    ]

    await query.edit_message_text(
        f"Ты зарегистрирован на {dist_key}\n\n"
        f"Участники:\n{format_users(dist_key)}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

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

async def my_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    dist = None

    for d in ("6km", "12km"):
        if any(u["id"] == user_id for u in registered_users[d]):
            dist = d
            break

    if not dist:
        await query.edit_message_text("Ты не зарегистрирован.")
        return

    text = (
        f"{RUN_DATE_TEXT}\n"
        f"{RUN_TITLE_TEXT}\n\n"
        f"Твоя дистанция: {dist}\n\n"
        f"Старт: {START_POINT}\n"
        "Сбор: 10:30\n"
        "Старт: 11:00\n\n"
        f"Маршрут 6 км: {START_MAP_LINK_6KM}\n"
        f"Маршрут 12 км: {START_MAP_LINK_12KM}"
    )

    keyboard = [
        [InlineKeyboardButton("Отменить регистрацию", callback_data=f"cancel_{dist}")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

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

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"{RUN_DATE_TEXT}\n"
        f"{RUN_TITLE_TEXT}\n\n"
        "Завтра пробежка\n\n"
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

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return

    keyboard = []

    for dist in ("6km", "12km"):
        for u in registered_users[dist]:
            keyboard.append([
                InlineKeyboardButton(
                    f"Удалить {u['name']} ({dist})",
                    callback_data=f"admin_del_{u['id']}_{dist}"
                )
            ])

    if not keyboard:
        await update.message.reply_text("Нет зарегистрированных участников.")
        return

    await update.message.reply_text(
        "Админка",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.message.chat.id != ADMIN_CHAT_ID:
        return

    _, _, user_id, dist = query.data.split("_")

    for u in registered_users[dist]:
        if u["id"] == user_id:
            registered_users[dist].remove(u)
            save_data()

            await query.edit_message_text(
                f"Удалён участник:\n{u['name']} ({dist})"
            )

            try:
                await context.bot.send_message(
                    chat_id=int(user_id),
                    text="Твоя регистрация была отменена администратором."
                )
            except Exception:
                pass
            return

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("admin", admin_panel))

    app.add_handler(CallbackQueryHandler(choose_distance_menu, pattern="^agree$"))
    app.add_handler(CallbackQueryHandler(choose_distance, pattern="^dist_"))
    app.add_handler(CallbackQueryHandler(cancel_registration, pattern="^cancel_"))
    app.add_handler(CallbackQueryHandler(my_info, pattern="^my_info$"))
    app.add_handler(CallbackQueryHandler(admin_delete, pattern="^admin_del_"))

    reminder_time = RUN_DATETIME - timedelta(hours=24)
    app.job_queue.run_once(send_reminder, when=reminder_time)

    logger.info("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()


