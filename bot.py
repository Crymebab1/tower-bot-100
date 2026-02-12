import os
import telebot
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from database import *

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ========== ИНИЦИАЛИЗАЦИЯ ==========
init_db()

# ========== ПРОВЕРКА ТЕЛЕГРАМ ==========
def check_sub(chat_id, channel):
    try:
        status = bot.get_chat_member(channel, chat_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return False

# ========== АДМИН-ПАНЕЛЬ ==========
ADMIN_ID = 123456789  # ЗАМЕНИ НА СВОЙ TELEGRAM ID!

def is_admin(chat_id):
    return chat_id == ADMIN_ID

# ========== КОМАНДА START ==========
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user = get_user(chat_id)
    
    if not user:
        # ПРОВЕРЯЕМ: есть ли места?
        result, position, unique, tier_name, vote = add_user(
            chat_id,
            message.from_user.username,
            message.from_user.first_name
        )
        
        if result == "FULL":
            text = """
❌ **ДОСТИГНУТ ЛИМИТ В 100 УЧАСТНИКОВ!**

😢 К сожалению, все места заняты.
Вы можете следить за проектом в соцсетях.

Спасибо за интерес! 🌟
            """
            bot.send_message(chat_id, text, parse_mode='Markdown')
            return
        
        # НОВЫЙ ПОЛЬЗОВАТЕЛЬ
        text = f"""
🗼 **ПЕРВАЯ СОТНЯ ЭЙФЕЛЕВОЙ БАШНИ**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎫 **ТВОЙ УНИКАЛЬНЫЙ НОМЕР:**  
`{unique}`

📊 **ПОЗИЦИЯ:** #{position}/100
🏆 **СТАТУС:** {tier_name}
🗳 **СИЛА ГОЛОСА:** {vote} баллов
💰 **СТАРТОВЫЙ БОНУС:** 100 монет

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 **ДЛЯ АКТИВАЦИИ ПОДПИШИСЬ:**

📱 Telegram:
1️⃣ {TG_CHANNEL_1}
2️⃣ {TG_CHANNEL_2}

📸 Instagram:
3️⃣ @{INSTAGRAM_1}
4️⃣ @{INSTAGRAM_2}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎁 **БОНУС ЗА ПОДПИСКУ:** +{BONUS_COINS} монет
✅ **ПОДПИШИСЬ И НАЖМИ КНОПКУ!**
        """
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("📱 КАНАЛ 1", url=TG_LINK_1),
            InlineKeyboardButton("📱 КАНАЛ 2", url=TG_LINK_2),
            InlineKeyboardButton("📸 INSTAGRAM 1", url=INSTA_LINK_1),
            InlineKeyboardButton("📸 INSTAGRAM 2", url=INSTA_LINK_2),
            InlineKeyboardButton("✅ ПРОВЕРИТЬ ПОДПИСКИ", callback_data="check"),
            InlineKeyboardButton("📊 СТАТУС", callback_data="status")
        )
        
        bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=keyboard)
    
    elif user and not user['is_verified']:
        # НЕ ВЕРИФИЦИРОВАН
        text = f"""
🔒 **ТВОЙ НОМЕР:** `{user['unique_number']}`
📊 **ПОЗИЦИЯ:** #{user['position']}/100

⚠️ **ДЛЯ АКТИВАЦИИ ПОДПИШИСЬ НА КАНАЛЫ!**
        """
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("📱 КАНАЛ 1", url=TG_LINK_1),
            InlineKeyboardButton("📱 КАНАЛ 2", url=TG_LINK_2),
            InlineKeyboardButton("📸 INSTAGRAM 1", url=INSTA_LINK_1),
            InlineKeyboardButton("📸 INSTAGRAM 2", url=INSTA_LINK_2),
            InlineKeyboardButton("✅ ПРОВЕРИТЬ", callback_data="check")
        )
        bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=keyboard)
    
    else:
        # ВЕРИФИЦИРОВАННЫЙ ПОЛЬЗОВАТЕЛЬ
        show_main_menu(chat_id, user)

