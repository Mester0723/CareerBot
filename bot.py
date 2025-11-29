import telebot
from config import TOKEN
from logic import *
import sqlite3

bot = telebot.TeleBot(TOKEN)
user_data = {}

# /start
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет!\n"
        "💠 Я CareerBot — ваш советчик по карьере!\n\n"
        "Выберите действие:",
        reply_markup=build_main_menu()
    )

# Обработка кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username or "unknown"

    if call.data == "recommend":
        interests = user_data.get(user_id, ["Аналитика"])
        recommendations = generate_recommendation(interests)
        save_recommendation(user_id, ", ".join(recommendations))
        formatted_list = "\n".join([f"- {item}" for item in recommendations])
        bot.send_message(chat_id, "🎯 Рекомендованные направления:\n" + formatted_list)

    elif call.data == "interests":
        bot.send_message(chat_id, "📄 Выберите ваши интересы:", reply_markup=build_interests_menu())

    elif call.data.startswith("interest_"):
        interest = call.data.replace("interest_", "")
        msg = handle_user_interest(user_id, username, interest)
        user_data[user_id] = [interest]
        bot.send_message(chat_id, msg)

    elif call.data == "back":
        bot.send_message(chat_id, "🏠 Главное меню:", reply_markup=build_main_menu())

# Обработка текстовых сообщений
@bot.message_handler(content_types=["text"])
def text_handler(message):
    bot.send_message(
        message.chat.id,
        "⁉️ Пожалуйста, используйте кнопки меню для выбора действий.",
        reply_markup=build_main_menu()
    )

print("CareerBot запущен!")
bot.infinity_polling()