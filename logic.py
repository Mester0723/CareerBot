import sqlite3
from config import DB_NAME
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Создание базы данных при импорте
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Таблица пользователей
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        interests TEXT
    )
    """)

    # Таблица рекомендаций
    cur.execute("""
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        recommendation TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# Работа с пользователями
def save_user_interests(user_id, username, interests):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO users (user_id, username, interests)
        VALUES (?, ?, ?)
    """, (user_id, username, interests))
    conn.commit()
    conn.close()


def save_recommendation(user_id, recommendation):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO recommendations (user_id, recommendation)
        VALUES (?, ?)
    """, (user_id, recommendation))
    conn.commit()
    conn.close()

# Логика рекомендаций
CAREER_OPTIONS = {
    "Программирование 💻": ["Логика", "Математика", "Аналитика"],
    "Дизайн 🎨": ["Творчество", "Визуальное мышление", "Эстетика"],
    "Маркетинг 💼": ["Коммуникации", "Креативность", "Аналитика"],
    "Менеджмент 📋": ["Организация", "Лидерство", "Командная работа"],
    "Наука 🧪": ["Любопытство", "Исследования", "Аналитика"]
}

def build_main_menu():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🎯 Получить рекомендацию", callback_data="recommend"))
    kb.add(InlineKeyboardButton("📝 Мои интересы", callback_data="interests"))
    return kb

def build_interests_menu():
    kb = InlineKeyboardMarkup()
    for career in CAREER_OPTIONS.keys():
        kb.add(InlineKeyboardButton(career, callback_data=f"interest_{career}"))
    kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="back"))
    return kb

def generate_recommendation(user_interests):
    recommended = []
    for career, skills in CAREER_OPTIONS.items():
        if any(interest in skills for interest in user_interests):
            recommended.append(career)
    if not recommended:
        recommended = ["Менеджмент", "Маркетинг", "Дизайн"]
    return recommended

def handle_user_interest(user_id, username, interest):
    save_user_interests(user_id, username, interest)
    return f"Ваш интерес «{interest}» сохранен ✅"