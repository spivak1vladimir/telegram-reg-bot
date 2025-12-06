import os
import json
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = 194614510
MAX_SLOTS = 20
DATA_FILE = "registered_users.json"

# Загружаем зарегистрированных пользователей
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        registered_users = json.load(f)
else:
    registered_users = {"7km": [], "10km": [], "15km": []}

# Приветствие и информация об условиях участия
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Рад, что ты присоединился к воскресной пробежке с Spivak Run!\n"
        "Мы стараемся делать каждую пробежку ещё лучше.\n\n"
        "Пожалуйста, ознакомься с условиями участия:\n\n"
        "• Я принимаю личную ответственность за свою жизнь и здоровье.\n"
        "• Я принимаю личную ответственность за сохранность своих вещей.\n"
        "• Я предоставляю согласие на обработку своих персональных данных.\n"
        "• Я даю согласие на фото и видео съёмку с публикацией материалов в социальных сетях.\n\n"
        "Если согласен — нажми кнопку ниже."
    )
    keyboard = [[InlineKeyboardButton("Согласен, выбрать дистанцию", callback_data="agree")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Выбор дистанции с кнопками маршрута
async def choose_distance_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "Эта воскресная пробежка 7 декабря.\n"
        "Сбор в 10:30, старт в 11:00, место — Bloom n Brew.\n\n"
        "Выбери свою дистанцию:"
    )
    keyboard = [
        [
            InlineKeyboardButton("7 км в темпе 7:30", callback_data="dist_7km"),
            InlineKeyboardButton("Маршрут 7 км", url="https://yandex.ru/maps?rtext=55.774650,37.673290~55.769040,37.692695~55.765216,37.700961~55.759326,37.694306~55.761901,37.687578~55.768948,37.692242~55.768203,37.688733~55.768738,37.684934~55.768301,37.675090~55.774814,37.672930&rtt=pd")
        ],
        [
            InlineKeyboardButton("10 км в темпе 7:00", callback_data="dist_10km"),
            InlineKeyboardButton("Маршрут 10 км", url="https://yandex.ru/maps?rtext=55.774650,37.673290~55.769040,37.692695~55.763970,37.690340~55.760132,37.685943~55.757018,37.672056~55.752569,37.672954~55.758319,37.664533~55.765028,37.659297~55.773411,37.664918~55.775838,37.669894~55.774962,37.673004&rtt=pd")
        ],
        [
            InlineKeyboardButton("10 км + 5 км в темпе 5:45-6:00", callback_data="dist_15km"),
            InlineKeyboardButton("Маршрут 10+5 км", url="https://yandex.ru/maps?rtext=55.774650,37.673290~55.769040,37.692695~55.763970,37.690340~55.760132,37.685943~55.757018,37.672056~55.752569,37.672954~55.758319,37.664533~55.765028,37.659297~55.773589,37.669766~55.775838,37.669894~55.774962,37.673004~55.779306,37.666190~55.769016,37.649918~55.769698,37.662970~55.773214,37.664370~55.777217,37.674062~55.774618,37.672971&rtt=pd")
        ]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Выбор конкретной дистанции
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
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(registered_users, f, ensure_ascii=False, indent=2)

    # Сообщение админу
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=(
            f"Новый участник!\nИмя: {user.first_name}\nUsername: @{user.username}\n"
            f"ID: {user_id}\nДистанция: {dist_key}"
        )
    )

    # Кнопка для отмены записи
    keyboard = [[InlineKeyboardButton("Отменить запись", callback_data=f"cancel_{dist_key}")]]
    await query.edit_message_text(f"Ты записан на дистанцию: {dist_key}", reply_markup=InlineKeyboardMarkup(keyboard))

# Отмена записи
async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    dist_key = query.data.split("_")[1]

    if user_id in registered_users[dist_key]:
        registered_users[dist_key].remove(user_id)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(registered_users, f, ensure_ascii=False, indent=2)
        await query.edit_message_text(f"Ты отменил запись на дистанцию: {dist_key}")
    else:
        await query.edit_message_text("Ты не был записан на эту дистанцию.")

# Основная функция
def main():
    if TOKEN is None:
        raise ValueError("Установи переменную окружения BOT_TOKEN")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", info))
    app.add_handler(CallbackQueryHandler(choose_distance_menu, pattern="agree"))
    app.add_handler(CallbackQueryHandler(choose_distance, pattern="^dist_"))
    app.add_handler(CallbackQueryHandler(cancel_registration, pattern="^cancel_"))

    logger.info("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
