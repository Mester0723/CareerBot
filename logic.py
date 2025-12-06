import sqlite3
from config import DB_NAME
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Создание базы данных при импорте
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        interests TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        recommendation TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS test_attempts (
        user_id INTEGER,
        interest TEXT,
        last_test_ts INTEGER,
        PRIMARY KEY (user_id, interest)
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

# Сохранение рекомендаций
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
    "Программирование": ["Логика", "Математика", "Аналитика"],
    "Дизайн": ["Творчество", "Визуальное мышление", "Эстетика"],
    "Маркетинг": ["Коммуникации", "Креативность", "Аналитика"],
    "Менеджмент": ["Организация", "Лидерство", "Командная работа"],
    "Наука": ["Любопытство", "Исследования", "Аналитика"]
}

# Подробные описания направлений + примеры
NBSP = "\u00A0"
CAREER_DESCRIPTIONS = {
    "Программирование": (
        "💻 <i>Разработка программного обеспечения: создание приложений, сайтов и сервисов.</i>\n\n"
        "<b>Что можно делать с этим навыком:</b>\n"
        "• Писать веб- и мобильные приложения.\n"
        "• Автоматизировать рутинные задачи и обрабатывать данные.\n"
        "• Работать в продуктовых командах, аутсорс-компаниях или на фрилансе.\n\n"
        "<b>Как начать:</b>\n"
        f"{NBSP}{NBSP}Изучите язык (Python/JavaScript), сделайте мини‑проект и опубликуйте код на GitHub."
    ),
    "Дизайн": (
        "🎨 <i>Создание визуальной части продуктов: графический дизайн, UI/UX, иллюстрации.</i>\n\n"
        "<b>Что можно делать с этим навыком:</b>\n"
        "• Проектировать интерфейсы и прототипы (UI/UX).\n"
        "• Создавать логотипы, брендбуки и рекламные визуалы.\n"
        "• Работать в студии, продуктовой команде или брать заказы на фрилансе.\n\n"
        "<b>Как начать:</b>\n"
        f"{NBSP}{NBSP}Освойте Figma/Adobe, сделайте 3–5 работ в портфолио и опубликуйте их."
    ),
    "Маркетинг": (
        "💼 <i>Продвижение продуктов и услуг: контент, реклама, аналитика рынков.</i>\n\n"
        "<b>Что можно делать с этим навыком:</b>\n"
        "• Запускать рекламные кампании (таргет/контекст).\n"
        "• Вести контент и SMM, работать с метриками и аналитикой.\n"
        "• Работать в агентстве, в продуктовой команде или как независимый специалист.\n\n"
        "<b>Как начать:</b>\n"
        f"{NBSP}{NBSP}Изучите основы SMM и таргетинга, запустите тестовую кампанию или ведите собственный канал."
    ),
    "Менеджмент": (
        "📋 <i>Организация работы команд и проектов: планирование, коммуникация, контроль.</i>\n\n"
        "<b>Что можно делать с этим навыком:</b>\n"
        "• Руководить проектами как PM, распределять задачи и оценивать риски.\n"
        "• Настраивать процессы и проводить ретроспективы.\n"
        "• Координировать команды в компаниях разных размеров или запускать собственные проекты.\n\n"
        "<b>Как начать:</b>\n"
        f"{NBSP}{NBSP}Попробуйте координировать небольшой проект, изучите Agile/Scrum и возьмите роль координатора."
    ),
    "Наука": (
        "🧪 <i>Исследовательская деятельность: эксперименты, анализ данных и публикации.</i>\n\n"
        "<b>Что можно делать с этим навыком:</b>\n"
        "• Проводить исследования и эксперименты в академии или R&D.\n"
        "• Анализировать данные, строить модели и решать прикладные задачи.\n"
        "• Публиковать статьи и участвовать в конференциях.\n\n"
        "<b>Как начать:</b>\n"
        f"{NBSP}{NBSP}Изучите методологию исследований и статистику, найдите курс или ментора и начните мини‑проект."
    )
}

# Экранирование HTML для динамических значений
def _escape_html(text: str) -> str:
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))

# Построение главного меню
def build_main_menu():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🎯 Получить рекомендацию", callback_data="recommend"))
    kb.add(InlineKeyboardButton("🧪 Пройти тест", callback_data="quiz"))
    kb.add(InlineKeyboardButton("📚 Все навыки", callback_data="all_skills"))
    kb.add(InlineKeyboardButton("📝 Мои интересы", callback_data="interests"))
    return kb

# Построение меню выбора интересов
def build_interests_menu():
    kb = InlineKeyboardMarkup()
    for career in CAREER_OPTIONS.keys():
        kb.add(InlineKeyboardButton(career, callback_data=f"interest_{career}"))
    kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="back"))
    return kb

# Меню выбора интереса для запуска теста
def build_interests_menu_for_quiz():
    kb = InlineKeyboardMarkup()
    for career in CAREER_OPTIONS.keys():
        kb.add(InlineKeyboardButton(career, callback_data=f"quiz_{career}"))
    kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="back"))
    return kb

# Получить сохранённый интерес пользователя
def get_user_interest(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT interests FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        return row[0]
    return None

# Сохранить/обновить время последнего теста
def set_last_test_time(user_id, interest, ts):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO test_attempts (user_id, interest, last_test_ts)
        VALUES (?, ?, ?)
    """, (user_id, interest, int(ts)))
    conn.commit()
    conn.close()

# Получить время последнего теста
def get_last_test_time(user_id, interest):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT last_test_ts FROM test_attempts WHERE user_id = ? AND interest = ?", (user_id, interest))
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        return int(row[0])
    return None

# Генерация рекомендаций на основе интересов пользователя
def generate_recommendation(user_interests):
    recommended = []
    for career, skills in CAREER_OPTIONS.items():
        if any(interest in skills for interest in user_interests):
            recommended.append(career)
    if not recommended:
        recommended = ["Менеджмент", "Маркетинг", "Дизайн"]
    return recommended

# Форматирование рекомендаций
def format_recommendations(recommendations):
    return "\n".join(f"• <b>{_escape_html(c)}</b>" for c in recommendations)

# Получение полного списка направлений и навыков
def get_all_skills_text():
    parts = []
    for career, skills in CAREER_OPTIONS.items():
        desc = CAREER_DESCRIPTIONS.get(career, "")
        skills_str = ", ".join(skills)
        parts.append(f"<b>{_escape_html(career)}</b>\n{desc}\n\n<b>Навыки:</b> {_escape_html(skills_str)}")
    header = "📚 <b>Полный список направлений и навыков</b>:\n\n"
    return header + "\n\n".join(parts)

# Обработка выбранного интереса пользователем
def handle_user_interest(user_id, username, interest):
    save_user_interests(user_id, username, interest)
    return f"Ваш интерес «{interest}» сохранен ✅"