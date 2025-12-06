import time
import telebot
from config import TOKEN
from logic import (
    build_main_menu,
    build_interests_menu,
    build_interests_menu_for_quiz,
    generate_recommendation,
    save_recommendation,
    format_recommendations,
    handle_user_interest,
    get_all_skills_text,
    get_user_interest,
    get_last_test_time,
    set_last_test_time
)
from questions import get_questions

bot = telebot.TeleBot(TOKEN)
user_data = {}

COOLDOWN_SECONDS = 10 * 60  # 10 минут

# Обработка команды /start
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет!\n"
        "💠 Я CareerBot — ваш советчик по карьере!\n\n"
        "Выберите действие:",
        reply_markup=build_main_menu()
    )

# Отправка вопроса квиза
def send_quiz_question(chat_id, user_id):
    data = user_data.get(user_id)
    if not data or "quiz" not in data:
        bot.send_message(chat_id, "Ошибка: квиз не найден.")
        return
    quiz = data["quiz"]
    idx = quiz["index"]
    questions = quiz["questions"]
    if idx >= len(questions):
        bot.send_message(chat_id, "Ошибка: индекс вне диапазона вопросов.")
        return
    q = questions[idx]
    q_text = q["q"]
    kb = telebot.types.InlineKeyboardMarkup()
    for opt_index, opt_text in enumerate(q["options"]):
        # callback_data: quiz_answer:{index}:{option_index}
        kb.add(telebot.types.InlineKeyboardButton(opt_text, callback_data=f"quiz_answer:{idx}:{opt_index}"))
    kb.add(telebot.types.InlineKeyboardButton("⏹ Отменить тест", callback_data="quiz_cancel"))
    bot.send_message(chat_id, f"Вопрос {idx+1}/{len(questions)}:\n\n{q_text}", reply_markup=kb)

# Запуск теста для выбранного интереса
def start_quiz_for_interest(chat_id, user_id, interest):
    last_ts = get_last_test_time(user_id, interest)
    now = int(time.time())
    if last_ts is not None:
        elapsed = now - last_ts
        if elapsed < COOLDOWN_SECONDS:
            remaining = COOLDOWN_SECONDS - elapsed
            mins = remaining // 60
            secs = remaining % 60
            bot.send_message(
                chat_id,
                f"⚠️ Тест по навыку «{interest}» вы уже недавно проходили.\n"
                f"Пожалуйста, подождите {mins} мин {secs} сек или выберите другой навык.\n\n"
                "обмануть меня не получится, я запускаю таймер с самого начала!"
            )
            return

    questions = get_questions(interest)
    if not questions:
        bot.send_message(chat_id, f"Для интереса «{interest}» вопросы не найдены.")
        return
    user_data[user_id] = {
        "interest": interest,
        "quiz": {
            "questions": questions[:10],
            "index": 0,
            "score": 0
        }
    }
    bot.send_message(chat_id, f"Начинаем тест по направлению: <b>{interest}</b>\nОтветьте на вопросы, выбирая вариант кнопкой.", parse_mode='HTML')
    send_quiz_question(chat_id, user_id)