def show_main_menu(chat_id, user):
    """Главное меню"""
    text = f"""
🗼 **ПЕРВАЯ СОТНЯ - ГЛАВНОЕ МЕНЮ**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎫 **НОМЕР:** `{user['unique_number']}`
📊 **ПОЗИЦИЯ:** #{user['position']}/100
🏆 **СТАТУС:** {user['tier_name']}
💰 **БАЛАНС:** {user['coins']} монет
🗳 **ГОЛОС:** {user['votes_power']} баллов

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 **КОМАНДЫ:**

/profile - 👤 Мой профиль
/rating - 🏆 Рейтинг первой сотни
/check - ✅ Статус подписок
/referral - 🤝 Пригласить друга
/top100 - 📊 Кто в первой сотне
    """
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("👤 ПРОФИЛЬ", callback_data="profile"),
        InlineKeyboardButton("🏆 РЕЙТИНГ", callback_data="rating"),
        InlineKeyboardButton("✅ ПРОВЕРИТЬ", callback_data="check"),
        InlineKeyboardButton("📊 ТОП-100", callback_data="top100")
    )
    
    bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=keyboard)

# ========== ПРОВЕРКА ПОДПИСОК ==========
@bot.callback_query_handler(func=lambda call: call.data == "check")
def check_subs(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    bot.edit_message_text("🔍 **ПРОВЕРКА ПОДПИСОК...**", chat_id, msg_id, parse_mode='Markdown')
    
    # Проверяем Telegram
    tg1 = check_sub(chat_id, TG_CHANNEL_1)
    tg2 = check_sub(chat_id, TG_CHANNEL_2)
    
    if tg1 and tg2:
        verify_user(chat_id)
        user = get_user(chat_id)
        
        text = f"""
✅ **ПОЗДРАВЛЯЮ! ТЫ В ПЕРВОЙ СОТНЕ!**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎫 **ТВОЙ НОМЕР:** `{user['unique_number']}`
📊 **ПОЗИЦИЯ:** #{user['position']}/100
🏆 **СТАТУС:** {user['tier_name']}
💰 **БОНУС:** +{BONUS_COINS} монет
💎 **БАЛАНС:** {user['coins']} монет

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📸 **INSTAGRAM:**
✅ Отправь скриншот подписки админу
🎁 Бонус: +500 монет

👤 Админ: @your_username  # ЗАМЕНИ!
        """
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ", callback_data="menu"))
        
        bot.edit_message_text(text, chat_id, msg_id, parse_mode='Markdown', reply_markup=keyboard)
    else:
        text = "❌ **НЕ ВСЕ ПОДПИСКИ!**\n\nПодпишись на оба Telegram канала и нажми снова."
        bot.edit_message_text(text, chat_id, msg_id, parse_mode='Markdown')

# ========== ПРОФИЛЬ ==========
@bot.message_handler(commands=['profile'])
def profile(message):
    chat_id = message.chat.id
    user = get_user(chat_id)
    
    if not user:
        start(message)
        return
    
    tg_status = "✅" if user['tg_verified'] else "❌"
    insta_status = "✅" if user['insta_verified'] else "⏳"
    
    text = f"""
👤 **ПРОФИЛЬ УЧАСТНИКА ПЕРВОЙ СОТНИ**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎫 `{user['unique_number']}`
📌 #{user['position']}/100
🏆 {user['tier_name']}
💰 {user['coins']} монет
🗳 {user['votes_power']} баллов

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **СТАТУС ПОДПИСОК:**

📱 Telegram: {tg_status}
📸 Instagram: {insta_status}

📅 РЕГИСТРАЦИЯ: {user['created_at'].strftime('%d.%m.%Y')}
    """
    
    bot.send_message(chat_id, text, parse_mode='Markdown')

# ========== РЕЙТИНГ ==========
@bot.message_handler(commands=['rating'])
def rating(message):
    top = get_top_users(10)
    
    text = """
🏆 **ТОП-10 ПЕРВОЙ СОТНИ**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    
    if not top:
        text += "\n❌ Пока нет активных участников"
    else:
        for i, u in enumerate(top, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            name = u['username'] or u['unique_number']
            text += f"\n{medal} {name[:10]} — {u['coins']}💰"
    
    # Добавляем статистику
    total, verified, insta = get_stats()
    
    text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **СТАТИСТИКА ПРОЕКТА:**

👥 Участников: {total}/100
✅ Активировано: {verified}
📸 Instagram: {insta}
    """
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# ========== ТОП-100 ==========
@bot.message_handler(commands=['top100'])
def top100(message):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('''
        SELECT unique_number, username, position, tier_name
        FROM users 
        WHERE is_verified = TRUE
        ORDER BY position
        LIMIT 100
    ''')
    users = cur.fetchall()
    cur.close()
    conn.close()
    
    text = "📊 **УЧАСТНИКИ ПЕРВОЙ СОТНИ**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for u in users[:20]:  # Показываем первых 20
        text += f"\n#{u['position']:03d} | {u['unique_number']} | {u['tier_name'][:10]}"
    
    text += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    text += f"\n✅ Всего активировано: {len(users)}/100"
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# ========== АДМИН-КОМАНДЫ ==========
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.chat.id):
        bot.send_message(message.chat.id, "❌ Доступ запрещен")
        return
    
    text = """
👑 **АДМИН-ПАНЕЛЬ**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📸 **ПОДТВЕРДИТЬ INSTAGRAM:**
/admin_insta 123456789

📊 **СТАТИСТИКА:**
/stats

🔄 **ПРОВЕРИТЬ ВСЕХ:**
/check_all
    """
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['admin_insta'])
def admin_insta(message):
    if not is_admin(message.chat.id):
        return
    
    try:
        user_id = int(message.text.split()[1])
        verify_instagram(user_id)
        bot.send_message(message.chat.id, f"✅ Instagram подтвержден для {user_id}")
        bot.send_message(user_id, "📸 **Instagram подтвержден!**\n✅ +500 монет")
    except:
        bot.send_message(message.chat.id, "❌ Используй: /admin_insta 123456789")

