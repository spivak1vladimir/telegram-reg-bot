# --- coding: utf-8 ---

import os
import json
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("8541958280:AAGFCQLEdWvAeLeW55sbHdxvBecGeHNWyyY")
ADMIN_CHAT_ID = 194614510
MAX_SLOTS = 20
DATA_FILE = "registered_users.json"

def load_users():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"7km": [], "10km": [], "15km": []}

def save_users(users):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

registered_users = load_users()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"/start — user_id={update.effective_user.id}")
    text = (
        "Ты присоединился к воскресной пробежке!\n"
        "Сбор в 10:30, старт в 11:00.\n\n"
        "Выбери свою дистанцию:"
    )

    keyboard = [
        [InlineKeyboardButton("7 км (7:30)", callback_data="dist_7km")],
        [InlineKeyboardButton("10 км (7:00)", callback_data="dist_10km")],
        [InlineKeyboardButton("10+5 км (5:45–6:00)", callback_data="dist_15km")],
    ]

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def choose_distance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_id = str(user.id)

    distances = {
        "dist_7km": "7km",
        "dist_10km": "10km",
        "dist_15km": "15km"
    }

    dist_key = distances.get(query.data)

    if dist_key is None:
        await query.edit_message_text("Ошибка: неизвестная дистанция.")
        return

    if len(registered_users[dist_key]) >= MAX_SLOTS:
        await query.edit_message_text("Все места на эту дистанцию заняты.")
        return

    if user_id in registered_users[dist_key]:
        await query.edit_message_text("Ты уже записан на эту дистанцию.")
        return

    registered_users[dist_key].append(user_id)
    save_users(registered_users)

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=(
            "Новый участник!\n"
            f"Имя: {user.first_name}\n"
            f"Username: @{user.username}\n"
            f"ID: {user_id}\n"
            f"Дистанция: {dist_key}"
        )
    )

    await query.edit_message_text(f"Ты записан на дистанцию: {dist_key}")

def main():
    if TOKEN is None:
        raise ValueError("❌ Ошибка: переменная окружения BOT_TOKEN не установлена!")

    logger.info("Bot starting…")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(choose_distance, pattern="^dist_"))

    logger.info("Bot running…")
    app.run_polling()

if __name__ == "__main__":
    main()
