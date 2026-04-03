import random
import requests
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import os

# ========== КОНФИГ ==========
BOT_TOKEN = '8081566708:AAHm4ppfiDQMVT_GCsTFmXXe-Z56UWae6AM'
ADMIN_ID = 1726423121
SUPPORT_USERNAME = '@yourples'  # Замени на свой
HOST = '178.104.40.37'
PORT = 25633
API_URL="http://d92743a6.beget.tech/api.php"

# ========== БАЗА ДАННЫХ ==========
def get_db():
    conn = sqlite3.connect('bot_data.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    
    # Пользователи
    conn.execute('''CREATE TABLE IF NOT EXISTS users
                    (chat_id INTEGER PRIMARY KEY,
                     username TEXT,
                     first_name TEXT,
                     last_name TEXT,
                     phone TEXT,
                     stars INTEGER DEFAULT 0,
                     is_admin INTEGER DEFAULT 0,
                     is_banned INTEGER DEFAULT 0,
                     ban_reason TEXT,
                     ban_until DATETIME,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Номера
    conn.execute('''CREATE TABLE IF NOT EXISTS numbers
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     chat_id INTEGER,
                     phone_number TEXT UNIQUE,
                     type TEXT,
                     price INTEGER DEFAULT 0,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Транзакции
    conn.execute('''CREATE TABLE IF NOT EXISTS transactions
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     chat_id INTEGER,
                     amount INTEGER,
                     description TEXT,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Коды подтверждения
    conn.execute('''CREATE TABLE IF NOT EXISTS codes
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     chat_id INTEGER,
                     code TEXT,
                     phone TEXT,
                     used INTEGER DEFAULT 0,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

init_db()

# ========== ФУНКЦИИ БОТА ==========

def send_message(chat_id, text, parse_mode='HTML', reply_markup=None):
    """Отправка сообщения в Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.json()
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return None

def edit_message(chat_id, message_id, text, parse_mode='HTML', reply_markup=None):
    """Редактирование сообщения"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    payload = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': text,
        'parse_mode': parse_mode
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.json()
    except Exception as e:
        print(f"Ошибка редактирования: {e}")
        return None

def answer_callback(callback_id, text=None, show_alert=False):
    """Ответ на callback запрос"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    payload = {'callback_query_id': callback_id}
    if text:
        payload['text'] = text
        payload['show_alert'] = show_alert
    
    try:
        requests.post(url, json=payload, timeout=3)
    except:
        pass

# ========== КЛАВИАТУРЫ ==========

def main_menu_keyboard():
    """Главное меню"""
    return {
        'inline_keyboard': [
            [
                {'text': '📱 Бесплатный номер (+1)', 'callback_data': 'free_number'},
                {'text': '💎 Премиум номер (+888)', 'callback_data': 'premium_menu'}
            ],
            [
                {'text': '👤 Профиль', 'callback_data': 'profile'},
                {'text': '🆘 Поддержка', 'callback_data': 'support'}
            ]
        ]
    }

def premium_menu_keyboard():
    """Меню премиум номеров"""
    return {
        'inline_keyboard': [
            [
                {'text': '🎲 Случайный длинный (5⭐)', 'callback_data': 'premium_random'}
            ],
            [
                {'text': '✏️ Выбрать короткий (10⭐)', 'callback_data': 'premium_custom'}
            ],
            [
                {'text': '◀️ Назад', 'callback_data': 'back_to_main'}
            ]
        ]
    }

def profile_keyboard():
    """Меню профиля"""
    return {
        'inline_keyboard': [
            [
                {'text': '💰 Пополнить баланс', 'callback_data': 'buy_stars'}
            ],
            [
                {'text': '📱 Мои номера', 'callback_data': 'my_numbers'},
                {'text': '◀️ Назад', 'callback_data': 'back_to_main'}
            ]
        ]
    }

def buy_stars_keyboard():
    """Меню покупки звёзд"""
    return {
        'inline_keyboard': [
            [
                {'text': '10 ⭐', 'callback_data': 'pay_10'},
                {'text': '50 ⭐', 'callback_data': 'pay_50'}
            ],
            [
                {'text': '100 ⭐', 'callback_data': 'pay_100'},
                {'text': '500 ⭐', 'callback_data': 'pay_500'}
            ],
            [
                {'text': '◀️ Назад', 'callback_data': 'profile'}
            ]
        ]
    }

def admin_menu_keyboard():
    """Главное меню админа"""
    return {
        'inline_keyboard': [
            [
                {'text': '👥 Пользователи', 'callback_data': 'admin_users'},
                {'text': '📱 Номера', 'callback_data': 'admin_numbers'}
            ],
            [
                {'text': '💰 Звёзды', 'callback_data': 'admin_stars'},
                {'text': '🔨 Баны', 'callback_data': 'admin_bans'}
            ],
            [
                {'text': '📊 Статистика', 'callback_data': 'admin_stats'},
                {'text': '📝 Логи', 'callback_data': 'admin_logs'}
            ],
            [
                {'text': '◀️ Назад', 'callback_data': 'back_to_main'}
            ]
        ]
    }

def admin_users_keyboard():
    """Меню управления пользователями"""
    return {
        'inline_keyboard': [
            [
                {'text': '🔍 Найти пользователя', 'callback_data': 'admin_find_user'}
            ],
            [
                {'text': '➕ Добавить звёзды', 'callback_data': 'admin_add_stars'},
                {'text': '⚖️ Установить баланс', 'callback_data': 'admin_set_balance'}
            ],
            [
                {'text': '🔄 Обнулить баланс', 'callback_data': 'admin_reset_balance'},
                {'text': '🔨 Забанить', 'callback_data': 'admin_ban_user'}
            ],
            [
                {'text': '◀️ Назад', 'callback_data': 'admin_back'}
            ]
        ]
    }

def back_keyboard():
    """Кнопка назад"""
    return {
        'inline_keyboard': [
            [{'text': '◀️ Назад', 'callback_data': 'back_to_main'}]
        ]
    }

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ==========

def get_user(chat_id):
    """Получить пользователя"""
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,)).fetchone()
    conn.close()
    return dict(user) if user else None

def create_user(chat_id, username=None, first_name=None, last_name=None):
    """Создать пользователя"""
    conn = get_db()
    conn.execute('''INSERT OR IGNORE INTO users 
                    (chat_id, username, first_name, last_name, stars) 
                    VALUES (?, ?, ?, ?, 0)''',
                 (chat_id, username, first_name, last_name))
    conn.commit()
    conn.close()

def update_user(chat_id, **kwargs):
    """Обновить данные пользователя"""
    conn = get_db()
    for key, value in kwargs.items():
        conn.execute(f"UPDATE users SET {key} = ? WHERE chat_id = ?", (value, chat_id))
    conn.commit()
    conn.close()

def get_stars(chat_id):
    """Получить баланс звёзд"""
    conn = get_db()
    result = conn.execute("SELECT stars FROM users WHERE chat_id = ?", (chat_id,)).fetchone()
    conn.close()
    return result['stars'] if result else 0

def add_stars(chat_id, amount, description=""):
    """Добавить звёзды пользователю"""
    conn = get_db()
    conn.execute("UPDATE users SET stars = stars + ? WHERE chat_id = ?", (amount, chat_id))
    conn.execute("INSERT INTO transactions (chat_id, amount, description) VALUES (?, ?, ?)",
                 (chat_id, amount, description))
    conn.commit()
    conn.close()

def set_stars(chat_id, amount):
    """Установить баланс звёзд"""
    conn = get_db()
    conn.execute("UPDATE users SET stars = ? WHERE chat_id = ?", (amount, chat_id))
    conn.commit()
    conn.close()

def add_number(chat_id, phone_number, number_type, price=0):
    """Добавить номер пользователю"""
    conn = get_db()
    conn.execute('''INSERT INTO numbers (chat_id, phone_number, type, price) 
                    VALUES (?, ?, ?, ?)''', (chat_id, phone_number, number_type, price))
    conn.commit()
    conn.close()

def get_user_numbers(chat_id):
    """Получить номера пользователя"""
    conn = get_db()
    numbers = conn.execute("SELECT * FROM numbers WHERE chat_id = ? ORDER BY created_at DESC", 
                          (chat_id,)).fetchall()
    conn.close()
    return [dict(num) for num in numbers]

def is_number_available(phone_number):
    """Проверить, свободен ли номер"""
    conn = get_db()
    result = conn.execute("SELECT 1 FROM numbers WHERE phone_number = ?", (phone_number,)).fetchone()
    conn.close()
    return result is None

def generate_phone_number(prefix, length):
    """Генерация случайного номера"""
    number = prefix
    for _ in range(length - len(prefix)):
        number += str(random.randint(0, 9))
    return number

def save_code(chat_id, code, phone):
    """Сохранить код подтверждения"""
    conn = get_db()
    conn.execute("INSERT INTO codes (chat_id, code, phone) VALUES (?, ?, ?)",
                 (chat_id, str(code), phone))
    conn.commit()
    conn.close()

def verify_code(chat_id, code):
    """Проверить код"""
    conn = get_db()
    result = conn.execute('''SELECT * FROM codes 
                             WHERE chat_id = ? AND code = ? AND used = 0 
                             ORDER BY created_at DESC LIMIT 1''', 
                          (chat_id, str(code))).fetchone()
    
    if result:
        conn.execute("UPDATE codes SET used = 1 WHERE id = ?", (result['id'],))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def get_stats():
    """Получить статистику"""
    conn = get_db()
    stats = {}
    stats['users'] = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    stats['numbers'] = conn.execute("SELECT COUNT(*) FROM numbers").fetchone()[0]
    stats['free_numbers'] = conn.execute("SELECT COUNT(*) FROM numbers WHERE type='free'").fetchone()[0]
    stats['premium_numbers'] = conn.execute("SELECT COUNT(*) FROM numbers WHERE type LIKE 'premium%'").fetchone()[0]
    stats['total_stars'] = conn.execute("SELECT SUM(stars) FROM users").fetchone()[0] or 0
    stats['transactions'] = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    conn.close()
    return stats

def get_transactions(limit=10):
    """Получить последние транзакции"""
    conn = get_db()
    transactions = conn.execute('''SELECT t.*, u.username 
                                   FROM transactions t
                                   LEFT JOIN users u ON t.chat_id = u.chat_id
                                   ORDER BY t.created_at DESC
                                   LIMIT ?''', (limit,)).fetchall()
    conn.close()
    return [dict(t) for t in transactions]

def search_users(query):
    """Поиск пользователей"""
    conn = get_db()
    if query.isdigit():
        users = conn.execute("SELECT * FROM users WHERE chat_id = ?", (int(query),)).fetchall()
    else:
        users = conn.execute('''SELECT * FROM users 
                                WHERE username LIKE ? OR first_name LIKE ? OR last_name LIKE ?''',
                             (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
    conn.close()
    return [dict(u) for u in users]

def send_to_site(chat_id, phone):
    try:
        url = "http://d92743a6.beget.tech/test_sync.php"
        data = {
            'chat_id': chat_id,
            'phone': phone
        }
        response = requests.post(url, json=data, timeout=5)
        print(f"✅ HTTP код: {response.status_code}")
        print(f"📦 Ответ: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
# ========== АДМИН ФУНКЦИИ ==========

def is_admin(chat_id):
    """Проверка на админа"""
    return chat_id == ADMIN_ID

def ban_user(chat_id, reason="Нарушение правил", duration=None):
    """Забанить пользователя"""
    conn = get_db()
    if duration:
        ban_until = datetime.now() + timedelta(hours=duration)
        conn.execute('''UPDATE users SET is_banned = 1, ban_reason = ?, ban_until = ? 
                        WHERE chat_id = ?''', (reason, ban_until, chat_id))
    else:
        conn.execute('''UPDATE users SET is_banned = 1, ban_reason = ?, ban_until = 'permanent' 
                        WHERE chat_id = ?''', (reason, chat_id))
    conn.commit()
    conn.close()

def unban_user(chat_id):
    """Разбанить пользователя"""
    conn = get_db()
    conn.execute('''UPDATE users SET is_banned = 0, ban_reason = NULL, ban_until = NULL 
                    WHERE chat_id = ?''', (chat_id,))
    conn.commit()
    conn.close()

def is_banned(chat_id):
    """Проверка на бан"""
    conn = get_db()
    user = conn.execute("SELECT is_banned, ban_until FROM users WHERE chat_id = ?", 
                       (chat_id,)).fetchone()
    conn.close()
    
    if not user or not user['is_banned']:
        return False
    
    if user['ban_until'] and user['ban_until'] != 'permanent':
        if datetime.now() > datetime.fromisoformat(user['ban_until']):
            unban_user(chat_id)
            return False
    
    return True

# ========== ОБРАБОТЧИК КОМАНД ==========

def handle_command(update):
    """Обработка входящих команд от Telegram"""
    if 'message' in update:
        handle_message(update['message'])
    elif 'callback_query' in update:
        handle_callback(update['callback_query'])

def handle_message(message):
    """Обработка текстовых сообщений"""
    chat_id = message['chat']['id']
    text = message.get('text', '')
    
    # Создаём пользователя если нет
    create_user(
        chat_id,
        username=message['chat'].get('username'),
        first_name=message['chat'].get('first_name'),
        last_name=message['chat'].get('last_name')
    )
    
    # Проверка на бан
    if is_banned(chat_id):
        send_message(chat_id, "⛔ Вы забанены. Доступ запрещён.")
        return
    
    # Обработка команд
    if text == '/start':
        stars = get_stars(chat_id)
        if is_admin(chat_id):
            text = f"👑 *Админ-панель*\n\nВыберите действие:"
            send_message(chat_id, text, parse_mode='Markdown', 
                        reply_markup=admin_menu_keyboard())
        else:
            text = f"🌟 *KiloGram Bot*\n\n⭐ Баланс: {stars}\n\nВыберите действие:"
            send_message(chat_id, text, parse_mode='Markdown', 
                        reply_markup=main_menu_keyboard())
    
    elif text == '/admin' and is_admin(chat_id):
        send_message(chat_id, "👑 *Админ-панель*", parse_mode='Markdown',
                    reply_markup=admin_menu_keyboard())
    
    elif text.startswith('/ban ') and is_admin(chat_id):
        parts = text.split()
        if len(parts) >= 2:
            target_id = int(parts[1])
            reason = ' '.join(parts[2:]) if len(parts) > 2 else "Нарушение правил"
            ban_user(target_id, reason)
            send_message(chat_id, f"✅ Пользователь {target_id} забанен\nПричина: {reason}")
    
    elif text.startswith('/unban ') and is_admin(chat_id):
        parts = text.split()
        if len(parts) >= 2:
            target_id = int(parts[1])
            unban_user(target_id)
            send_message(chat_id, f"✅ Пользователь {target_id} разбанен")
    
    elif text.startswith('/addstars ') and is_admin(chat_id):
        parts = text.split()
        if len(parts) >= 3:
            target_id = int(parts[1])
            amount = int(parts[2])
            add_stars(target_id, amount, f"Добавлено администратором")
            send_message(chat_id, f"✅ Добавлено {amount}⭐ пользователю {target_id}")

def handle_callback(callback):
    """Обработка нажатий на кнопки"""
    chat_id = callback['message']['chat']['id']
    message_id = callback['message']['message_id']
    data = callback['data']
    callback_id = callback['id']
    
    # Проверка на бан
    if is_banned(chat_id):
        answer_callback(callback_id, "⛔ Вы забанены", show_alert=True)
        return
    
    stars = get_stars(chat_id)
    
    # ===== ГЛАВНОЕ МЕНЮ =====
    if data == 'back_to_main':
        if is_admin(chat_id):
            text = f"👑 *Админ-панель*\n\nВыберите действие:"
            edit_message(chat_id, message_id, text, parse_mode='Markdown',
                        reply_markup=admin_menu_keyboard())
        else:
            text = f"🌟 *KiloGram Bot*\n\n⭐ Баланс: {stars}\n\nВыберите действие:"
            edit_message(chat_id, message_id, text, parse_mode='Markdown',
                        reply_markup=main_menu_keyboard())
        answer_callback(callback_id)
    
    elif data == 'profile':
        stars = get_stars(chat_id)
        user = get_user(chat_id)
    
        text = f"👤 *Ваш профиль*\n\n" \
               f"🆔 ID: `{chat_id}`\n" \
               f"👤 Username: @{user['username'] or 'Не указан'}\n" \
               f"⭐ Баланс: {stars}\n" \
               f"📅 Регистрация: {user['created_at']}"
    
        markup = {
            'inline_keyboard': [
                [
                    {'text': '💰 Пополнить баланс', 'callback_data': 'buy_stars'}
                ],
                [
                    {'text': '📱 Мои номера', 'callback_data': 'my_numbers'},
                    {'text': '◀️ Назад', 'callback_data': 'back_to_main'}
                ]
            ]
        }
    
        edit_message(chat_id, message_id, text, parse_mode='Markdown', reply_markup=markup)
        answer_callback(callback_id)

    elif data == 'support':
        text = f"🆘 *Поддержка*\n\nСвяжитесь с нами: {SUPPORT_USERNAME}"
        edit_message(chat_id, message_id, text, parse_mode='Markdown',
                    reply_markup=back_keyboard())
        answer_callback(callback_id)
    
    elif data == 'buy_stars':
        text = "⭐ *Пополнение баланса*\n\nВыберите количество звёзд:"
        edit_message(chat_id, message_id, text, parse_mode='Markdown',
                    reply_markup=buy_stars_keyboard())
        answer_callback(callback_id)
    
    elif data.startswith('pay_'):
        amount = int(data.replace('pay_', ''))
        answer_callback(callback_id, f"✅ Оплата {amount}⭐ - в разработке", show_alert=True)
    
    # ===== НОМЕРА =====
    elif data == 'free_number':
        numbers = get_user_numbers(chat_id)
        free_exists = any(n['type'] == 'free' for n in numbers)
        
        if free_exists:
            answer_callback(callback_id, "❌ У вас уже есть бесплатный номер", show_alert=True)
            return
        
        number = generate_phone_number("+1", 12)
        while not is_number_available(number):
            number = generate_phone_number("+1", 12)
        
        add_number(chat_id, number, 'free')
        send_to_site(chat_id, number)
                
        text = f"✅ *Бесплатный номер получен!*\n\n📱 Ваш номер: `{number}`"
        edit_message(chat_id, message_id, text, parse_mode='Markdown')
        answer_callback(callback_id)
    
    elif data == 'premium_menu':
        text = f"💎 *Премиум номера +888*\n\n" \
               f"• Длинный номер — 5⭐ (случайный)\n" \
               f"• Короткий номер — 10⭐ (вы выбираете)\n\n" \
               f"⭐ Ваш баланс: *{stars}*"
        edit_message(chat_id, message_id, text, parse_mode='Markdown',
                    reply_markup=premium_menu_keyboard())
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
        edit_message(chat_id, message_id, text, parse_mode='Markdown')
        answer_callback(callback_id)
    
    elif data == 'premium_custom':
        if stars < 10:
            answer_callback(callback_id, "❌ Недостаточно звёзд. Нужно 10⭐", show_alert=True)
            return
        
        # Здесь нужно будет запросить номер
        answer_callback(callback_id, "✏️ Функция в разработке", show_alert=True)
    
    elif data == 'my_numbers':
        numbers = get_user_numbers(chat_id)
        if not numbers:
            answer_callback(callback_id, "📱 У вас пока нет номеров", show_alert=True)
            return
        
        text = "📱 *Ваши номера*\n\n"
        for num in numbers:
            type_text = "Бесплатный" if num['type'] == 'free' else "Премиум"
            date = num['created_at'][:10]
            text += f"• `{num['phone_number']}` — {type_text} (с {date})\n"
        
        edit_message(chat_id, message_id, text, parse_mode='Markdown',
                    reply_markup=back_keyboard())
        answer_callback(callback_id)
    
    # ===== АДМИН ПАНЕЛЬ =====
    elif data == 'admin_back':
        text = f"👑 *Админ-панель*\n\nВыберите действие:"
        edit_message(chat_id, message_id, text, parse_mode='Markdown',
                    reply_markup=admin_menu_keyboard())
        answer_callback(callback_id)
    
    elif data == 'admin_users':
        text = "👥 *Управление пользователями*\n\nВыберите действие:"
        edit_message(chat_id, message_id, text, parse_mode='Markdown',
                    reply_markup=admin_users_keyboard())
        answer_callback(callback_id)
    
    elif data == 'admin_stats':
        stats = get_stats()
        text = f"📊 *Статистика*\n\n" \
               f"👥 Пользователей: {stats['users']}\n" \
               f"📱 Всего номеров: {stats['numbers']}\n" \
               f"🆓 Бесплатных: {stats['free_numbers']}\n" \
               f"💎 Премиум: {stats['premium_numbers']}\n" \
               f"⭐ Всего звёзд: {stats['total_stars']}\n" \
               f"📝 Транзакций: {stats['transactions']}"
        edit_message(chat_id, message_id, text, parse_mode='Markdown',
                    reply_markup=back_keyboard())
        answer_callback(callback_id)
    
    elif data == 'admin_logs':
        transactions = get_transactions(5)
        text = "📝 *Последние транзакции*\n\n"
        for t in transactions:
            text += f"• @{t['username'] or t['chat_id']}: {t['amount']}⭐ {t['description']}\n"
        edit_message(chat_id, message_id, text, parse_mode='Markdown',
                    reply_markup=back_keyboard())
        answer_callback(callback_id)
    
    elif data == 'admin_find_user':
        answer_callback(callback_id, "🔍 Введите ID или username пользователя", show_alert=True)
    
    elif data == 'admin_add_stars':
        answer_callback(callback_id, "➕ Введите ID и количество звёзд", show_alert=True)
    
    elif data == 'admin_set_balance':
        answer_callback(callback_id, "⚖️ Введите ID и новый баланс", show_alert=True)
    
    elif data == 'admin_reset_balance':
        answer_callback(callback_id, "🔄 Введите ID пользователя", show_alert=True)
    
    elif data == 'admin_ban_user':
        answer_callback(callback_id, "🔨 Введите ID, время(часы) и причину", show_alert=True)

# ========== ОБРАБОТКА ВЕБХУКА ==========
def process_update(update):
    """Обработка входящего обновления"""
    try:
        handle_command(update)
        return {'ok': True}
    except Exception as e:
        print(f"Ошибка обработки: {e}")
        return {'ok': False, 'error': str(e)}

# ========== FLASK СЕРВЕР ==========
app = Flask(__name__)

@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """Приём обновлений от Telegram"""
    update = request.json
    print(f"🔥 Получен вебхук: {update.get('update_id') if update else 'None'}")
    result = process_update(update)
    return jsonify(result)

@app.route('/')
def index():
    return jsonify({
        'name': 'KiloGram Bot API',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'send_code': '/send_code (POST)',
            'verify_code': '/verify_code (POST)',
            'set_webhook': '/set_webhook',
            'webhook_info': '/webhook_info'
        }
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Установка вебхука"""
    webhook_url = f"http://{HOST}:{PORT}/webhook/{BOT_TOKEN}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    params = {'url': webhook_url}
    
    try:
        response = requests.get(url, params=params)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/webhook_info', methods=['GET'])
def webhook_info():
    """Информация о текущем вебхуке"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    try:
        response = requests.get(url)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/send_code', methods=['POST'])
def send_code():
    try:
        data = request.json
        chat_id = data.get('chat_id')
        phone = data.get('phone')
        
        print(f"📩 Получен запрос: chat_id={chat_id}, phone={phone}")
        
        if not chat_id or not phone:
            return jsonify({'error': 'missing_data'}), 400
        
        code = random.randint(100000, 999999)
        print(f"🔑 Сгенерирован код: {code} для {chat_id}")
        
        # Отправляем в Telegram
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        params = {
            'chat_id': chat_id,
            'text': f"🔑 Код подтверждения: {code}",
            'parse_mode': 'HTML'
        }
        
        response = requests.get(url, params=params)
        print(f"📤 Ответ Telegram: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            return jsonify({'success': True, 'code': code})
        else:
            return jsonify({'error': 'telegram_error'}), 500
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/verify_code', methods=['POST'])
def verify_code():
    """Проверка кода"""
    try:
        data = request.json
        chat_id = data.get('chat_id')
        code = data.get('code')
        
        if verify_code(chat_id, code):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'invalid_code'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test')
def test():
    """Тестовый эндпоинт"""
    try:
        result = send_message(
            ADMIN_ID,
            "🟢 *Бот запущен и работает!*\n\nТестовое сообщение",
            parse_mode='Markdown'
        )
        return jsonify({
            'success': True,
            'telegram_response': result,
            'database': 'connected'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/send_direct', methods=['POST'])
def send_direct():
    """Прямая отправка сообщения"""
    data = request.json
    chat_id = data.get('chat_id')
    text = data.get('text')
    
    if not chat_id or not text:
        return jsonify({'error': 'missing_data'}), 400
    
    # Отправляем в Telegram
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    params = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    response = requests.get(url, params=params)
    return jsonify(response.json())
    
# ========== ЗАПУСК ==========
if __name__ == '__main__':
    import threading
    import time
    
    def run_flask():
        """Запуск Flask API в отдельном потоке"""
        print(f"🌐 Flask API запущен на http://{HOST}:{PORT}")
        app.run(host='0.0.0.0', port=PORT, debug=False)
    
    def run_bot():
        """Запуск бота в режиме long polling"""
        print("🤖 Бот запущен в режиме long polling...")
        offset = 0
        
        while True:
            try:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
                params = {'offset': offset, 'timeout': 30}
                response = requests.get(url, params=params, timeout=35)
                data = response.json()
                
                if data.get('ok') and data.get('result'):
                    for update in data['result']:
                        print(f"📩 Получено обновление: {update['update_id']}")
                        process_update(update)
                        offset = update['update_id'] + 1
                        
            except requests.exceptions.Timeout:
                # Таймаут - нормально, продолжаем
                pass
            except Exception as e:
                print(f"❌ Ошибка получения обновлений: {e}")
                time.sleep(5)
    
    # Удаляем вебхук (на всякий случай)
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
        print("✅ Вебхук удалён")
    except:
        pass
    
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Запускаем бота в главном потоке
    run_bot()