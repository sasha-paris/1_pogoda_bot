import requests
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# Константы состояний
CHOOSING_NAME, MAIN_MENU, SETTING_CITY = range(3)

# Константы
DEFAULT_CITY = "Киев"
API_KEY = "39f2b14295d8c8fcec18f7cd1abcb094"  # Ваш ключ OpenWeatherMap
user_data = {}

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для получения погоды
def get_weather_and_recommendation(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=ru"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        temperature = data['main']['temp']
        weather_description = data['weather'][0]['description']
        weather = f"Погода в {city}: {weather_description}, температура: {temperature}°C."

        if temperature > 20:
            recommendation = "Рекомендуется надеть лёгкую куртку или футболку и шорты."
        elif 10 <= temperature <= 20:
            recommendation = "Лучше надеть куртку или кофту."
        else:
            recommendation = "Холодно, стоит надеть тёплую одежду."

        return weather, recommendation
    else:
        return "Ошибка получения данных о погоде.", "Не удается получить рекомендации."

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data[chat_id] = {"city": DEFAULT_CITY}

    welcome_message = (
        f"Привет! Я бот для прогноза погоды и рекомендаций по одежде.\n"
        f"Как вас зовут?"
    )
    await update.message.reply_text(welcome_message)
    return CHOOSING_NAME

# Сохранение имени пользователя
async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    name = update.message.text
    user_data[chat_id]["name"] = name

    await update.message.reply_text(
        f"Привет, {name}! Выберите команду ниже.",
        reply_markup=main_menu_markup()
    )
    return MAIN_MENU

# Главное меню
def main_menu_markup():
    buttons = [["pogoda", "city", "test"]]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# Кнопка pogoda
async def send_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    city = user_data[chat_id].get("city", DEFAULT_CITY)
    weather, recommendation = get_weather_and_recommendation(city)

    await update.message.reply_text(
        f"Погода в городе {city}:\n{weather}\nРекомендации: {recommendation}"
    )

# Кнопка city (смена города)
async def change_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"Ваш текущий город: {user_data[chat_id].get('city', DEFAULT_CITY)}.\nВведите новый город:"
    )
    return SETTING_CITY

# Сохранение города
async def save_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    city = update.message.text.strip()

    # Проверяем город через API, чтобы избежать ошибок
    weather, _ = get_weather_and_recommendation(city)
    if "Ошибка" in weather:
        await update.message.reply_text(
            f"Не удалось найти город '{city}'. Пожалуйста, попробуйте снова."
        )
        return SETTING_CITY

    user_data[chat_id]["city"] = city
    await update.message.reply_text(
        f"Город успешно изменён на {city}.", reply_markup=main_menu_markup()
    )
    return MAIN_MENU

# Кнопка test (имитация работы)
async def test_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    city = user_data[chat_id].get("city", DEFAULT_CITY)
    name = user_data[chat_id].get("name", "Пользователь")

    messages = []
    for hour in range(7, 19, 2):  # Сообщения каждые 2 часа с 7 до 19
        weather, recommendation = get_weather_and_recommendation(city)
        messages.append(
            f"Сообщение {hour}:00 для {name}:\nПогода: {weather}\nРекомендации: {recommendation}"
        )

    await update.message.reply_text("\n\n".join(messages))

# Функция для необработанных команд
async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Команда не распознана. Выберите действие из меню.")

# Главная функция
def main():
    application = Application.builder().token("7702975397:AAFL3j5iwmBbhncn54zIAOPFz3-5PzSRVbk").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_name)],
            MAIN_MENU: [
                MessageHandler(filters.Regex("^pogoda$"), send_weather),
                MessageHandler(filters.Regex("^city$"), change_city),
                MessageHandler(filters.Regex("^test$"), test_day),
            ],
            SETTING_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_city)],
        },
        fallbacks=[MessageHandler(filters.TEXT | filters.COMMAND, fallback)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
