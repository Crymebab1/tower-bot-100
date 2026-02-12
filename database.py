import psycopg2
import psycopg2.extras
import random
import string
from datetime import datetime

def get_conn():
    from config import DATABASE_URL
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """Создание таблиц"""
    conn = get_conn()
    cur = conn.cursor()
    
    # Таблица пользователей (только 100 мест!)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id BIGINT PRIMARY KEY,
            unique_number VARCHAR(30) UNIQUE,
            username TEXT,
            first_name TEXT,
            position INTEGER UNIQUE,
            tier INTEGER,
            tier_name TEXT,
            coins INTEGER DEFAULT 0,
            votes_power DECIMAL(3,1) DEFAULT 0,
            is_verified BOOLEAN DEFAULT FALSE,
            tg_verified BOOLEAN DEFAULT FALSE,
            insta_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(),
            last_active TIMESTAMP DEFAULT NOW()
        )
    ''')
    
    # Таблица для рейтинга
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT REFERENCES users(chat_id),
            unique_number VARCHAR(30),
            rating_value INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ База данных готова")

def get_user_count():
    """Количество пользователей"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM users')
    count = cur.fetchone()[0] or 0
    cur.close()
    conn.close()
    return count

def generate_number(position):
    """Генерация номера для ТОП-100"""
    if position <= 10:
        return f"TOP-{position:02d}", 1, "👑 ТОП-10 ЭЛИТА", 2.0
    elif position <= 30:
        return f"VIP-{position:02d}", 2, "💎 ВИП ПРЕМИУМ", 1.5
    elif position <= 60:
        return f"PRO-{position:02d}", 3, "⚡️ ПРО УЧАСТНИК", 1.0
    elif position <= 100:
        return f"MEM-{position:03d}", 4, "🎯 ПЕРВАЯ СОТНЯ", 0.5
    else:
        return None, None, None, None  # МЕСТ ЗАНЯТО!

def add_user(chat_id, username, first_name):
    """Добавление нового пользователя (только 100 мест!)"""
    
    # ПРОВЕРЯЕМ: есть ли свободные места?
    current_count = get_user_count()
    
    if current_count >= 100:
        return "FULL", None, None, None  # МЕСТ БОЛЬШЕ НЕТ!
    
    conn = get_conn()
    cur = conn.cursor()
    
    position = current_count + 1
    unique, tier, tier_name, vote = generate_number(position)
    
    cur.execute('''
        INSERT INTO users (
            chat_id, unique_number, username, first_name, 
            position, tier, tier_name, votes_power, coins
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (chat_id) DO NOTHING
    ''', (chat_id, unique, username, first_name, position, tier, tier_name, vote, 100))
    
    conn.commit()
    cur.close()
    conn.close()
    return "OK", position, unique, tier_name, vote

def get_user(chat_id):
    """Получение пользователя"""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('SELECT * FROM users WHERE chat_id = %s', (chat_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def verify_user(chat_id):
    """Подтверждение пользователя"""
    from config import BONUS_COINS
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        UPDATE users SET 
            is_verified = TRUE,
            tg_verified = TRUE,
            coins = coins + %s,
            last_active = NOW()
        WHERE chat_id = %s
    ''', (BONUS_COINS, chat_id))
    conn.commit()
    cur.close()
    conn.close()

def verify_instagram(chat_id):
    """Ручное подтверждение Instagram админом"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        UPDATE users SET 
            insta_verified = TRUE,
            coins = coins + 500,
            last_active = NOW()
        WHERE chat_id = %s
    ''', (chat_id,))
    conn.commit()
    cur.close()
    conn.close()

def get_top_users(limit=10):
    """Топ пользователей"""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('''
        SELECT unique_number, username, coins, position, tier_name
        FROM users 
        WHERE is_verified = TRUE
        ORDER BY coins DESC 
        LIMIT %s
    ''', (limit,))
    users = cur.fetchall()
    cur.close()
    conn.close()
    return users

def get_stats():
    """Статистика бота"""
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM users')
    total = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM users WHERE is_verified = TRUE')
    verified = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM users WHERE insta_verified = TRUE')
    insta = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    return total, verified, insta
