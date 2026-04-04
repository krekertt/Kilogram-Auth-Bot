from flask import Flask, request, jsonify
import requests
import random
import sqlite3
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# ========== КОНФИГ ==========
BOT_TOKEN = '8081566708:AAHm4ppfiDQMVT_GCsTFmXXe-Z56UWae6AM'
ADMIN_ID = 1726423121
SUPPORT_USERNAME = '@yourples'
SITE_URL = 'http://d92743a6.beget.tech'

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (chat_id INTEGER PRIMARY KEY,
                  username TEXT,
                  first_name TEXT,
                  last_name TEXT,
                  phone TEXT,
                  stars INTEGER DEFAULT 0,
                  is_admin INTEGER DEFAULT 0,
                  is_banned INTEGER DEFAULT 0,
                  ban_reason TEXT,
                  ban_until TEXT,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS numbers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  chat_id INTEGER,
                  phone_number TEXT UNIQUE,
                  type TEXT,
                  price INTEGER DEFAULT 0,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  chat_id INTEGER,
                  amount INTEGER,
                  description TEXT,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS codes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  chat_id INTEGER,
                  code TEXT,
                  phone TEXT,
                  used INTEGER DEFAULT 0,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

init_db()

# ========== ФУНКЦИИ БАЗЫ ДАННЫХ ==========
def get_db():
    return sqlite3.connect('bot_data.db')

def get_stars(chat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT stars FROM users WHERE chat_id = ?", (chat_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def add_stars(chat_id, amount, description=""):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET stars = stars + ? WHERE chat_id = ?", (amount, chat_id))
    c.execute("INSERT INTO transactions (chat_id, amount, description) VALUES (?, ?, ?)", (chat_id, amount, description))
    conn.commit()
    conn.close()

def set_stars(chat_id, amount):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET stars = ? WHERE chat_id = ?", (amount, chat_id))
    conn.commit()
    conn.close()

def add_number(chat_id, phone_number, number_type, price=0):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO numbers (chat_id, phone_number, type, price) VALUES (?, ?, ?, ?)", (chat_id, phone_number, number_type, price))
    conn.commit()
    conn.close()

def get_user_numbers(chat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM numbers WHERE chat_id = ? ORDER BY created_at DESC", (chat_id,))
    numbers = c.fetchall()
    conn.close()
    return numbers

def is_number_available(phone_number):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT 1 FROM numbers WHERE phone_number = ?", (phone_number,))
    result = c.fetchone()
    conn.close()
    return result is None

def generate_phone_number(prefix, length):
    number = prefix
    for _ in range(length - len(prefix)):
        number += str(random.randint(0, 9))
    return number

def save_code(chat_id, code, phone):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO codes (chat_id, code, phone) VALUES (?, ?, ?)", (chat_id, str(code), phone))
    conn.commit()
    conn.close()

def verify_code(chat_id, code):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM codes WHERE chat_id = ? AND code = ? AND used = 0 ORDER BY created_at DESC LIMIT 1", (chat_id, str(code)))
    result = c.fetchone()
    if result:
        c.execute("UPDATE codes SET used = 1 WHERE id = ?", (result[0],))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def get_user(chat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
    user = c.fetchone()
    conn.close()
    return user

def create_user(chat_id, username=None, first_name=None, last_name=None):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (chat_id, username, first_name, last_name, stars) VALUES (?, ?, ?, ?, 0)", (chat_id, username, first_name, last_name))
    conn.commit()
    conn.close()

def get_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM numbers")
    numbers = c.fetchone()[0]
    c.execute("SELECT SUM(stars) FROM users")
    stars = c.fetchone()[0] or 0
    conn.close()
    return users, numbers, stars

def get_transactions(limit=10):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM transactions ORDER BY created_at DESC LIMIT ?", (limit,))
    logs = c.fetchall()
    conn.close()
    return logs

# ========== ФУНКЦИИ TELEGRAM ==========
def send_telegram(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
    if reply_markup:
        payload['reply_markup'] = reply_markup
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.json()
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return None

def edit_telegram(chat_id, message_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    payload = {'chat_id': chat_id, 'message_id': message_id, 'text': text, 'parse_mode': 'Markdown'}
    if reply_markup:
        payload['reply_markup'] = reply_markup
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.json()
    except Exception as e:
        print(f"Ошибка редактирования: {e}")
        return None

def answer_callback(callback_id, text=None, show_alert=False):
    if not text:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    payload = {'callback_query_id': callback_id, 'text': text, 'show_alert': show_alert}
    try:
        requests.post(url, json=payload, timeout=3)
    except:
        pass

# ========== КЛАВИАТУРЫ ==========
def main_menu_keyboard():
    return {
        'inline_keyboard': [
            [{'text': '📱 Бесплатный номер (+1)', 'callback_data': 'free_number'}, {'text': '💎 Премиум номер (+888)', 'callback_data': 'premium_menu'}],
            [{'text': '👤 Профиль', 'callback_data': 'profile'}, {'text': '🆘 Поддержка', 'callback_data': 'support'}]
        ]
    }

def premium_menu_keyboard():
    return {
        'inline_keyboard': [
            [{'text': '🎲 Случайный длинный (5⭐)', 'callback_data': 'premium_random'}],
            [{'text': '✏️ Выбрать короткий (10⭐)', 'callback_data': 'premium_custom'}],
            [{'text': '◀️ Назад', 'callback_data': 'back_to_main'}]
        ]
    }

def profile_keyboard():
    return {
        'inline_keyboard': [
            [{'text': '💰 Пополнить баланс', 'callback_data': 'buy_stars'}],
            [{'text': '📱 Мои номера', 'callback_data': 'my_numbers'}, {'text': '◀️ Назад', 'callback_data': 'back_to_main'}]
        ]
    }

def buy_stars_keyboard():
    return {
        'inline_keyboard': [
            [{'text': '10 ⭐', 'callback_data': 'pay_10'}, {'text': '50 ⭐', 'callback_data': 'pay_50'}],
            [{'text': '100 ⭐', 'callback_data': 'pay_100'}, {'text': '500 ⭐', 'callback_data': 'pay_500'}],
            [{'text': '◀️ Назад', 'callback_data': 'profile'}]
        ]
    }

def back_keyboard():
    return {'inline_keyboard': [[{'text': '◀️ Назад', 'callback_data': 'back_to_main'}]]}

def admin_menu_keyboard():
    return {
        'inline_keyboard': [
            [{'text': '👥 Пользователи', 'callback_data': 'admin_users'}, {'text': '📱 Номера', 'callback_data': 'admin_numbers'}],
            [{'text': '💰 Звёзды', 'callback_data': 'admin_stars'}, {'text': '🔨 Баны', 'callback_data': 'admin_bans'}],
            [{'text': '📊 Статистика', 'callback_data': 'admin_stats'}, {'text': '📝 Логи', 'callback_data': 'admin_logs'}],
            [{'text': '◀️ Назад', 'callback_data': 'back_to_main'}]
        ]
    }

def admin_users_keyboard():
    return {
        'inline_keyboard': [
            [{'text': '🔍 Найти пользователя', 'callback_data': 'admin_find_user'}],
            [{'text': '➕ Добавить звёзды', 'callback_data': 'admin_add_stars'}, {'text': '⚖️ Установить баланс', 'callback_data': 'admin_set_balance'}],
            [{'text': '🔄 Обнулить баланс', 'callback_data': 'admin_reset_balance'}, {'text': '🔨 Забанить', 'callback_data': 'admin_ban_user'}],
            [{'text': '◀️ Назад', 'callback_data': 'admin_back'}]
        ]
    }

# ========== ВЕБХУК ==========
@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = request.json
    if not update:
        return jsonify({'ok': False})
    
    # Обработка сообщений
    if 'message' in update:
        msg = update['message']
        chat_id = msg['chat']['id']
        text = msg.get('text', '')
        
        create_user(chat_id, msg['chat'].get('username'), msg['chat'].get('first_name'), msg['chat'].get('last_name'))
        
        if text == '/start':
            stars = get_stars(chat_id)
            if chat_id == ADMIN_ID:
                send_telegram(chat_id, "👑 *Админ-панель*\n\nВыберите действие:", admin_menu_keyboard())
            else:
                send_telegram(chat_id, f"🌟 *KiloGram Bot*\n\n⭐ Баланс: {stars}\n\nВыберите действие:", main_menu_keyboard())
    
    # Обработка нажатий на кнопки
    elif 'callback_query' in update:
        callback = update['callback_query']
        chat_id = callback['message']['chat']['id']
        message_id = callback['message']['message_id']
        data = callback['data']
        callback_id = callback['id']
        
        stars = get_stars(chat_id)
        
        # ===== ГЛАВНОЕ МЕНЮ =====
        if data == 'back_to_main':
            if chat_id == ADMIN_ID:
                edit_telegram(chat_id, message_id, "👑 *Админ-панель*\n\nВыберите действие:", admin_menu_keyboard())
            else:
                edit_telegram(chat_id, message_id, f"🌟 *KiloGram Bot*\n\n⭐ Баланс: {stars}\n\nВыберите действие:", main_menu_keyboard())
            answer_callback(callback_id)
        
        elif data == 'profile':
            user = get_user(chat_id)
            text = f"👤 *Ваш профиль*\n\n🆔 ID: `{chat_id}`\n⭐ Баланс: {stars}\n📅 Регистрация: {user[10] if user else 'неизвестно'}"
            edit_telegram(chat_id, message_id, text, profile_keyboard())
            answer_callback(callback_id)
        
        elif data == 'support':
            edit_telegram(chat_id, message_id, f"🆘 *Поддержка*\n\nСвяжитесь с нами: {SUPPORT_USERNAME}", back_keyboard())
            answer_callback(callback_id)
        
        elif data == 'buy_stars':
            edit_telegram(chat_id, message_id, "⭐ *Пополнение баланса*\n\nВыберите количество звёзд:", buy_stars_keyboard())
            answer_callback(callback_id)
        
        elif data.startswith('pay_'):
            amount = int(data.replace('pay_', ''))
            answer_callback(callback_id, f"✅ Оплата {amount}⭐ - в разработке", show_alert=True)
        
        # ===== НОМЕРА =====
        elif data == 'free_number':
            numbers = get_user_numbers(chat_id)
            free_exists = any(n[3] == 'free' for n in numbers)
            if free_exists:
                answer_callback(callback_id, "❌ У вас уже есть бесплатный номер", show_alert=True)
                return
            
            number = generate_phone_number("+1", 12)
            while not is_number_available(number):
                number = generate_phone_number("+1", 12)
            
            add_number(chat_id, number, 'free')
            text = f"✅ *Бесплатный номер получен!*\n\n📱 Ваш номер: `{number}`"
            edit_telegram(chat_id, message_id, text)
            answer_callback(callback_id)
        
        elif data == 'premium_menu':
            text = f"💎 *Премиум номера +888*\n\n• Длинный номер — 5⭐ (случайный)\n• Короткий номер — 10⭐ (вы выбираете)\n\n⭐ Ваш баланс: *{stars}*"
            edit_telegram(chat_id, message_id, text, premium_menu_keyboard())
            answer_callback(callback_id)
        
        elif data == 'premium_random':
            if stars < 5:
                answer_callback(callback_id, "❌ Недостаточно звёзд. Нужно 5⭐", show_alert=True)
                return
            
            number = generate_phone_number("+888", 12)
            while not is_number_available(number):
                number = generate_phone_number("+888", 12)
            
            add_stars(chat_id, -5, "Покупка длинного номера")
            add_number(chat_id, number, 'premium_random', 5)
            text = f"✅ *Премиум номер куплен!*\n\n📱 Ваш номер: `{number}`\n⭐ Списано: 5"
            edit_telegram(chat_id, message_id, text)
            answer_callback(callback_id)
        
        elif data == 'premium_custom':
            if stars < 10:
                answer_callback(callback_id, "❌ Недостаточно звёзд. Нужно 10⭐", show_alert=True)
                return
            answer_callback(callback_id, "✏️ Введите желаемый номер (3-6 цифр)", show_alert=True)
        
        elif data == 'my_numbers':
            numbers = get_user_numbers(chat_id)
            if not numbers:
                answer_callback(callback_id, "📱 У вас пока нет номеров", show_alert=True)
                return
            text = "📱 *Ваши номера*\n\n"
            for num in numbers:
                type_text = "Бесплатный" if num[3] == 'free' else "Премиум"
                text += f"• `{num[2]}` — {type_text}\n"
            edit_telegram(chat_id, message_id, text, back_keyboard())
            answer_callback(callback_id)
        
        # ===== АДМИН ПАНЕЛЬ =====
        elif data == 'admin_users':
            edit_telegram(chat_id, message_id, "👥 *Управление пользователями*\n\nВыберите действие:", admin_users_keyboard())
            answer_callback(callback_id)
        
        elif data == 'admin_stats':
            users, numbers, stars_total = get_stats()
            text = f"📊 *Статистика*\n\n👥 Пользователей: {users}\n📱 Номеров: {numbers}\n⭐ Всего звёзд: {stars_total}"
            edit_telegram(chat_id, message_id, text, back_keyboard())
            answer_callback(callback_id)
        
        elif data == 'admin_logs':
            logs = get_transactions(10)
            text = "📝 *Последние транзакции*\n\n"
            for log in logs:
                text += f"• {log[4][:10]} | {log[2]}⭐ {log[3]}\n"
            edit_telegram(chat_id, message_id, text, back_keyboard())
            answer_callback(callback_id)
        
        elif data == 'admin_back':
            edit_telegram(chat_id, message_id, "👑 *Админ-панель*\n\nВыберите действие:", admin_menu_keyboard())
            answer_callback(callback_id)
        
        elif data == 'admin_find_user':
            answer_callback(callback_id, "🔍 Введите ID пользователя", show_alert=True)
        
        elif data == 'admin_add_stars':
            answer_callback(callback_id, "➕ Введите ID и количество звёзд", show_alert=True)
        
        elif data == 'admin_set_balance':
            answer_callback(callback_id, "⚖️ Введите ID и новый баланс", show_alert=True)
        
        elif data == 'admin_reset_balance':
            answer_callback(callback_id, "🔄 Введите ID пользователя", show_alert=True)
        
        elif data == 'admin_ban_user':
            answer_callback(callback_id, "🔨 Введите ID, время(часы) и причину", show_alert=True)
    
    return jsonify({'ok': True})

# ========== API ДЛЯ САЙТА ==========
@app.route('/send_code', methods=['POST'])
def send_code():
    try:
        data = request.json
        chat_id = data.get('chat_id')
        phone = data.get('phone')
        
        if not chat_id:
            return jsonify({'error': 'no_chat_id'}), 400
        
        code = random.randint(100000, 999999)
        save_code(chat_id, str(code), phone)
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        params = {'chat_id': chat_id, 'text': f"🔑 Код подтверждения: {code}", 'parse_mode': 'HTML'}
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            return jsonify({'success': True, 'code': code})
        return jsonify({'error': 'telegram_error'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/verify_code', methods=['POST'])
def verify_code():
    try:
        data = request.json
        chat_id = data.get('chat_id')
        code = data.get('code')
        
        if verify_code(chat_id, code):
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'invalid_code'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'bot': 'KiloGram'})

@app.route('/')
def index():
    return jsonify({
        'name': 'KiloGram Bot',
        'status': 'running',
        'endpoints': ['/health', '/send_code', '/verify_code', '/webhook']
    })

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Бот запущен на порту {port}")
    app.run(host='0.0.0.0', port=port)