# Обработка callback'ов
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    username = call.from_user.username or "unknown"

    # Рекомендация
    if call.data == "recommend":
        interest = user_data.get(user_id, {}).get("interest")
        interests = [interest] if interest else ["Аналитика"]
        recommendations = generate_recommendation(interests)
        save_recommendation(user_id, ", ".join(recommendations))
        detailed_text = format_recommendations(recommendations)
        bot.send_message(chat_id, "🎯 Рекомендованные направления:\n\n" + detailed_text, parse_mode='HTML')
        return

    # Меню интересов (сохранение интереса)
    if call.data == "interests":
        bot.send_message(chat_id, "📄 Выберите ваши интересы:", reply_markup=build_interests_menu())
        return

    # Сохранение интереса
    if call.data.startswith("interest_"):
        interest = call.data.replace("interest_", "")
        msg = handle_user_interest(user_id, username, interest)
        user_data[user_id] = {"interest": interest}
        bot.send_message(chat_id, msg)
        return

    # Все навыки
    if call.data == "all_skills":
        text = get_all_skills_text()
        bot.send_message(chat_id, text, parse_mode='HTML')
        return

    # Назад в меню
    if call.data == "back":
        bot.send_message(chat_id, "🏠 Главное меню:", reply_markup=build_main_menu())
        return

    # Запуск теста
    if call.data == "quiz":
        interest = user_data.get(user_id, {}).get("interest")
        if not interest:
            interest = get_user_interest(user_id)
            if interest:
                user_data[user_id] = {"interest": interest}
        if interest:
            start_quiz_for_interest(chat_id, user_id, interest)
        else:
            bot.send_message(
                chat_id,
                "⚠️ Вы ещё не выбрали интерес. Пожалуйста, сначала выберите интерес в разделе «📝 Мои интересы» либо выберите сейчас:",
                reply_markup=build_interests_menu_for_quiz()
            )
        return

    # Выбор интереса для теста: callback 'quiz_{interest}'
    if call.data.startswith("quiz_") and not call.data.startswith("quiz_answer"):
        interest = call.data.replace("quiz_", "")
        start_quiz_for_interest(chat_id, user_id, interest)
        return

    # Ответ на вопрос: формат quiz_answer:{index}:{option_index}
    if call.data.startswith("quiz_answer:"):
        parts = call.data.split(":")
        if len(parts) != 3:
            bot.send_message(chat_id, "Неправильный формат ответа.")
            return
        try:
            index = int(parts[1])
            chosen = int(parts[2])
        except ValueError:
            bot.send_message(chat_id, "Неверный формат данных ответа.")
            return

        data = user_data.get(user_id)
        if not data or "quiz" not in data:
            bot.send_message(chat_id, "Квиз неактивен или истёк.")
            return
        quiz = data["quiz"]
        questions = quiz["questions"]
        if index < 0 or index >= len(questions):
            bot.send_message(chat_id, "Неверный индекс вопроса.")
            return

        correct_index = questions[index].get("answer")
        if correct_index is not None and chosen == int(correct_index):
            quiz["score"] += 1

        quiz["index"] += 1

        if quiz["index"] < len(questions):
            send_quiz_question(chat_id, user_id)
        else:
            score = quiz["score"]
            interest_finished = data.get("interest")
            set_last_test_time(user_id, interest_finished, int(time.time()))
            user_data[user_id] = {"interest": interest_finished}
            if score >= 7:
                msg = f"✅ Результат: {score}/{len(questions)} — Этот навык самый подходящий для вас из всех!"
            elif 4 <= score <= 6:
                msg = f"🟡 Результат: {score}/{len(questions)} — Стоит поработать над этим навыком или выбрать другой."
            else:
                msg = f"🔴 Результат: {score}/{len(questions)} — Этот навык совсем не подходит, рекомендуем выбрать другой навык."
            bot.send_message(chat_id, msg, reply_markup=build_main_menu())
            print("Тест пройден! Подождите 10 минут для повторного его прохождения.")
        return

    # Отмена теста
    if call.data == "quiz_cancel":
        if user_id in user_data and "quiz" in user_data[user_id]:
            interest = user_data[user_id].get("interest")
            user_data[user_id] = {"interest": interest}
        bot.send_message(chat_id, "Тест отменён.", reply_markup=build_main_menu())
        return

# Текстовые сообщения
@bot.message_handler(content_types=["text"])
def text_handler(message):
    bot.send_message(
        message.chat.id,
        "⁉️ Пожалуйста, используйте кнопки меню для выбора действий.",
        reply_markup=build_main_menu()
    )

print("CareerBot запущен!")
bot.infinity_polling()