@bot.message_handler(commands=['stats'])
def stats(message):
    if not is_admin(message.chat.id):
        return
    
    total, verified, insta = get_stats()
    
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT SUM(coins) FROM users')
    total_coins = cur.fetchone()[0] or 0
    cur.close()
    conn.close()
    
    text = f"""
📊 **СТАТИСТИКА ПРОЕКТА**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 Участники: {total}/100
✅ Telegram: {verified}
📸 Instagram: {insta}
💰 Всего монет: {total_coins}

🎯 Осталось мест: {100 - total}
    """
    
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# ========== CALLBACK ХЕНДЛЕРЫ ==========
@bot.callback_query_handler(func=lambda call: call.data == "menu")
def menu_callback(call):
    chat_id = call.message.chat.id
    user = get_user(chat_id)
    if user:
        show_main_menu(chat_id, user)

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def profile_callback(call):
    profile(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "rating")
def rating_callback(call):
    rating(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "top100")
def top100_callback(call):
    top100(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "status")
def status_callback(call):
    total, verified, insta = get_stats()
    text = f"""
📊 **СТАТУС ПРОЕКТА**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 ЗАНЯТО МЕСТ: {total}/100
✅ АКТИВИРОВАНО: {verified}
📸 INSTAGRAM: {insta}

🎯 СВОБОДНЫХ МЕСТ: {100 - total}
    """
    bot.answer_callback_query(call.id, f"Свободно: {100-total} мест", show_alert=True)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='Markdown')

# ========== FLASK ==========
@app.route('/')
def index():
    total, verified, insta = get_stats()
    return f"""
    <h1>🗼 ЭЙФЕЛЕВА БАШНЯ - ПЕРВАЯ СОТНЯ</h1>
    <p>✅ Бот работает!</p>
    <p>👥 Участников: {total}/100</p>
    <p>✅ Активировано: {verified}</p>
    <p>📸 Instagram: {insta}</p>
    """

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'OK', 200

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    print("🚀 ЗАПУСК БОТА ПЕРВАЯ СОТНЯ")
    print(f"👥 Лимит: 100 пользователей")
    
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
