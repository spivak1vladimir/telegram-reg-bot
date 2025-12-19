import os
import json
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8541958280:AAHHq0zmw0J1bRnxj8XI3wS9PDa3SGkYzLg"
ADMIN_CHAT_ID = 194614510
MAX_SLOTS = 20
DATA_FILE = "registered_users.json"

# Загружаем зарегистрированных пользователей
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        registered_users = json.load(f)
else:
    registered_users = {
        "5km": [],
        "10km": [],
        "waiting": []
    }

# Приветствие и информация об условиях участия
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Рад, что ты присоединился к воскресной пробежке с Spivak Run!\n"
        "Мы стараемся делать каждую пробежку ещё лучше.\n\n"
        "Пожалуйста, ознакомься с условиями участия:\n\n"
        "• Я принимаю личную ответственность за свою жизнь и здоровье.\n"
        "• Я принимаю личную ответственность за сохранность своих вещей.\n"
        "• Я предоставляю согласие на обработку своих персональных данных.\n"
        "• Я даю согласие на фото и видео съёмку с публикацией материалов в соцсетях.\n\n"
        "Если согласен — нажми кнопку ниже."
    )
    keyboard = [[InlineKeyboardButton("Согласен, выбрать дистанцию", callback_data="agree")]]
    await update.effective_message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Меню выбора дистанции
async def choose_distance_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = (
        "Выбегаем из кафе «Onsightotdoor» 21 декабря, в воскресенье.\n"
        "Сбор в 10:30, старт в 11:00.\n"
        "Бежим двумя группами.\n\n"
        "Выбери свою дистанцию:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("5 км — темп 7:30", callback_data="dist_5km"),
            InlineKeyboardButton("Маршрут 5 км", url="https://yandex.ru/maps/-/CLDaANz3")
        ],
        [
            InlineKeyboardButton("10 км — темп 7:00 - 6:30", callback_data="dist_10km"),
            InlineKeyboardButton("Маршрут 10 км", url="https://yandex.ru/maps/-/CLDaeU~S")
        ]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Регистрация на дистанцию
async def choose_distance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_id = str(user.id)

    distances = {
        "dist_5km": "5km",
        "dist_10km": "10km"
    }

    dist_key = distances.get(query.data)
    if dist_key is None:
        await query.edit_message_text("Ошибка: неизвестная дистанция.")
        return

    # Проверяем, есть ли места
    total_slots = len(registered_users["5km"]) + len(registered_users["10km"])

    if total_slots >= MAX_SLOTS:
        # Лист ожидания
        registered_users["waiting"].append({"id": user_id, "distance": dist_key})
        
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(registered_users, f, ensure_ascii=False, indent=2)

        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                f"Новый участник добавлен в лист ожидания!\n"
                f"Имя: {user.first_name}\nUsername: @{user.username}\n"
                f"ID: {user_id}\nВыбранная дистанция: {dist_key}"
            )
        )

        await query.edit_message_text(
    "Основные места заняты.\n"
    "Ты добавлен в *лист ожидания*.\n"
    "Если кто-то отменит участие — ты попадёшь в основной список!",
    parse_mode="Markdown"
)

        return

    # Добавляем в основную группу
    if user_id in registered_users[dist_key]:
        await query.edit_message_text("Ты уже записан на эту дистанцию.")
        return

    registered_users[dist_key].append(user_id)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(registered_users, f, ensure_ascii=False, indent=2)

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=(
            f"Новый участник!\nИмя: {user.first_name}\nUsername: @{user.username}\n"
            f"ID: {user_id}\nДистанция: {dist_key}"
        )
    )

    keyboard = [[InlineKeyboardButton("Отменить запись", callback_data=f"cancel_{dist_key}")]]
    await query.edit_message_text(
        f"Ты записан на дистанцию: {dist_key}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Отмена регистрации
async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    dist_key = query.data.split("_")[1]

    if user_id in registered_users.get(dist_key, []):
        registered_users[dist_key].remove(user_id)

        # При отмене — переводим первого из листа ожидания в основной список
        if registered_users["waiting"]:
            next_user = registered_users["waiting"].pop(0)
            registered_users[next_user["distance"]].append(next_user["id"])

            # Уведомляем админа
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=(
                    f"Участник из листа ожидания перемещён в основной список!\n"
                    f"ID: {next_user['id']}\n"
                    f"Дистанция: {next_user['distance']}"
                )
            )

    else:
        await query.edit_message_text("Ты не был записан на эту дистанцию.")
        return

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(registered_users, f, ensure_ascii=False, indent=2)

    await query.edit_message_text(f"Ты отменил запись на дистанцию: {dist_key}")

# Основной запуск бота
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", info))
    app.add_handler(CallbackQueryHandler(choose_distance_menu, pattern="^agree$"))
    app.add_handler(CallbackQueryHandler(choose_distance, pattern="^dist_"))
    app.add_handler(CallbackQueryHandler(cancel_registration, pattern="^cancel_"))

    logger.info("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()