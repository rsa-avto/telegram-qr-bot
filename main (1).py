import os
from flask import Flask, request
import telebot
from telebot.types import Update
from flask import Flask, request
import html
import difflib
import re
import sqlite3
import telebot
from apscheduler.schedulers.background import BackgroundScheduler
import signal
import sys
import uuid
import time
from datetime import datetime, timedelta, date
from flask import Flask
from telebot import custom_filters
from threading import Thread
from types import SimpleNamespace
import time
import requests
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import qrcode
from types import SimpleNamespace
import locale
from io import BytesIO
import schedule
import urllib.parse
from urllib.parse import unquote

from aiofiles.os import remove

from geopy.distance import geodesic
from telebot.apihelper import ApiTelegramException
from telebot import types
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import threading
import calendar
from telebot.handler_backends import State, StatesGroup
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta, date
import threading  

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не задан")

WEBHOOK_URL = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
        bot.process_new_updates([update])
        return '', 200
    return 'Unsupported Media Type', 415

@app.route("/", methods=["GET"])
def index():
    return "Бот работает!", 200


ADMIN_ID = [5035760364]  # <-- ЗАМЕНИ на свой Telegram ID
ADMIN_ID2 = 5035760364
ADMIN_ID3 = 5035760364
DAN_ID = 5035760364
OFFICE_COORDS = (53.548713,49.292195)

PUBLIC_ID = 'cloudpayments-public-id'
API_KEY = 'cloudpayments-api-key'
DB_PATH = 'cars.db'
db_lock = threading.Lock()

bot.add_custom_filter(custom_filters.StateFilter(bot))

geolocator = Nominatim(user_agent="tolyatti_car_rental_bot", timeout=20)
booked_slots = {}
ADMIN_REPLY_STATE = {}
user_data = {}
repair_reject_reasons = {}
pending_replies = {}
temp_data = {}
selected_service = {}
USER_SELECTED_RENT_START = {}
user_sessions = {}
USER_SELECTED_RENT_END = {}
USER_DRIVER_CALL_SIGN = {}
USER_PHONE_NUMBER = {}
rent_start_dates = {}
selected_car_ids = {}
selected_dates = {}
USER_SELECTED_DATE = {}
selected_suggest = {}
repair_selected_suggest = {}
conn = sqlite3.connect('cars.db', check_same_thread=False)
cursor = conn.cursor()
user_car_messages = {}
session = {}
admin_reply_targets = {}
# --- БАЗА ДАННЫХ ---
def get_db_connection():
    conn = sqlite3.connect('cars.db', check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")  # Включить поддержку внешних ключей
    return conn


def get_db():
    return sqlite3.connect(DB_PATH)



def setup_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    #cursor.execute('DROP TABLE cars')
    #cursor.execute("ALTER TABLE users ADD COLUMN driver_license_photo TEXT;")
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT UNIQUE,
                name TEXT,
                birthday_date TEXT,
                telegram_id INTEGER UNIQUE,
                driver_license_photo TEXT, 
                status TEXT DEFAULT 'new',
                bonus INTEGER DEFAULT '0'
            )
        ''')

    cursor.execute('''
                CREATE TABLE IF NOT EXISTS bookings_taxi (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    job TEXT,
                    name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    status TEXT DEFAULT 'pending'
                )
            ''')
    cursor.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    "№" INTEGER PRIMARY KEY AUTOINCREMENT,
                    "Дата" DATETIME DEFAULT CURRENT_TIMESTAMP,
                    "Адрес" TEXT,
                    "Топливо" TEXT,
                    "Рубли" REAL,
                    "Литры" REAL,
                    "Оплата" TEXT,
                    "Telegram_ID" INTEGER
                )
            ''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS bookings
    (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
     user_id INTEGER NOT NULL, car_id TEXT,
      service TEXT DEFAULT 'rent',
       date TEXT NOT NULL, time TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
           notified INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id));''')

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS repair_bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                car_id INTEGER NOT NULL,
                service TEXT DEFAULT 'rent',
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT DEFAULT 'pending',   -- pending, confirmed, rejected
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notified INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (car_id) REFERENCES cars(car_id)
            )
        ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings_wash (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            car_id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_model TEXT,
            year INTEGER,
            transmission TEXT,
            service TEXT,
            number TEXT,
            photo_url TEXT,
            is_available INTEGER DEFAULT 1
        )
    ''')
    #cursor.execute("DROP TABLE IF EXISTS rental_history")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rental_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            car_id INTEGER NOT NULL,
            rent_start TEXT NOT NULL,
            rent_end TEXT NOT NULL,
            price REAL NOT NULL,
            delivery_price REAL,
            delivery_address TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (car_id) REFERENCES cars(car_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            question_text TEXT,
            answer_text TEXT,
            answered BOOLEAN
        )
    ''')
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                feedback_type TEXT NOT NULL,
                score INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    conn.commit()
    conn.close()

months = {
    '01': 'Январь', '02': 'Февраль', '03': 'Март',
    '04': 'Апрель', '05': 'Май', '06': 'Июнь',
    '07': 'Июль', '08': 'Август', '09': 'Сентябрь',
    '10': 'Октябрь', '11': 'Ноябрь', '12': 'Декабрь'
}
OPERATORS = {
    'station_1': 5035760364,
    'station_2': 5035760364,
    'station_3': 5035760364,
    'station_4': 5035760364
}

FUEL_PRICES = {
    'benzin': 60.0,
    'gaz': 25.0
}

STATION_NAMES = {
    'station_1': "Южное шоссе 129",
    'station_2': "Южное шоссе 12/2",
    'station_3': "Лесная 66А",
    'station_4': "Борковская 72/1"
}


def add_booking(user_id, car_id, service, date, time, status='pending'):
    cursor.execute('''
        INSERT INTO bookings (user_id, car_id, service, date, time, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, car_id, service, date, time, status))
    conn.commit()

def get_busy_slots(car_id, date, service):
    cursor.execute('''
        SELECT time FROM bookings
        WHERE car_id=? AND date=? AND service=? AND status='confirmed'
    ''', (car_id, date, service))
    return [row[0] for row in cursor.fetchall()]

#очистка заявок
def remove_expired_bookings():
    while True:
        try:
            now = datetime.now()
            current_date = now.strftime('%Y-%m-%d')
            current_time = now.strftime('%H:%M')

            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('''
                DELETE FROM bookings 
                WHERE 
                    (date < ?) 
                    OR (date = ? AND time <= ?)
            ''', (current_date, current_date, current_time))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[ERROR] Ошибка при удалении просроченных заявок: {e}")

        # Проверять каждые 5 минут
        time.sleep(300)

# --- РАБОТА С ПОЛЬЗОВАТЕЛЕМ ---
def check_user_in_db(phone_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE phone = ?", (phone_number,))
    user = cursor.fetchone()
    conn.close()
    return user is not None

user_states = {}
add_car_flow = {}
def get_state(user_id):
    return user_states.get(user_id)

def set_state(user_id, state):
    user_states[user_id] = state

def clear_state(user_id):
    user_states.pop(user_id, None)


def add_rental_history(user_id, car_id, rent_start, rent_end, price):
    try:
        connection = sqlite3.connect('cars.db')
        cursor = connection.cursor()

        # Вставляем запись в таблицу rental_history
        cursor.execute(''' 
        INSERT INTO rental_history (user_id, car_id, rent_start, rent_end, price)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, car_id, rent_start, rent_end, price))

        connection.commit()
        connection.close()
    except Exception as e:
        print(f"[ERROR] Ошибка при добавлении записи в историю аренды: {e}")

def get_rental_history(user_id):
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("SELECT car_id, rent_start, rent_end, price FROM rental_history WHERE user_id = ?", (user_id,))
    history = cursor.fetchall()
    conn.close()
    return history

def update_user_name(phone, name):
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET name = ? WHERE phone = ?', (name, phone))
    conn.commit()
    conn.close()

def get_session(chat_id):
    return user_sessions.setdefault(chat_id, {})

def set_state(chat_id, state):
    get_session(chat_id)["state"] = state

def get_state(chat_id):
    return get_session(chat_id).get("state")

def save_session(user_id, session):
    user_sessions[user_id] = session


def delete_user_from_db(phone_number):
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE phone = ?", (phone_number,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("SELECT phone, name, telegram_id FROM users")
    users = cursor.fetchall()  # список кортежей (phone, name)
    conn.close()
    return users


def get_booked_dates_and_times():
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("SELECT date, time FROM bookings")
    booked_dates_and_times = cursor.fetchall()
    conn.close()
    return booked_dates_and_times

def get_booked_dates_and_times():
    conn = sqlite3.connect('cars.db')
    c = conn.cursor()
    c.execute("SELECT date, time FROM bookings WHERE status IN ('pending', 'confirmed', 'suggested')")
    data = c.fetchall()
    conn.close()
    return data


def get_user_name_by_id(user_id):
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM users WHERE telegram_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def update_user_telegram_id(phone, telegram_id):
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()

    # Проверяем, есть ли пользователь с таким телефоном
    cursor.execute('SELECT id FROM users WHERE phone = ?', (phone,))
    user = cursor.fetchone()

    if user:
        cursor.execute('UPDATE users SET telegram_id = ? WHERE phone = ?', (telegram_id, phone))
    else:
        cursor.execute('INSERT INTO users (phone, telegram_id) VALUES (?, ?)', (phone, telegram_id))

    conn.commit()
    conn.close()

def send_time_selection(call):
    markup = InlineKeyboardMarkup(row_width=3)
    for hour in range(10, 19):  # 10:00 - 18:00
        time_str = f"{hour:02d}:00"
        markup.add(InlineKeyboardButton(time_str, callback_data=f"select_time:{time_str}"))

    markup.add(InlineKeyboardButton("📌 По усмотрению админа", callback_data="custom_datetime_time"))

    bot.send_message(call.message.chat.id, "⏰ Выберите время встречи:", reply_markup=markup)


def add_rental_history(user_id, car_id, rent_start, rent_end, price):
    try:
        connection = sqlite3.connect('cars.db')
        cursor = connection.cursor()

        # Вставляем запись в таблицу rental_history
        rent_end_str = rent_end.strftime("%Y-%m-%d")
        rent_start_str = rent_start.strftime("%Y-%m-%d")
        ...
        cursor.execute('''
            INSERT INTO rental_history (user_id, car_id, rent_start, rent_end, price)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, car_id, rent_start_str, rent_end_str, price))
        connection.commit()
        connection.close()
    except Exception as e:
        print(f"[ERROR] Ошибка при добавлении записи в историю аренды: {e}")

def get_rental_history(user_id):
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("SELECT car_id, rent_start, rent_end, price FROM rental_history WHERE user_id = ?", (user_id,))
    history = cursor.fetchall()
    conn.close()
    return history

def get_booked_dates_and_times():
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("SELECT date, time FROM bookings")
    booked_dates_and_times = cursor.fetchall()
    conn.close()
    return booked_dates_and_times

from telebot import types
from datetime import datetime, timedelta

MONTH_NAMES_RU_GEN = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря"
]

def create_calendar_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    today = datetime.today()
    calendar_buttons = []

    for i in range(30):
        day = today + timedelta(days=i)
        day_num = day.day
        month_name = MONTH_NAMES_RU_GEN[day.month - 1]
        button_text = f"{day_num} {month_name}"
        calendar_buttons.append(types.KeyboardButton(button_text))

    for i in range(0, len(calendar_buttons), 3):
        markup.row(*calendar_buttons[i:i + 3])

    return markup


def create_rent_end_markup(start_date_str: str):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=7)

    # Преобразуем строку в datetime
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    today = datetime.today()

    # Базовый день — либо сегодня, либо дата начала аренды (если она позже)
    base_day = max(today, start_date)

    calendar_buttons = []


def generate_year_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    years = [str(y) for y in range(2015, 2026)]
    for i in range(0, len(years), 3):
        markup.row(*years[i:i+3])
    return markup

def clear_keyboard():
    return types.ReplyKeyboardRemove()

# Проверка, что введено именно дата (формат "день месяц", например "21 May")
def is_valid_date(date_str):
    date_pattern = r'^\d{1,2} [A-Za-z]{3}$'  # Пример: 21 May
    return re.match(date_pattern, date_str) is not None
def create_calendar_markup_for_meet(include_custom_button=False):
    today = datetime.today()
    markup = InlineKeyboardMarkup(row_width=3)

    for i in range(7):
        day = today + timedelta(days=i)
        date_str = day.strftime("%d.%m.%Y")
        markup.add(InlineKeyboardButton(date_str, callback_data=f"select_date:{date_str}"))

    if include_custom_button:
        markup.add(InlineKeyboardButton("📌 По усмотрению админа", callback_data="custom_datetime"))

    return markup





def add_user_to_db(phone_number, telegram_id=None, name=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (phone, telegram_id, name) VALUES (?, ?, ?)", (phone_number, telegram_id, name))
        conn.commit()


ADMIN_STATE = {}
session = {}
@bot.message_handler(commands=['check_delivery'])
def check_delivery_command(message):
    if message.from_user.id != DAN_ID:
        bot.send_message(message.chat.id, "⛔ У вас нет доступа к этой команде.")
        return

    bot.send_message(message.chat.id, "💳 Введите сумму доставки, которую вы получили на карту:")
    ADMIN_STATE[message.chat.id] = 'waiting_for_delivery_amount'


@bot.message_handler(func=lambda message: ADMIN_STATE.get(message.chat.id) == 'waiting_for_delivery_amount')
def handle_delivery_amount(message):
    try:
        amount = float(message.text.strip())

        conn = sqlite3.connect('cars.db')
        cursor = conn.cursor()

        # Найдём запись, где delivery_price совпадает и доставка ещё не подтверждена
        cursor.execute('''
            SELECT id, user_id, delivery_price, delivery_address
            FROM rental_history
            WHERE delivery_price = ? 
        ''', (amount,))
        match = cursor.fetchone()

        if match:
            rental_id, user_id, delivery_price, address = match

            # Здесь можешь обновить статус — например, в rental_history или bookings (если есть поле status)
            # cursor.execute('UPDATE rental_history SET status = "paid_delivery" WHERE id = ?', (rental_id,))
            # cursor.execute('UPDATE bookings SET status = "paid_delivery" WHERE user_id = ? AND delivery_price = ?', (user_id, amount))

            conn.commit()
            conn.close()

            # Сообщение пользователю
            bot.send_message(user_id,
                f"✅ Мы получили оплату за доставку автомобиля ({delivery_price} ₽).\n"
                f"🚗 Машина будет доставлена по адресу: {address}\n"
                f"Спасибо за оплату!")

            bot.send_message(message.chat.id, f"✅ Успешно: пользователь {user_id} подтвердил доставку.")
        else:
            conn.close()
            bot.send_message(message.chat.id, "❌ Запись с такой суммой не найдена.")

    except ValueError:
        bot.send_message(message.chat.id, "⚠️ Пожалуйста, введите корректное число.")
    finally:
        ADMIN_STATE[message.chat.id] = None


@bot.message_handler(commands=['ask'])
def handle_ask_command(message):
    chat_id = message.chat.id

    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()

    # Получаем последние 5 вопросов с ответами
    cursor.execute('''
        SELECT id, question_text, answer_text 
        FROM questions 
        WHERE answered = 1 
        ORDER BY id DESC 
        LIMIT 5
    ''')
    questions = cursor.fetchall()
    conn.close()

    markup = types.InlineKeyboardMarkup()
    for q_id, q_text, answer in questions:
        short_text = q_text[:40] + "..." if len(q_text) > 40 else q_text
        markup.add(types.InlineKeyboardButton(short_text, callback_data=f"show_answer_{q_id}"))

    # Кнопка "Задать новый вопрос"
    markup.add(types.InlineKeyboardButton("✏ Задать новый вопрос", callback_data="ask_new"))

    bot.send_message(chat_id, "Выберите вопрос или задайте новый:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("show_answer_") or call.data == "ask_new")
def handle_ask_buttons(call):
    chat_id = call.message.chat.id

    if call.data == "ask_new":
        bot.send_message(chat_id, "✏ Введите ваш вопрос:")
        bot.register_next_step_handler(call.message, question_function)
        bot.answer_callback_query(call.id)
        return

    # Показываем ответ на выбранный вопрос
    question_id = int(call.data.replace("show_answer_", ""))
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("SELECT question_text, answer_text FROM questions WHERE id = ?", (question_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        question_text, answer_text = row
        bot.send_message(chat_id, f"*Вопрос:*\n_{question_text}_\n\n*Ответ:*\n{answer_text}", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "❌ Вопрос не найден.")

    bot.answer_callback_query(call.id)


def question_function(message):
    user_id = message.from_user.id
    username = message.from_user.username or 'пользователь'
    raw_text = message.text.strip()

    if raw_text.startswith('/'):
        return

    # Нормализация текста
    normalized_text = re.sub(r'\s+', ' ', raw_text).lower()
    normalized_text = re.sub(r'[^\w\s]', '', normalized_text)

    # Игнорировать слишком короткие и бессмысленные фразы
    if len(normalized_text) < 3:
        bot.send_message(user_id, "Пожалуйста, задайте более конкретный вопрос.")
        return

    # Проверка на схожесть
    cursor.execute("SELECT id, user_id, question_text, answer_text, answered FROM questions")
    all_questions = cursor.fetchall()

    threshold = 0.7
    for q_id, q_user_id, q_text, q_answer, q_answered in all_questions:
        q_norm = re.sub(r'\s+', ' ', q_text.lower())
        q_norm = re.sub(r'[^\w\s]', '', q_norm)
        similarity = difflib.SequenceMatcher(None, normalized_text, q_norm).ratio()

        if similarity >= threshold:
            if q_answer and str(q_answer).strip():
                bot.send_message(user_id, f"✉ Похожий вопрос уже был, вот ответ:\n\n{q_answer}")
            else:
                bot.send_message(user_id, "Похожий вопрос уже был, но на него пока нет ответа. Пожалуйста, подождите.")
            return  # Ничего не сохраняем и не отправляем админу

    # Новый вопрос — сохраняем и отправляем админу
    cursor.execute('''
        INSERT INTO questions (user_id, username, question_text, answer_text, answered)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, raw_text, None, False))
    question_id = cursor.lastrowid
    conn.commit()

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Ответить", callback_data=f"answer_{question_id}_{user_id}"))

    bot.send_message(
        ADMIN_ID[0],
        f"❓ Новый вопрос от @{username} (ID: {user_id}):\n{raw_text}",
        reply_markup=markup
    )

    bot.send_message(user_id, "Ваш вопрос отправлен администратору. Ожидайте ответа.")
@bot.callback_query_handler(func=lambda call: call.data.startswith("answer_"))
def handle_answer_callback(call):
    if call.from_user.id not in ADMIN_ID:
        bot.answer_callback_query(call.id, "У вас нет доступа")
        return

    _, question_id, user_id = call.data.split("_")
    question_id, user_id = int(question_id), int(user_id)



    msg = bot.send_message(call.from_user.id, f"Введите ответ на вопрос #{question_id}:")
    bot.register_next_step_handler(msg, process_admin_answer, question_id, user_id)

# --- Обработка ответа от админа ---
def process_admin_answer(message, question_id, user_id):
    answer = message.text

    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()

    # Обновляем ответ
    cursor.execute("UPDATE questions SET answer_text = ?, answered = ? WHERE id = ?", (answer, True, question_id))
    conn.commit()

    # Получаем текст вопроса
    cursor.execute("SELECT question_text FROM questions WHERE id = ?", (question_id,))
    row = cursor.fetchone()
    question_text = row[0] if row else "неизвестный вопрос"

    conn.close()

    try:
        bot.send_message(
            user_id,
            f"✉ Ответ администратора на вопрос:\n*{question_text}*\n\n{answer}",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.send_message(message.chat.id, "Ответ отправлен пользователю.")


@bot.message_handler(commands=['list_cars'])
def list_all_cars(message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT car_id, brand_model, year, transmission, service, photo_url, is_available FROM cars")
    cars = cursor.fetchall()
    conn.close()

    if not cars:
        bot.send_message(message.chat.id, "Машин пока нет.")
    else:
        msg = "🚘 Все автомобили:\n"
        for c in cars:
            status = "Свободна" if c[6] else "Занята"
            msg += f"{c[0]}. {c[1]} {c[2]} {c[3]} {c[4]} — {status}\n\n\n"
        bot.send_message(message.chat.id, msg)


MONTHS_RU_GEN = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
    "мая": 5, "июня": 6, "июля": 7, "августа": 8,
    "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12
}

def parse_russian_date(text):
    try:
        parts = text.strip().split()
        if len(parts) != 2:
            return None

        day = int(parts[0])
        month_name = parts[1].lower()

        month = MONTHS_RU_GEN.get(month_name)
        if not month:
            return None

        year = datetime.today().year
        return datetime(year, month, day)
    except:
        return None


@bot.message_handler(func=lambda message: get_state(message.chat.id) == "waiting_for_rental_start")
def handle_date_selection(message):
    user_id = message.chat.id
    session = get_session(user_id)
    rent_start_raw = message.text.strip()

    car_id = session.get("car_id") or session.get("selected_car_id")
    if not car_id:
        bot.send_message(user_id, "Ошибка: автомобиль не выбран. Пожалуйста, выберите автомобиль.")
        return

    parsed_date = parse_russian_date(rent_start_raw)
    if not parsed_date:
        bot.send_message(user_id, "❌ Неверный формат даты. Пожалуйста, выберите дату, используя кнопки календаря.")
        return

    selected_rent_start = parsed_date.strftime('%Y-%m-%d')
    session["rent_start"] = selected_rent_start
    session["car_id"] = car_id
    set_state(user_id, "waiting_for_rent_end")

    bot.send_message(
        user_id,
        f"✅ Вы выбрали дату начала: {selected_rent_start}. Теперь выберите дату завершения:",
        reply_markup=create_rent_end_markup(selected_rent_start)
    )


@bot.message_handler(func=lambda message: get_state(message.chat.id) == "waiting_for_rent_end")
def handle_rent_end_date(message):
    from datetime import datetime
    import sqlite3

    user_id = message.chat.id
    session = get_session(user_id)

    end_date_str = message.text.strip()
    start_date_str = session.get("rent_start")
    car_id = session.get("car_id")

    if not start_date_str or not car_id:
        bot.send_message(user_id, "❌ Ошибка: не выбрана дата начала или автомобиль.")
        return

    parsed_end = parse_russian_date(end_date_str)
    if not parsed_end:
        bot.send_message(user_id, "❌ Неверный формат даты. Пожалуйста, выберите дату, используя кнопки календаря.")
        return

    try:
        rent_start = datetime.strptime(start_date_str, "%Y-%m-%d")
        rent_end = parsed_end.replace(year=rent_start.year)

        days = (rent_end - rent_start).days
        if days <= 0:
            bot.send_message(user_id, "⛔ Дата окончания должна быть позже даты начала.")
            return

        rent_start_str = rent_start.strftime("%Y-%m-%d")
        rent_end_str = rent_end.strftime("%Y-%m-%d")


        # TODO: расчёт стоимости на основе TARIFFS

    except Exception as e:
        bot.send_message(user_id, f"❌ Ошибка при обработке даты: {e}")

    TARIFFS = {
        "Аренда": {
            "Рено Логан": {2017: 1700, 2018: 1750, 2019: 1800, 2020: 1900, 2021: 1950},
            "Фольцваген Поло": {2018: 2100, 2019: 2200},
            "Шкода Рапид": {2016: 2000, 2018: 2100},
            "Шкода Октавия": {2017: 2900, 2019: 2900, 2020: 3100},
            "Джили Эмгранд": {2023: 2900}
        },
        "Прокат": {
            "Рено Логан": {1: 2400, 7: 2300, 14: 2200, 30: 2100},
            "Джили Эмгранд": {1: 3400, 7: 3300, 14: 3200, 30: 3100}
        }
    }

    def calculate_price(model, year, days, service):
        service_lower = service.lower()
        if service_lower in ["аренда", "rental"]:
            price_per_day = TARIFFS.get("Аренда", {}).get(model, {}).get(year)
            if not price_per_day:
                price_per_day = 2000
            return price_per_day * days

        elif service_lower in ["прокат", "rental service"]:
            tariffs = TARIFFS.get("Прокат", {}).get(model)
            if not tariffs:
                return 0
            valid_keys = [k for k in tariffs if k <= days]
            max_key = max(valid_keys) if valid_keys else min(tariffs)
            base_price = tariffs[max_key]
            return int(base_price * days / max_key)

        return 0

    # Получаем данные авто
    with sqlite3.connect("cars.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT brand_model, year, service FROM cars WHERE car_id = ?", (car_id,))
        car = cursor.fetchone()

    if not car:
        bot.send_message(user_id, "❌ Автомобиль не найден.")
        return

    model, year, service = car

    # Приведение сервиса к русскому виду
    service = {
        "rental": "Аренда",
        "rental service": "Прокат"
    }.get(service.lower(), service)

    price = calculate_price(model, year, days, service)
    print(rent_end_str, rent_start_str, days, price, model, year, service, user_id)
    # Сохраняем все важные данные в сессию
    session["rent_end"] = rent_end_str
    session["rent_start"] = rent_start_str
    session["days"] = days
    session["price"] = price
    session["car_model"] = model
    session["car_year"] = year
    session["service"] = service
    session["db_user_id"] = user_id

    # Показываем пользователю информацию и запрашиваем подтверждение
    bot.send_message(
        user_id,
        f"✅ Вы арендовали {model} ({year}) с {rent_start_str} по {rent_end_str}.\n"
        f"📅 Дней: {days}\n💰 Стоимость: {price} ₽",
        reply_markup=clear_keyboard()
    )

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Да", "Нет")
    bot.send_message(user_id, "Все верно?", reply_markup=markup)

    set_state(user_id, "waiting_for_delivery_choice")
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, status FROM users WHERE telegram_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        name, status = result

        if status == 'awaiting_use':
            start_use_kb = types.InlineKeyboardMarkup()
            start_use_kb.add(types.InlineKeyboardButton("🚀 Начать использование машины", callback_data="start_use"))
            bot.send_message(message.chat.id,
                             f"Привет, {name}! Готовы начать использование автомобиля?",
                             reply_markup=start_use_kb)

        elif status == 'using_car':
            show_main_menu(message.chat.id)

        else:
            name = result[0]
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🏠 Смотреть квартиры Тольятти", url="https://homereserve.ru/AACykQ"))
            markup.add(InlineKeyboardButton("🚗 Машины Элит", callback_data="elite_cars"))
            bot.send_message(message.chat.id, "Привет! Выберите действие:", reply_markup=markup)

            # Здесь можно показать главное меню
            return

    else:
        bot.send_message(
            user_id,
            "👋 <b>Добро пожаловать в официальный бот компании ЭЛИТ!</b>\n\n"
            "🚗 Здесь ты можешь арендовать авто и квартиру, заказать такси и многое другое.\n\n"
            "Для начала давай познакомимся.\n\n"
            "Как тебя зовут? 😊",
            parse_mode='HTML'
        )
        bot.register_next_step_handler(message, get_name)




def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'name': message.text.strip()}
    bot.send_message(chat_id, "А теперь введи свою фамилию, чтобы я мог получше тебя узнать:")
    bot.register_next_step_handler(message, get_surname)

def get_surname(message):
    chat_id = message.chat.id
    user_data[chat_id]['surname'] = message.text.strip()

    markup = types.InlineKeyboardMarkup(row_width=3)
    for code, name in months.items():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"month_{code}"))
    bot.send_message(chat_id, "📅 Выбери месяц своего рождения:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("month_"))
def select_month(call):
    month = call.data.split("_")[1]
    chat_id = call.message.chat.id

    if chat_id not in user_data:
        bot.send_message(chat_id, "❗ Данные не найдены. Пожалуйста, начни сначала: /start")
        return

    user_data[chat_id]['birth_month'] = month

    markup = types.InlineKeyboardMarkup(row_width=7)
    row = []

    for day in range(1, 32):
        day_str = f"{day:02}"
        button = types.InlineKeyboardButton(day_str, callback_data=f"day_{day_str}")
        row.append(button)
        if len(row) == 7:
            markup.row(*row)
            row = []

    if row:
        markup.row(*row)

    bot.edit_message_text("📆 А теперь выбери день:",
                          chat_id,
                          call.message.message_id,
                          reply_markup=markup)
@bot.callback_query_handler(func=lambda call: call.data.startswith("day_"))
def select_day(call):
    day = call.data.split("_")[1]
    user_data[call.message.chat.id]['birth_day'] = day

    current_year = datetime.now().year
    markup = types.InlineKeyboardMarkup(row_width=5)
    for year in range(1950, current_year + 1):  # от 1901 до текущего года (включительно)
        markup.add(types.InlineKeyboardButton(str(year), callback_data=f"year_{year}"))
    bot.edit_message_text("📅 И наконец — выбери год рождения:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("year_"))
def select_year(call):
    year = call.data.split("_")[1]
    chat_id = call.message.chat.id
    user_data[chat_id]['birth_year'] = year

    name = user_data[chat_id]['name']
    surname = user_data[chat_id]['surname']
    b_day = user_data[chat_id]['birth_day']
    b_month = user_data[chat_id]['birth_month']
    b_year = user_data[chat_id]['birth_year']

    text = (f"🎉 Спасибо, <b>{name} {surname}</b>!\n"
            f"🎂 Мы запомнили твою дату рождения: <b>{b_day}.{b_month}.{b_year}</b>\n\n"
            "Всё верно?")

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Да ✅", callback_data="confirm_yes"),
        types.InlineKeyboardButton("Нет ❌", callback_data="confirm_no")
    )

    bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def confirm_handler(call):
    chat_id = call.message.chat.id

    if call.data == "confirm_yes":
        # Запрос номера телефона
        contact_markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        contact_button = types.KeyboardButton(text="Отправить номер телефона", request_contact=True)
        contact_markup.add(contact_button)
        bot.edit_message_text("Пожалуйста, поделись своим номером телефона для связи:", chat_id, call.message.message_id)
        bot.send_message(chat_id, "Нажми кнопку ниже, чтобы отправить номер телефона:", reply_markup=contact_markup)

    elif call.data == "confirm_no":
        # Начинаем заново (можно только имя или всё)
        bot.edit_message_text("Давай попробуем ещё раз.\nКак тебя зовут?", chat_id, call.message.message_id)
        bot.register_next_step_handler_by_chat_id(chat_id, get_name)
@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    chat_id = message.chat.id
    phone = message.contact.phone_number

    if chat_id not in user_data:
        bot.send_message(chat_id, "❗ Произошла ошибка: данные не найдены. Пожалуйста, начни сначала /start")
        return

    name = user_data[chat_id]['name']
    surname = user_data[chat_id]['surname']
    b_day = int(user_data[chat_id]['birth_day'])
    b_month = int(user_data[chat_id]['birth_month'])
    b_year = int(user_data[chat_id]['birth_year'])

    birth_date = datetime(b_year, b_month, b_day)
    birth_date_str = birth_date.strftime('%Y-%m-%d')  # формат для хранения в базе
    print(birth_date_str)
    age = (datetime.now() - birth_date).days // 365  # простой расчет возраста в годах
    if age < 18:
        bot.send_message(chat_id, "🚫 Извините, наш сервис доступен только пользователям старше 18 лет.")
        return

    user_data[chat_id]['phone'] = phone

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Вставляем или игнорируем пользователя (чтобы гарантировать наличие записи)
        cursor.execute('''
            INSERT OR IGNORE INTO users (telegram_id, name, phone, status)
            VALUES (?, ?, ?, ?)
        ''', (chat_id, f"{name} {surname}", phone, 'new'))

        # Обновляем дату рождения (обновит только если запись есть)
        cursor.execute('''
            UPDATE users
            SET birthday_date = ?
            WHERE telegram_id = ?
        ''', (birth_date_str, chat_id))

        conn.commit()
    except Exception as e:
        bot.send_message(chat_id, f"❗ Ошибка при сохранении данных: {e}")
        return
    finally:
        conn.close()


    bot.send_message(
        chat_id,
        f"📱 Спасибо за номер, <b>{name} {surname}</b>!\n"
        f"Мы тебя запомнили: ДР {b_day}.{b_month}.{b_year}, Телефон: {phone}\n\n"
        "Теперь ты готов пользоваться нашим сервисом — выбирай! 🚗",
        parse_mode='HTML',
        reply_markup=types.ReplyKeyboardRemove()
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🏠 Смотреть квартиры Тольятти", url="https://yandex.ru/maps?whatshere%5Bpoint%5D=49.258310120938255%2C53.55394002594526&whatshere%5Bzoom%5D=12.109293&ll=49.25831012019384%2C53.553940026040266&z=12.109293&si=9w1gtgppfvdjfudny44z6dr2km"))
    markup.add(InlineKeyboardButton("🚗 Машины Элит", callback_data="elite_cars"))
    bot.send_message(chat_id, "Привет! Выберите действие:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "elite_cars")
def handle_elite_menu(call):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🚕 Заказать такси", callback_data="taxi"))
    markup.add(InlineKeyboardButton("🏎 Аренда/Прокат", callback_data="rent"))
    markup.add(InlineKeyboardButton("⛽ Заправки", callback_data="gas"))
    markup.add(InlineKeyboardButton("🔧 Ремонт авто", callback_data="rext"))
    markup.add(InlineKeyboardButton("💼 Вакансии", callback_data="jobs"))
    markup.add(InlineKeyboardButton("ℹ️ О нас", callback_data="about"))


    bot.send_message(call.message.chat.id, "Выберите категорию Машины Элит:", reply_markup=markup)


@bot.message_handler(commands=['clear_all_user'])
def clear_all_users(message):
    admin_id = message.from_user.id

    if admin_id != ADMIN_ID2:
        bot.send_message(message.chat.id, "❌ У вас нет прав для этой команды.")
        return

    try:
        conn = sqlite3.connect('cars.db')
        cursor = conn.cursor()

        # Удаляем все бронирования, связанные с пользователями
        cursor.execute("""
            DELETE FROM bookings 
            WHERE user_id IN (SELECT id FROM users WHERE telegram_id != ?)
        """, (admin_id,))

        # Удаляем всех пользователей, кроме администратора
        cursor.execute("DELETE FROM users WHERE telegram_id != ?", (admin_id,))

        conn.commit()
        conn.close()

        bot.send_message(message.chat.id, "✅ Все пользователи (кроме администратора) и их бронирования удалены.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при удалении пользователей: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "gas")
def handle_gas(call):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎁 Баллы", callback_data="fuel_bonuses"))
    markup.add(InlineKeyboardButton("📍 Точки", callback_data="fuel_locations"))
    markup.add(InlineKeyboardButton("⛽️ Заправиться", callback_data="fuel_get"))
    bot.send_message(call.message.chat.id, "Выберите категорию Машины Элит:", reply_markup=markup)

def reset_state(chat_id):
    user_sessions[chat_id] = {
        "station": None,
        "column": None,
        "fuel": None,
        "amount_type": None,
        "amount": None,
        "payment_method": None
    }
@bot.callback_query_handler(func=lambda call: call.data.startswith("fuel_"))
def handle_fuel(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    data = call.data.replace("fuel_", "")

    # Убедимся, что сессия существует
    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}

    conn = get_db_connection()
    cursor = conn.cursor()

    if data == "locations":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Южное шоссе 129 газ/бензин",
                                        url="https://yandex.ru/maps?whatshere%5Bpoint%5D=49.258310120938255%2C53.55394002594526&whatshere%5Bzoom%5D=12.109293&ll=49.25831012019384%2C53.553940026040266&z=12.109293&si=9w1gtgppfvdjfudny44z6dr2km"))
        markup.add(InlineKeyboardButton("Южное шоссе 12/2 газ/бензин",
                                        url="https://yandex.ru/maps?whatshere%5Bpoint%5D=49.320123195638516%2C53.552624083421854&whatshere%5Bzoom%5D=19.115421&ll=49.32012319563051%2C53.552624082637955&z=19.115421&si=9w1gtgppfvdjfudny44z6dr2km"))
        markup.add(InlineKeyboardButton("Лесная 66А газ",
                                        url="https://yandex.ru/maps?whatshere%5Bpoint%5D=49.39527625230795%2C53.520279635182185&whatshere%5Bzoom%5D=19.115421&ll=49.39527625230796%2C53.520279634790576&z=19.115421&si=9w1gtgppfvdjfudny44z6dr2km"))
        markup.add(InlineKeyboardButton("Борковская 72/1 газ",
                                        url="https://yandex.ru/maps?whatshere%5Bpoint%5D=49.283085%2C53.550687&whatshere%5Bzoom%5D=17.681623&ll=49.283085%2C53.550686999608416&z=17.681623&si=9w1gtgppfvdjfudny44z6dr2km"))
        bot.send_message(call.message.chat.id, "Вот где ты можешь заправиться", reply_markup=markup)


    elif data == "bonuses":
        cursor.execute("SELECT bonus FROM users WHERE telegram_id = ?", (user_id,))
        result = cursor.fetchone()
        if result:
            bonus = result[0]
            count = int(bonus) % 10
            word = "баллов" if count in [0, 5, 6, 7, 8, 9] else "балл" if count == 1 else "балла"
            bot.send_message(chat_id, f"У вас {bonus} {word}")
        else:
            bot.send_message(chat_id, "❌ Не удалось получить информацию о баллах.")

    elif data == "get":
        reset_state(chat_id)
        markup = InlineKeyboardMarkup()
        markup.add(
            #InlineKeyboardButton("📷 Сканировать QR", callback_data="start_scan"),
            InlineKeyboardButton("📍 Выбрать адрес", callback_data="choose_address")
        )
        bot.send_message(chat_id, "Для начала нужен адрес", reply_markup=markup)

    elif data == "qr":
        cursor.execute("SELECT phone FROM users WHERE telegram_id = ?", (user_id,))
        result = cursor.fetchone()
        if result:
            phone = result[0]
            qr_image = generate_qr_code(phone)
            bot.send_photo(chat_id, qr_image, caption=f"Ваш QR-код по номеру: {phone}")
        else:
            bot.send_message(chat_id, "❌ Не удалось найти ваш номер.")

    elif data in ["benzin", "gaz"]:
        user_sessions[chat_id]['fuel'] = data
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("₽ Рубли", callback_data="amount_rub"),
            InlineKeyboardButton("Литры", callback_data="amount_litres")
        )
        bot.edit_message_text("Введите сумму в рублях или литрах:", chat_id, call.message.message_id, reply_markup=markup)

    cursor.close()
    conn.close()
    bot.answer_callback_query(call.id)

def generate_qr_code(data: str) -> BytesIO:
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    bio.name = 'qr.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

def delete_last_message(chat_id):
    message_id = user_sessions.get(chat_id, {}).get('last_message_id')
    if message_id:
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as e:
            print(f"[Удаление] Ошибка удаления сообщения {message_id}: {e}")


@bot.callback_query_handler(func=lambda call: call.data in ["start_scan", "choose_address"])
def handle_start_choice(call):
    chat_id = call.message.chat.id
    delete_last_message(chat_id)

    if call.data == "start_scan":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📷 Сканировать QR",
                                        web_app=WebAppInfo(url="https://doctor-eggman444.github.io/qr-scanner/")))
        msg = bot.send_message(chat_id, "Нажмите кнопку и отсканируйте QR-код на заправке:", reply_markup=markup)

    elif call.data == "choose_address":
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("Южное шоссе 129", callback_data="station_1"),
            InlineKeyboardButton("Южное шоссе 12/2", callback_data="station_2"),
            InlineKeyboardButton("Лесная 66А", callback_data="station_3"),
            InlineKeyboardButton("Борковская 72/1", callback_data="station_4")
        )
        msg = bot.send_message(chat_id, "Выберите адрес:", reply_markup=markup)

    user_sessions[chat_id] = user_sessions.get(chat_id, {})
    user_sessions[chat_id]['last_message_id'] = call.message.message_id

@bot.message_handler(content_types=["web_app_data"])
def handle_qr(message):
    station_id = message.web_app_data.data
    chat_id = message.chat.id

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM stations WHERE station_id = ?", (station_id,))
    station = cursor.fetchone()

    if not station:
        bot.send_message(chat_id, "❌ Станция не найдена.")
        return

    amount = 100.00
    invoice_id = f"{chat_id}_{int(time.time())}"

    payment_data = {
        "Amount": amount,
        "Currency": "RUB",
        "InvoiceId": invoice_id,
        "Description": f"Оплата на станции {station[0]}",
        "AccountId": str(chat_id),
        "JsonData": {
            "telegram_id": chat_id,
            "station_id": station_id
        }
    }

    r = requests.post(
        "https://api.cloudpayments.ru/payments/checkout",
        auth=(PUBLIC_ID, API_KEY),
        json=payment_data
    )

    if r.status_code != 200:
        bot.send_message(chat_id, "🚫 Ошибка создания оплаты. Попробуйте позже.")
        return

    url = r.json().get("Model", {}).get("Url", "")
    if not url:
        bot.send_message(chat_id, "🚫 Не удалось получить ссылку.")
        return

    cursor.execute('''
        INSERT INTO transactions (telegram_id, station_id, amount, status, payment_url, invoice_id)
        VALUES (?, ?, ?, 'pending', ?, ?)
    ''', (chat_id, station_id, amount, url, invoice_id))
    conn.commit()
    conn.close()

    bot.send_message(chat_id, f"⛽️ Станция: {station[0]}\n💳 Оплата: {amount:.2f} ₽\n🔗 Ссылка на оплату:\n{url}")




@bot.callback_query_handler(func=lambda call: isinstance(call.data, str) and call.data.startswith(
    ("station_", "column_", "accepted_", "amount_", "pay_", "confirm", "cancel")
))
def callback_handler(call):
    chat_id = call.message.chat.id
    data = call.data

    # Убедимся, что сессия для пользователя существует
    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}

    # === Выбор станции ===
    if data.startswith("station_"):
        user_sessions[chat_id]['station'] = data

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("1", callback_data="column_1"),
            InlineKeyboardButton("2", callback_data="column_2")
        )
        bot.edit_message_text("Выберите колонку:", chat_id, call.message.message_id, reply_markup=markup)

    # === Выбор колонки ===
    elif data.startswith("column_"):
        user_sessions[chat_id]['column'] = data.split("_")[1]
        station_code = user_sessions[chat_id].get('station')

        if station_code in ["station_3", "station_4"]:
            user_sessions[chat_id]['fuel'] = 'gaz'  # Газ по умолчанию

            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("₽ Рубли", callback_data="amount_rub"),
                InlineKeyboardButton("Литры", callback_data="amount_litres")
            )
            bot.edit_message_text("На этой станции доступен только газ.\nВыберите способ ввода:", chat_id, call.message.message_id, reply_markup=markup)
        else:
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("Бензин", callback_data="fuel_benzin"),
                InlineKeyboardButton("Газ", callback_data="fuel_gaz")
            )
            bot.edit_message_text("Выберите тип топлива:", chat_id, call.message.message_id, reply_markup=markup)

    # === Подтверждение заказа админом ===
    elif data.startswith("accepted_"):
        client_chat_id = int(data.split("_")[1])
        session = user_sessions.get(client_chat_id)
        litres = session.get('litres', 0) if session else 0

        earned, total = add_bonus(client_chat_id, litres)

        if earned > 0:
            bot.send_message(client_chat_id, f"🎁 Вам начислено {earned} баллов!\n💰 Всего у вас: {total} баллов.")
        else:
            bot.send_message(client_chat_id, f"ℹ️ Баллы не начислены (литры: {litres}).")

        bot.send_message(call.message.chat.id, "✅ Заказ подтверждён и сохранён в системе.")
    elif data in ["amount_rub", "amount_litres"]:
        user_sessions[chat_id]['amount_type'] = 'rub' if data == 'amount_rub' else 'litres'
        bot.send_message(chat_id, "Введите значение:")

    # === Выбор способа оплаты ===
    elif data in ["pay_cash", "pay_card"]:
        user_sessions[chat_id]['payment_method'] = 'cash' if data == 'pay_cash' else 'card'
        finalize_order(chat_id)

    # === Подтверждение заказа перед оплатой ===
    elif data == "confirm":
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("💵 Наличные", callback_data="pay_cash"),
            InlineKeyboardButton("💳 Безнал (Tinkoff)", callback_data="pay_card")
        )
        bot.send_message(chat_id, "Выберите способ оплаты:", reply_markup=markup)

    # === Отмена заказа ===
    elif data == "cancel":
        reset_state(chat_id)
        bot.send_message(chat_id, "❌ Операция отменена.")
        choose_address_menu(chat_id)

def choose_address_menu(chat_id):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Южное шоссе 129", callback_data="station_1"),
        InlineKeyboardButton("Южное шоссе 12/2", callback_data="station_2"),
        InlineKeyboardButton("Лесная 66А", callback_data="station_3"),
        InlineKeyboardButton("Борковская 72/1", callback_data="station_4")
    )
    bot.send_message(chat_id, "📍 Выберите адрес:", reply_markup=markup)
@bot.message_handler(func=lambda m: (
    m.chat.id in user_sessions and
    user_sessions[m.chat.id].get('amount_type') and
    user_sessions[m.chat.id].get('amount') is None
))
def amount_input_handler(msg):
    chat_id = msg.chat.id

    try:
        amount = float(msg.text.replace(',', '.'))
        user_sessions[chat_id]['amount'] = amount
    except ValueError:
        bot.send_message(chat_id, "❌ Введите корректное число")
        return

    # Удаляем старое сообщение от бота, если было
    last_msg_id = user_sessions[chat_id].get("last_bot_msg_id")
    if last_msg_id:
        try:
            bot.delete_message(chat_id, last_msg_id)
        except Exception as e:
            print(f"[!] Не удалось удалить сообщение: {e}")

    data = user_sessions[chat_id]
    fuel_name = 'Бензин' if data['fuel'] == 'benzin' else 'Газ'
    price = FUEL_PRICES[data['fuel']]

    if data['amount_type'] == 'rub':
        litres = round(amount / price, 2)
        rub = amount
    else:
        litres = amount
        rub = round(amount * price, 2)
    user_sessions[chat_id]['litres'] = litres

    confirm_text = (f"🧾 Проверьте данные:\n"
                    f"Станция: {STATION_NAMES.get(data['station'], 'Неизвестно')}\n"
                    f"Колонка: {data['column']}\n"
                    f"Топливо: {fuel_name}\n"
                    f"Объём: {litres} л\n"
                    f"Сумма: {rub:.2f} ₽")

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Верно", callback_data="confirm"),
        InlineKeyboardButton("❌ Отмена", callback_data="cancel")
    )
    # ⬇️ Сохраняем ID отправленного ботом сообщения
    sent = bot.send_message(chat_id, confirm_text, reply_markup=markup)
    user_sessions[chat_id]['last_bot_msg_id'] = sent.message_id

def finalize_order(chat_id):
    data = user_sessions[chat_id]
    required_fields = ['station', 'column', 'fuel', 'amount_type', 'amount', 'payment_method']
    missing = [field for field in required_fields if data.get(field) is None]
    if missing:
        bot.send_message(chat_id, f"❌ Не хватает данных: {', '.join(missing)}. Попробуйте заново.")
        reset_state(chat_id)
        return

    fuel_name = 'Бензин' if data['fuel'] == 'benzin' else 'Газ'
    price = FUEL_PRICES[data['fuel']]

    if data['amount_type'] == 'rub':
        litres = round(data['amount'] / price, 2)
        rub = data['amount']
    else:
        litres = data['amount']
        rub = round(data['amount'] * price, 2)

    station_code = data['station']
    station_name = STATION_NAMES.get(station_code, "Неизвестно")
    operator_id = OPERATORS.get(station_code)

    # Сохраняем данные в сессии клиента (chat_id)
    user_sessions[chat_id].update({
        'rub': rub,
        'litres': litres,
        'station_name': station_name,
        'fuel_name': fuel_name,
    })

    message = (f"🧾 Новый заказ\n"
               f"Станция: {station_name}\n"
               f"Колонка: {data['column']}\n"
               f"Топливо: {fuel_name}\n"
               f"Объем: {litres} л\n"
               f"Сумма: {rub:.2f} ₽\n"
               f"Оплата: {'💵 Наличные' if data['payment_method'] == 'cash' else '💳 Безнал'}")

    if data['payment_method'] == 'cash':
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Принял", callback_data=f"accepted_{chat_id}"))
        bot.send_message(operator_id, message, reply_markup=markup)
        bot.send_message(chat_id, "✅ Отлично! Подойдите и оплатите свой заказ.")
    else:
        bot.send_message(chat_id, f"💳 Ссылка на оплату (заглушка): https://pay.tinkoff.ru")
        bot.send_message(operator_id, message)
        save_to_db(chat_id)  # Для безнала — сохраняем сразу


def add_bonus(chat_id, litres):
    import sqlite3
    conn = sqlite3.connect("cars.db")
    cursor = conn.cursor()

    cursor.execute("SELECT bonus FROM users WHERE telegram_id = ?", (chat_id,))
    result = cursor.fetchone()
    current_bonus = int(result[0]) if result and result[0] else 0

    try:
        earned = int(litres)
        new_bonus = current_bonus + earned
        cursor.execute("UPDATE users SET bonus = ? WHERE telegram_id = ?", (new_bonus, chat_id))
        conn.commit()
        return earned, new_bonus  # Возвращаем начисленные и итого
    except Exception as e:
        print("Ошибка при начислении бонусов:", e)
        return 0, current_bonus
    finally:
        conn.close()

price_change_sessions = {}

@bot.message_handler(commands=['setprice'])
def set_price_handler(message):
    if message.chat.id != ADMIN_ID2:
        bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")
        return

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Бензин", callback_data="setprice_benzin"),
        InlineKeyboardButton("Газ", callback_data="setprice_gaz")
    )
    bot.send_message(message.chat.id, "🔧 Какое топливо изменить?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("setprice_"))
def fuel_price_selection(call):
    if call.message.chat.id != ADMIN_ID2:
        bot.send_message(call.message.chat.id, "❌ У вас нет доступа.")
        return

    fuel = call.data.split("_")[1]
    price_change_sessions[call.message.chat.id] = fuel
    bot.send_message(call.message.chat.id, f"💬 Введите новую цену для {fuel.upper()} (в рублях):")


@bot.message_handler(func=lambda m: m.chat.id in price_change_sessions)
def price_input_handler(message):
    fuel = price_change_sessions.get(message.chat.id)

    try:
        new_price = float(message.text.replace(',', '.'))
        FUEL_PRICES[fuel] = new_price
        del price_change_sessions[message.chat.id]
        bot.send_message(message.chat.id, f"✅ Цена на {fuel.upper()} обновлена: {new_price:.2f} ₽")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите корректное число.")

@bot.message_handler(commands=['history'])
def show_history(msg):
    chat_id = msg.chat.id

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT "Адрес", "Топливо", ROUND("Рубли"), "Литры", "Дата", "Оплата"
        FROM history
        WHERE "Telegram_ID" = ?
        ORDER BY "Дата" DESC
        LIMIT 10
    ''', (chat_id,))
    records = cursor.fetchall()
    conn.close()

    if not records:
        bot.send_message(chat_id, "📭 История пуста.")
        return

    history_text = "🕘 Последние заказы:\n\n"
    for row in records:
        station, fuel, rub, litres, ts, pay = row
        history_text += (
            f"📍 {station}\n"
            f"🛢 Топливо: {fuel}\n"
            f"💸 Сумма: {int(rub)} ₽\n"
            f"⛽️ Объем: {litres:.2f} л\n"
            f"💳 Оплата: {pay}\n"
            f"🗓 {ts}\n\n"
        )

    bot.send_message(chat_id, history_text)
def save_to_db(chat_id):
    data = user_sessions.get(chat_id)
    if not data:
        return

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO history ("Адрес", "Топливо", "Рубли", "Литры", "Оплата", "Telegram_ID")
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data['station_name'],
        data['fuel_name'],
        data['rub'],
        data['litres'],
        'Наличные' if data['payment_method'] == 'cash' else 'Безнал',
        chat_id
    ))
    conn.commit()
    conn.close()
    reset_state(chat_id)


@bot.callback_query_handler(func=lambda call: call.data == "rext")
def show_repair_info(message):
    text = (
        "🚗 <b>Элит Рихтовка — Тольятти</b>\n"
        "📍 ул. 40 лет Победы, 94Б\n"
        "🕘 Пн–Пт 08:30–18:00\n"
        "📞 +7 927 729‑…\n\n"
        "✨ <b>Что делают:</b>\n"
        "🔧 Рихтовка без следов\n"
        "🎨 Покраска с подбором цвета\n"
        "🧲 Вакуумная правка\n"
        "🔩 Ремонт бамперов и кузова\n"
        "💯 Гарантия, качество, честные цены\n\n"
        "💬 <b>Отзывы:</b> ⭐ 5.0 — довольны все\n"
        "📲 Есть WhatsApp и Telegram\n"
        "🎁 Часто бонусы и скидки\n\n"
        "Хочешь — найду прямые контакты или помогу записаться!"
    )


    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("📊 Цены", callback_data="repair_prices"),
        types.InlineKeyboardButton("🎁 Скидки", callback_data="repair_discounts")
    )

    bot.send_message(message.from_user.id, text, reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "taxi")
def handle_taxi(call):
    bot.answer_callback_query(call.id)

    app_link = "https://play.google.com/store/apps/details?id=com.taxi.app"  # вставь свою ссылку

    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton("Скачать приложение", url=app_link)
    markup.add(button)

    bot.send_message(
        call.message.chat.id,
        "🚕 Чтобы заказать такси, позвоните по номеру: +7 123 456 78 90\n"
        "Или скачайте наше приложение для быстрого заказа:",
        reply_markup=markup
    )
@bot.callback_query_handler(func=lambda call: call.data == "about")
def handle_about(call):
    text = (
        "🚗 <b>ЭЛИТ — ваш комфорт на дороге!</b>\n\n"
        "Мы — команда профессионалов в Тольятти, которая делает всё, "
        "чтобы ваше передвижение было лёгким, стильным и безопасным.\n\n"
        "🔧 <b>Наши направления:</b>\n"
        "— Аренда и прокат автомобилей\n"
        "— Заказ такси (эконом, комфорт, бизнес)\n"
        "— Кузовной ремонт и детейлинг\n"
        "— Ремонт авто, катеров, спецтехники\n\n"
        "📍 Адреса:\n\n"
        "<b>г. Тольятти, ул. Борковская 59:</b>\n"
        "🫧 Мойка\n"
        "🔧 СТО\n"
        "☎️ Офис\n\n"
        "<b>⛽️ Заправки</b>:\n"
        "• Южное шоссе 129 газ и бензин\n"
        "• Южное шоссе 12/2 газ и бензин\n"
        "• Лесная 66А газ\n"
        "• Борковская 72/1 (г)\n\n"
        "<b>г. Тольятти, ул. 40 лет Победы 94Б</b>:\n"
        "🛠 Кузовной ремонт\n"
        "🎨 Покраска авто\n\n"
        "📞 Всегда на связи и готовы помочь!"
    )
    bot.send_message(call.message.chat.id, text, parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data == "jobs")
def handle_jobs(call):
    bot.answer_callback_query(call.id)

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🚕 Водитель такси", callback_data="job_taxi"),
        types.InlineKeyboardButton("🚚 Водитель Газели", callback_data="job_gazel"),
        types.InlineKeyboardButton("🎨 Маляр по авто", callback_data="job_painter")
    )
    bot.send_message(call.message.chat.id, "💼 Выберите вакансию:", reply_markup=kb)

from telebot import TeleBot, types
from telebot.handler_backends import State, StatesGroup
import pytesseract
from PIL import Image
import os

# from telebot import TeleBot, types
# from telebot.handler_backends import State, StatesGroup
# import pytesseract
# from PIL import Image
# import os
# import re
# from datetime import datetime
#
#
#
# admin_reply_target = {}
#
# # Состояния
# class JobStates(StatesGroup):
#     waiting_for_license = State()
#     waiting_for_full_name = State()
#     waiting_for_birth_date = State()
#     waiting_for_license_number = State()
#     waiting_for_kbm_reply = State()
#
#
# def fix_ocr_mixed_text(text):
#     replacements = {
#         'A': 'А', 'B': 'В', 'C': 'С', 'E': 'Е', 'H': 'Н', 'K': 'К',
#         'M': 'М', 'O': 'О', 'P': 'Р', 'T': 'Т', 'X': 'Х', 'Y': 'У',
#         'a': 'а', 'e': 'е', 'o': 'о', 'p': 'р', 'c': 'с', 'x': 'х',
#         'y': 'у', 'k': 'к', 'm': 'м', 't': 'т', 'h': 'н', 'u': 'и', 'i': 'й',
#         '4b': 'б', '$': 'З'
#     }
#     for latin, cyrillic in replacements.items():
#         text = text.replace(latin, cyrillic)
#     return text
#
#
# def extract_full_name(lines):
#     for i in range(len(lines) - 1):
#         if lines[i].isupper() and len(lines[i].split()) == 1:
#             name_parts = lines[i + 1].split()
#             if len(name_parts) >= 2:
#                 return f"{lines[i].capitalize()} {name_parts[0].capitalize()} {name_parts[1].capitalize()}"
#             elif len(name_parts) == 1:
#                 return f"{lines[i].capitalize()} {name_parts[0].capitalize()}"
#     return lines[0].capitalize() if lines else None
#
#
# def extract_categories(text):
#     pattern = r'\b(A|B|C|D|BE|CE|DE)\b'
#     matches = re.findall(pattern, text.upper())
#     return set(matches)
#
#
# def is_category_suitable(job, categories):
#     if job == "такси":
#         return any('B' in cat for cat in categories)
#     elif job == "газель":
#         return any('B' in cat.upper() for cat in categories)
#     else:
#         return False
#
#
# def extract_issue_and_expiry_dates(text):
#     issue_date = None
#     expiry_date = None
#
#     # Ищем дату после 4a)
#     issue_match = re.search(r'4a\)?\s*[-–—]?\s*(\d{2}[.\-/ ]\d{2}[.\-/ ]\d{4})', text, re.IGNORECASE)
#     if issue_match:
#         issue_date = issue_match.group(1).replace("-", ".").replace("/", ".").replace(" ", ".")
#
#     # Ищем дату после 4b)
#     expiry_match = re.search(r'4b\)?\s*[-–—]?\s*(\d{2}[.\-/ ]\d{2}[.\-/ ]\d{4})', text, re.IGNORECASE)
#     if expiry_match:
#         expiry_date = expiry_match.group(1).replace("-", ".").replace("/", ".").replace(" ", ".")
#
#     # Если issue_date нет, но есть expiry_date, попробуем найти дату перед 4b)
#     if not issue_date and expiry_match:
#         pattern_before_4b = r'(\d{2}[.\-/ ]\d{2}[.\-/ ]\d{4})\s*4b\)?'
#         before_4b_match = re.search(pattern_before_4b, text, re.IGNORECASE)
#         if before_4b_match:
#             issue_date = before_4b_match.group(1).replace("-", ".").replace("/", ".").replace(" ", ".")
#         else:
#             # fallback — ставим дату окончания (плохо, но пусть будет)
#             issue_date = expiry_date
#
#     return issue_date, expiry_date
#
#
# def calculate_experience(issue_date_str):
#     try:
#         issue_date = datetime.strptime(issue_date_str, "%d.%m.%Y")
#     except:
#         return 0
#     today = datetime.today()
#     years = today.year - issue_date.year
#     if (today.month, today.day) < (issue_date.month, issue_date.day):
#         years -= 1
#     return max(years, 0)
#
#
# def send_to_admin_with_button(chat_id, user_id, summary):
#     keyboard = types.InlineKeyboardMarkup()
#     keyboard.add(types.InlineKeyboardButton("✍️ Ответить (ввести КБМ)", callback_data=f"reply_kbm:{user_id}"))
#     bot.send_message(ADMIN_ID2, f"🧾 Данные для проверки:\n{summary}", reply_markup=keyboard)
#
#
# @bot.message_handler(state=JobStates.waiting_for_license, content_types=["photo"])
# def handle_license_photo(message):
#     user_id = message.from_user.id
#     photo_id = message.photo[-1].file_id
#     file_info = bot.get_file(photo_id)
#     downloaded_file = bot.download_file(file_info.file_path)
#
#     path = f"temp_{user_id}.jpg"
#     with open(path, "wb") as f:
#         f.write(downloaded_file)
#
#     image = Image.open(path)
#     text = pytesseract.image_to_string(image, lang='rus+eng')
#     os.remove(path)
#
#     raw_lines = [line.strip() for line in text.splitlines() if line.strip()]
#     cleaned_lines = [fix_ocr_mixed_text(line) for line in raw_lines]
#
#     full_name = extract_full_name(cleaned_lines)
#
#     birth_pattern = re.search(r'\d{2}[.\-/ ]\d{2}[.\-/ ]\d{4}', text)
#     birth_date = birth_pattern.group().replace(" ", ".").replace("-", ".").replace("/", ".") if birth_pattern else None
#
#     vu_pattern = re.search(r'\d{10}', text.replace(" ", ""))
#     license_number = vu_pattern.group() if vu_pattern else None
#
#     issue_date, expiry_date = extract_issue_and_expiry_dates(text)
#
#     categories = extract_categories(text)
#
#     selected_job = user_data.get(user_id, {}).get("selected_job")
#
#     if not selected_job:
#         bot.send_message(message.chat.id, "❗ Пожалуйста, сначала выберите вакансию.")
#         return
#
#     missing = []
#     if not full_name: missing.append("ФИО")
#     if not birth_date: missing.append("дата рождения")
#     if not license_number: missing.append("номер ВУ")
#
#     user_data[user_id].update({
#         "full_name": full_name,
#         "birth_date": birth_date,
#         "license_number": license_number,
#         "issue_date": issue_date,
#         "expiry_date": expiry_date,
#         "missing": missing,
#         "text": text,
#         "message_id": message.message_id,
#         "categories": categories
#     })
#
#     bot.send_message(
#         message.chat.id,
#         f"🧾 ВСЯ ИНФОРМАЦИЯ:\n"
#         f"ФИО: {full_name or '❌ не найдено'}\n"
#         f"Дата рождения: {birth_date or '❌ не найдена'}\n"
#         f"Номер ВУ: {license_number or '❌ не найден'}\n"
#         f"Дата выдачи ВУ: {issue_date or '❌ не найдена'}\n"
#         f"Дата окончания ВУ: {expiry_date or '❌ не найдена'}\n"
#         f"Категории: {', '.join(categories) if categories else 'не найдены'}\n"
#         f"Текст: \n{text}"
#     )
#
#     if not is_category_suitable(selected_job, categories):
#         if selected_job == "такси" and "B" not in categories:
#             bot.send_message(message.chat.id,
#                              "❌ Для работы водителем такси у вас должна быть категория B.\n"
#                              "Пожалуйста, проверьте своё ВУ или выберите другую вакансию.")
#             bot.delete_state(user_id, message.chat.id)
#             return
#         elif selected_job == "газель" and not any(cat.lower() == "B" for cat in categories):
#             bot.send_message(message.chat.id,
#                              "❌ Для работы водителем Газели у вас должна быть категория B.\n"
#                              "Пожалуйста, проверьте своё ВУ или выберите другую вакансию.")
#             bot.delete_state(user_id, message.chat.id)
#             return
#
#     if not missing:
#         bot.send_message(message.chat.id,
#                          f"✅ Извлечённые данные:\nФИО: {full_name}\nДата рождения: {birth_date}\n"
#                          f"ВУ: {license_number}\nДата выдачи ВУ: {issue_date}")
#         bot.delete_state(user_id, message.chat.id)
#     else:
#         bot.send_message(message.chat.id, f"⚠️ Не удалось извлечь: {', '.join(missing)}. Введите вручную:")
#         proceed_next_missing(message)
#
#     bot.set_state(user_id, JobStates.waiting_for_full_name, message.chat.id)
#     bot.send_message(message.chat.id, "Пожалуйста, введите ФИО полностью:")
#
#
# def proceed_next_missing(message):
#     user_id = message.from_user.id
#     missing = user_data[user_id]["missing"]
#
#     # После ввода ФИО в функции input_full_name нужно убрать "ФИО" из missing, чтобы proceed_next_missing правильно работал
#     # И теперь пропускаем "ФИО" если вдруг она там осталась, т.к. мы её уже ввели
#
#     # Убираем "ФИО" из missing, если она там есть
#     if "ФИО" in missing:
#         missing.remove("ФИО")
#
#     if not missing:
#         send_summary_to_admin(user_id, message.chat.id)
#         bot.delete_state(user_id, message.chat.id)
#         return
#
#     next_field = missing[0]
#     if next_field == "дата рождения":
#         bot.set_state(user_id, JobStates.waiting_for_birth_date, message.chat.id)
#         bot.send_message(message.chat.id, "Введите дату рождения (ДД.ММ.ГГГГ):")
#     elif next_field == "номер ВУ":
#         bot.set_state(user_id, JobStates.waiting_for_license_number, message.chat.id)
#         bot.send_message(message.chat.id, "Введите номер ВУ (10 цифр):")
#
# @bot.message_handler(state=JobStates.waiting_for_full_name)
# def input_full_name(message):
#     user_id = message.from_user.id
#     text = message.text.strip()
#     if len(text.split()) < 2:
#         bot.send_message(message.chat.id, "ФИО должно содержать 2 или 3 слова. Попробуйте ещё раз:")
#         return
#     user_data[user_id]["full_name"] = text
#     user_data[user_id]["user_id"] = user_id
#     if "ФИО" in user_data[user_id]["missing"]:
#         user_data[user_id]["missing"].remove("ФИО")
#     proceed_next_missing(message)
#
# @bot.message_handler(state=JobStates.waiting_for_birth_date)
# def input_birth_date(message):
#     user_id = message.from_user.id
#     text = message.text.strip()
#     if not re.fullmatch(r'\d{2}[.]\d{2}[.]\d{4}', text):
#         bot.send_message(message.chat.id, "Введите дату в формате ДД.ММ.ГГГГ.")
#         return
#     user_data[user_id]["birth_date"] = text
#     user_data[user_id]["missing"].remove("дата рождения")
#     proceed_next_missing(message)
#
# @bot.message_handler(state=JobStates.waiting_for_license_number)
# def input_license_number(message):
#     user_id = message.from_user.id
#     text = message.text.strip()
#     if not re.fullmatch(r'\d{10}', text):
#         bot.send_message(message.chat.id, "Номер ВУ должен быть из 10 цифр.")
#         return
#     user_data[user_id]["license_number"] = text
#     user_data[user_id]["missing"].remove("номер ВУ")
#     proceed_next_missing(message)
#
# def send_summary_to_admin(user_id, chat_id):
#     data = user_data[user_id]
#     experience = calculate_experience(data.get("issue_date") or "01.01.1970")
#     summary = (f"ФИО: {data['full_name']}\n"
#                f"Дата рождения: {data['birth_date']}\n"
#                f"Номер ВУ: {data['license_number']}\n"
#                f"Стаж (примерно): {experience} лет")
#     send_to_admin_with_button(chat_id, user_id, summary)
#
# @bot.callback_query_handler(func=lambda call: call.data.startswith("reply_kbm:"))
# def admin_kbm_reply(call):
#     user_id = int(call.data.split(":")[1])
#     admin_reply_target[DAN_ID] = user_id  # Помощник вводит КБМ
#     bot.set_state(DAN_ID, JobStates.waiting_for_kbm_reply, call.message.chat.id)
#     bot.send_message(call.message.chat.id, f"Введите КБМ для пользователя {user_id}")
#     bot.answer_callback_query(call.id)
#
# def calculate_age(birth_date_str):
#     try:
#         birth_date = datetime.strptime(birth_date_str, "%d.%m.%Y")
#     except Exception:
#         return "неизвестен"
#     today = datetime.today()
#     age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
#     return age
#
# @bot.message_handler(state=JobStates.waiting_for_kbm_reply)
# def handle_kbm_reply(message):
#     admin_id = message.from_user.id
#     if admin_id != DAN_ID:
#         bot.send_message(admin_id, "⚠️ Только помощник админа может вводить КБМ.")
#         return
#
#     user_id = admin_reply_target.get(admin_id)
#     if not user_id:
#         bot.send_message(admin_id, "⚠️ Пользователь не найден.")
#         return
#
#     try:
#         kbm = float(message.text.strip().replace(",", "."))
#     except ValueError:
#         bot.send_message(admin_id, "Введите КБМ как число, например 0.95")
#         return
#
#     # 💡 Просто сохраняем по user_id
#     user_data[user_id]["kbm"] = kbm
#     bot.delete_state(admin_id, message.chat.id)
#     show_user_rental_calendar(message)

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

#class JobStates(StatesGroup):
 #   waiting_for_license = State()

@bot.callback_query_handler(func=lambda call: call.data == "job_painter")
def handle_job_painter(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id

    description = (
        "🎨 <b>Вакансия: Маляр по покраске автомобилей</b>\n\n"
        "📍 <b>Локация:</b> [укажите адрес или город]\n"
        "💼 <b>Тип занятости:</b> Полная занятость\n"
        "💰 <b>Зарплата:</b> от 70 000 ₽/мес\n\n"
        "🔧 <b>Обязанности:</b>\n"
        "• Подготовка деталей к покраске\n"
        "• Окраска автомобилей в камере\n"
        "• Полировка, устранение дефектов\n\n"
        "🧰 <b>Требования:</b>\n"
        "• Опыт от 1 года\n"
        "• Аккуратность и внимательность\n"
        "• Ответственность\n\n"
        "✅ <b>Мы предлагаем:</b>\n"
        "• Современное оборудование\n"
        "• Стабильную загрузку\n"
        "• Своевременную оплату\n"
        "• Дружный коллектив\n\n"
        "📞 Для отклика: +7 (XXX) XXX-XX-XX"
    )

    user_data[user_id] = {"selected_job": "painter"}

    bot.send_message(call.message.chat.id, description, parse_mode="HTML")

    # Вызов календаря без car_id
    show_user_calendar(call.message, None, user_id)

class JobStates(StatesGroup):
    waiting_for_license = State()

@bot.callback_query_handler(func=lambda call: call.data.startswith("meeting_next_") or call.data == "return_location")
def yes_or_no(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id  # предпочтительнее использовать user_id
    print("Callback received:", call.data)

    if call.data.startswith("meeting_next_"):
        car_id_str = call.data.replace("meeting_next_", "")
        try:
            car_id = int(car_id_str)
        except ValueError:
            bot.answer_callback_query(call.id, "Ошибка ID машины.")
            return

        # Обновляем сессию
        session = get_session(user_id)
        session['selected_car_id'] = car_id
        set_state(user_id, f"waiting_for_meeting_date_{car_id}")

        bot.answer_callback_query(call.id)

        # Читаем из сессии delivery_address и delivery_price
        delivery_address = session.get("delivery_address")
        delivery_price = session.get("delivery_price")

        if not delivery_address or not delivery_price:
            bot.send_message(chat_id, "⚠ Не найдены данные о доставке. Повторите ввод.")
            return

        with sqlite3.connect("cars.db") as conn:
            cursor = conn.cursor()

            # Получаем user_id из БД (твой уникальный id)
            cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (chat_id,))
            row = cursor.fetchone()
            if not row:
                bot.send_message(chat_id, "⚠ Пользователь не найден в базе.")
                return

            db_user_id = row[0]

            # Находим последнюю запись без доставки
            cursor.execute('''
                SELECT id FROM rental_history
                WHERE user_id = ? AND car_id = ? AND delivery_address IS NULL AND delivery_price IS NULL
                ORDER BY rent_start DESC LIMIT 1
            ''', (db_user_id, car_id))
            rental_row = cursor.fetchone()

            if rental_row:
                rental_id = rental_row[0]
                cursor.execute('''
                    UPDATE rental_history
                    SET delivery_address = ?, delivery_price = ?
                    WHERE id = ?
                ''', (delivery_address, delivery_price, rental_id))
            else:
                print("🚫 Нет записи для обновления доставки.")
                show_user_rental_calendar(call.message, car_id, chat_id)
                return

            # Проверяем наличие доставки и получаем rent_start
            cursor.execute('''
                SELECT rent_start FROM rental_history
                WHERE user_id = ? AND car_id = ? AND delivery_address IS NOT NULL AND delivery_price IS NOT NULL
                ORDER BY rent_start DESC LIMIT 1
            ''', (db_user_id, car_id))
            rent_row = cursor.fetchone()

            if rent_row:
                rent_start = rent_row[0]

                # Обрезаем до даты (если есть время)
                rent_start_str = str(rent_start)[:10]
                rent_dt = datetime.strptime(rent_start_str, "%Y-%m-%d")

                MONTHS_RU = {
                    "January": "Января", "February": "Февраля", "March": "Марта",
                    "April": "Апреля", "May": "Мая", "June": "Июня",
                    "July": "Июля", "August": "Августа", "September": "Сентября",
                    "October": "Октября", "November": "Ноября", "December": "Декабря"
                }

                formatted_date = rent_dt.strftime("%d %B %Y")
                for en, ru in MONTHS_RU.items():
                    formatted_date = formatted_date.replace(en, ru)

                bot.send_message(chat_id, f"📦 Доставка оформлена!\n📅 Встреча состоится: {formatted_date}")

                # Переходим к выбору времени, обновляем состояние в сессии
                set_state(user_id, f"waiting_for_time_selection|rental|{car_id}")

                from types import SimpleNamespace
                fake_message = SimpleNamespace(chat=SimpleNamespace(id=chat_id), text=rent_dt.strftime("%d %b"))
                handle_date_selection(fake_message)

                return

            else:
                print("🚫 Доставка не найдена.")
                show_user_rental_calendar(call.message, car_id, chat_id)

    elif call.data == "return_location":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Написать адрес"))
        bot.send_message(chat_id, "Попробуйте снова", reply_markup=markup)
        bot.answer_callback_query(call.id)


def show_user_rental_calendar(message, car_id):
    chat_id = message.chat.id
    get_session(chat_id)["selected_car_id"] = car_id
    if not car_id:
        bot.send_message(chat_id, "❌ Ошибка: не указан идентификатор автомобиля.")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)

    from datetime import datetime, timedelta
    today = datetime.today()
    buttons = []

    for i in range(30):
        day = today + timedelta(days=i)
        button_text = day.strftime('%d %b')
        buttons.append(types.KeyboardButton(button_text))

    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i + 3])

    bot.send_message(chat_id, "📅 Выберите дату встречи:", reply_markup=markup)
@bot.message_handler(func=lambda message: (get_state(message.from_user.id) or '').startswith('waiting_for_rental_time_'))
def process_rental_time(message):
    print(1)
    user_id = message.from_user.id
    chat_id = message.chat.id
    state = get_state(user_id) or ''

    if state.startswith('waiting_for_rent_time_'):
        car_id = int(state.split('_')[-1])  # извлечь car_id из состояния
        selected_date = message.text  # например, '30 May'

        if not car_id:
            bot.send_message(chat_id, "Не удалось определить выбранную машину.")
            return

        bot.send_message(chat_id, f"Вы выбрали дату {selected_date} для машины с ID {car_id}.")




@bot.callback_query_handler(func=lambda call: call.data in ["job_taxi", "job_gazel"])
def handle_job_selection(call):
    user_id = call.from_user.id
    job_title = "такси" if call.data == "job_taxi" else "газель"
    car_id = "taxi_001" if job_title == "такси" else "gazel_001"

    user_data[user_id] = {
        "selected_job": job_title,
        "car_id": car_id
    }

    description = (
        "🚖 *Вакансия: Водитель такси*\n\n"
        "✅ _Преимущества:_\n"
        "• Без диспетчерских комиссий\n"
        "• Свободный график — работаешь когда хочешь\n"
        "• ...\n"
        "• *Нужен ИП*\n"
        "• 💰 Заработок зависит только от тебя\n"
    ) if job_title == "такси" else (
        "🚚 *Вакансия: Водитель Газели*\n\n"
        "✅ _Преимущества:_\n"
        "• График работы обсуждается индивидуально\n"
        "• ...\n"
        "• ЗП от 80 000 ₽\n"
    )

    bot.send_message(call.message.chat.id, description, parse_mode="Markdown")
    bot.send_message(call.message.chat.id, "📸 Пожалуйста, отправьте фото водительского удостоверения.")

    # FSM или собственное состояние
    try:
        bot.set_state(user_id, JobStates.waiting_for_license, call.message.chat.id)
    except Exception as e:
        print(f"[!] FSM ошибка set_state: {e}")

@bot.message_handler(content_types=['photo'])
def handle_all_photos(message):
    user_id = message.from_user.id
    state = get_state(user_id)
    photo_id = message.photo[-1].file_id

    # 🔹 1. Админ добавляет машину
    if state == "admin_add_car_photo":
        session = get_session(user_id)
        session["photo"] = photo_id

        with db_lock:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO cars (brand_model, year, transmission, photo_url, service, is_available)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (
                session.get("model"),
                session.get("year"),
                session.get("transmission"),
                photo_id,
                session.get("service")
            ))
            conn.commit()
            conn.close()

        # Подтверждение
        text = (
            f"<b>Модель:</b> {session.get('model')}\n"
            f"<b>Год:</b> {session.get('year')}\n"
            f"<b>Коробка:</b> {session.get('transmission')}\n"
            f"<b>Тип услуги:</b> {session.get('service')}"
        )
        bot.send_message(user_id, f"✅ Машина добавлена:\n\n{text}", parse_mode="HTML")
        bot.send_photo(user_id, photo_id)
        user_sessions.pop(user_id, None)
        clear_state(user_id)
        return

    # 🔹 2. Добавление машины в другом потоке (add_car_flow)
    if user_id in add_car_flow:
        car_data = add_car_flow[user_id]
        car_data['photo_url'] = photo_id

        with db_lock:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO cars (brand_model, year, transmission, photo_url, is_available)
                VALUES (?, ?, ?, ?, 1)
            """, (car_data['brand_model'], car_data['year'], car_data['transmission'], photo_id))
            conn.commit()
            conn.close()

        bot.send_message(user_id, "✅ Машина успешно добавлена в базу!")
        del add_car_flow[user_id]
        return
    session = get_session(user_id)
    selected_job = user_data.get(user_id, {}).get("selected_job")
    car_id = user_data.get(user_id, {}).get("car_id") or session.get("car_id")

    with db_lock:
        conn = get_db_connection()
        cur = conn.cursor()

        # Сохраняем фото прав
        cur.execute("UPDATE users SET driver_license_photo = ? WHERE telegram_id = ?", (photo_id, user_id))
        conn.commit()
        conn.close()

    bot.send_message(message.chat.id, "✅ Фото удостоверения получено.")

    # 🔹 4. Переход к календарю
    if selected_job:
        if selected_job in ["такси", "газель"]:
            show_user_calendar(message, None, user_id)

        elif selected_job in ["rent", "rental"]:
            if not car_id:
                bot.send_message(message.chat.id, "❌ Сначала выберите машину.")
                return

            service = session.get("service") or selected_job  # <- извлекаем тип услуги

            if service == "rental":
                session["selected_car_id"] = car_id
                session["state"] = "waiting_for_rental_start"
                bot.send_message(message.chat.id, "Теперь выберите дату для бронирования:",
                                 reply_markup=create_calendar_markup())
                return
            else:
                show_user_calendar(message, car_id, user_id)

        else:
            show_user_calendar(message, car_id, user_id)


# @bot.message_handler(content_types=['photo'])
# def handle_photo(message):
#     user_id = message.from_user.id
#     photo_id = message.photo[-1].file_id
#
      # ✅ правильно
#
#     print(f"📌 selected_job: {selected_job}")
#     print(f"📌 session: {session}")
#
#     car_id = user_data.get(user_id, {}).get("car_id") or session.get("car_id")
#
#     conn = sqlite3.connect('cars.db')
#     cursor = conn.cursor()
#
#     if selected_job in ["такси", "газель"]:
#         car_id = 0  # присваиваем 0 для этих вакансий
#
#         # Сохраняем фото в БД
#         cursor.execute("UPDATE users SET driver_license_photo = ? WHERE telegram_id = ?", (photo_id, user_id))
#         conn.commit()
#         conn.close()
#
#         bot.send_message(message.chat.id, "✅ Фото получено.")
#         show_user_calendar(message, None, user_id)
#
#     elif selected_job in ["rent", "rental"]:
#         if not car_id:
#             bot.send_message(message.chat.id, "❌ Сначала выберите машину.")
#             conn.close()
#             return
#
#         # Сохраняем фото в БД
#         cursor.execute("UPDATE users SET driver_license_photo = ? WHERE telegram_id = ?", (photo_id, user_id))
#         conn.commit()
#         conn.close()
#
#         bot.send_message(message.chat.id, "✅ Фото получено.")
#         show_user_calendar(message, car_id, user_id)
#
#     else:
#         bot.send_message(message.chat.id, "⚠️ Фото не требуется для этой вакансии.")
@bot.message_handler(func=lambda message: (get_state(message.from_user.id) or "").startswith("waiting_for_time_selection|"))
def handle_date_selection(message):
    from datetime import datetime
    import sqlite3

    user_id = message.from_user.id
    chat_id = message.chat.id
    user_input = message.text.strip()

    # Пробуем распарсить дату в русском формате, например "21 июля"
    chosen_date = parse_russian_date(user_input)
    if not chosen_date:
        bot.send_message(chat_id, "❌ Неверный формат даты. Пожалуйста, выберите дату с клавиатуры.")
        return

    date_str = chosen_date.strftime("%Y-%m-%d")

    # Разбор состояния
    state = get_state(user_id)
    parts = state.split("|")
    if len(parts) != 3:
        bot.send_message(chat_id, "⚠️ Ошибка состояния. Повторите попытку.")
        return

    _, service, car_id = parts

    # Получаем уже забронированные слоты
    conn = sqlite3.connect('cars.db')
    c = conn.cursor()
    c.execute("""
        SELECT time FROM bookings
        WHERE date = ? AND status = 'confirmed'
    """, (date_str,))
    booked_times = set(t[0] for t in c.fetchall())
    conn.close()

    # Формируем inline-клавиатуру
    markup = types.InlineKeyboardMarkup(row_width=3)
    has_available = False

    for hour in range(0, 24):  # Время с 10:00 до 19:59
        for minute in range(0, 60, 10):  # каждые 10 минут
            time_str = f"{hour:02}:{minute:02}"
            if time_str not in booked_times:
                has_available = True
                callback_data = f"select_time|{service}|{car_id}|{date_str}|{time_str}"
                markup.add(types.InlineKeyboardButton(time_str, callback_data=callback_data))

    bot.send_message(chat_id, f"📅 Вы выбрали дату: {user_input}", reply_markup=types.ReplyKeyboardRemove())

    if has_available:
        bot.send_message(chat_id, "🕐 Выберите свободное время:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "❌ На эту дату нет свободных времён. Попробуйте другую.")

    # Сохраняем новое состояние
    set_state(user_id, f"waiting_for_time_pick|{service}|{car_id}|{date_str}")
# Обработчик выбора времени (callback query)
   # markup = types.InlineKeyboardMarkup(row_width=3)
    # has_available = False
    #
    # for hour in range(10, 19):  # с 10:00 до 18:00
    #     time_str = f"{hour:02}:00"
    #     if time_str not in booked_times:
    #         has_available = True
    #         callback_data = f"select_time|{service}|{car_id}|{date_str}|{time_str}"
    #         markup.add(types.InlineKeyboardButton(time_str, callback_data=callback_data))
    #


@bot.callback_query_handler(func=lambda call: call.data.startswith("select_time|"))
def handle_time_selection(call):
    try:
        _, service, car_id_str, date_str, time_str = call.data.split("|")
        car_id = int(car_id_str) if car_id_str.isdigit() else 0
    except Exception:
        bot.answer_callback_query(call.id, text="Ошибка данных.")
        return

    telegram_id = call.from_user.id
    chat_id = call.message.chat.id

    conn = sqlite3.connect('cars.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Получаем пользователя по telegram_id
        cursor.execute("SELECT id, telegram_id, name FROM users WHERE telegram_id = ?", (telegram_id,))
        user_row = cursor.fetchone()
        if not user_row:
            bot.send_message(chat_id, "⚠️ Вы не зарегистрированы. Нажмите /start.")
            return

        user_id = user_row['id']
        user_telegram_id = user_row['telegram_id']
        full_name = user_row['name']

        # Сохраняем бронирование
        cursor.execute("""
            INSERT INTO bookings (service, car_id, user_id, date, time, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (service, car_id, user_telegram_id, date_str, time_str, 'pending'))
        conn.commit()

        if car_id != 0 and car_id is not None:
            cursor.execute("UPDATE cars SET is_available = 0 WHERE car_id = ?", (car_id,))
            conn.commit()

        # Получаем данные машины, если есть
        car = None
        if car_id:
            cursor.execute("SELECT brand_model, year FROM cars WHERE car_id = ?", (car_id,))
            car = cursor.fetchone()

    except Exception as e:
        conn.rollback()
        bot.send_message(chat_id, f"❌ Ошибка бронирования: {e}")
        return
    finally:
        conn.close()

    # Информация о доставке
    session = get_session(user_telegram_id) if 'get_session' in globals() else None
    delivery_info = ""
    if session:
        delivery_address = session.get("delivery_address")
        delivery_price = session.get("delivery_price")
        if delivery_address and delivery_price is not None:
            delivery_info = (
                f"\n🚚 Доставка:\n"
                f"Адрес: {delivery_address}\n"
                f"Стоимость: 💸 {delivery_price} ₽"
            )
        elif delivery_address:
            delivery_info = f"\n🚚 Доставка по адресу: {delivery_address}"
        else:
            delivery_info = "\n🚚 Доставка: не указана"

    # Отображение услуги на русском
    service_display = {
        "rent": "аренда",
        "rental": "прокат",
        "taxi": "такси",
        "газель": "газель",
        "painter": "маляр"
    }.get(service, service)

    # Формируем клавиатуру (без кнопки "Ответить")
    car_id_str = car_id_str if car_id_str.isdigit() else "0"
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Принять",
                                   callback_data=f"approve_{service}_{car_id_str}_{user_id}_{user_telegram_id}_{date_str}_{time_str}"),
        types.InlineKeyboardButton("🕒 Предложить другое время",
                                   callback_data=f"suggest_{car_id_str}_{user_telegram_id}"),
    )
    markup.add(
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{car_id_str}_{user_telegram_id}"),
    )

    # Добавляем кнопку "Водительское удостоверение", только если сервис не painter
    if service != "painter":
        markup.add(types.InlineKeyboardButton(
            "📄 Водительское удостоверение",
            callback_data=f"show_driver_license_{user_telegram_id}"
        ))

    # Формируем сообщение админу
    message_text = (
        f"📥 Новая заявка:\n\n"
        f"👤 Имя: {full_name}\n"
        f"🛠 Услуга: {service_display}\n"
        f"📅 Дата: {date_str}\n"
        f"⏰ Время: {time_str}"
    )

    if car:
        brand_model, year = car['brand_model'], car['year']
        message_text += f"\n🚗 Машина: {brand_model} ({year})"

    message_text += delivery_info

    # Отправляем админу
    bot.send_message(ADMIN_ID2, message_text, reply_markup=markup)
    bot.send_message( user_telegram_id, f"✅Отлично!\nМы Уже отправили заявку админу. Это может занять некоторое время")
@bot.message_handler(commands=['show_bookings'])
def show_bookings(message):
    try:
        conn = sqlite3.connect('cars.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM bookings ORDER BY id DESC")
        bookings = cursor.fetchall()

        if not bookings:
            bot.send_message(message.chat.id, "📋 Нет бронирований.")
            return

        def split_message(text, max_length=4000):
            parts = []
            while len(text) > max_length:
                split_index = text.rfind('\n', 0, max_length)
                if split_index == -1:
                    split_index = max_length
                parts.append(text[:split_index])
                text = text[split_index:]
            parts.append(text)
            return parts

        response = ""
        for b in bookings:
            response += (
                f"ID: {b['id']}, Service: {b['service']}, Car ID: {b['car_id']}, "
                f"User ID: {b['user_id']}, Date: {b['date']}, Time: {b['time']}, "
                f"Status: {b['status']}\n"
            )

        for part in split_message(response):
            bot.send_message(message.chat.id, part)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при получении бронирований: {e}")
    finally:
        conn.close()
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def process_approve(call):
    try:
        full_data = call.data[len("approve_"):]
        parts = full_data.split("_")
        if len(parts) < 6:
            raise ValueError(f"Недостаточно частей в callback_data: {parts}")

        service = parts[0]
        car_id_raw = parts[1]
        print(car_id_raw)
        car_id = int(car_id_raw) if car_id_raw != "None" else 0
        user_id = int(parts[2])  # Добавлено, чтобы отправлять сообщение в Telegram

        date_str = parts[4]
        time_str = parts[5]



        with db_lock:
            conn = get_db_connection()
            cur = conn.cursor()


            # Обновляем статус машины


            # Получаем telegram_id по user_id
            cur.execute("SELECT telegram_id FROM users WHERE id = ?", (user_id,))
            result = cur.fetchone()
            if result is None or result[0] is None:
                raise ValueError(f"Telegram ID не найден для user_id={user_id}")
            telegram_id = result[0]
            print(f"service={service}, car_id={car_id}, user_id={telegram_id}, date={date_str}, time={time_str}")
            # Остальной твой код с выборкой delivery_address и delivery_price
            cur.execute("""
                SELECT delivery_address, delivery_price 
                FROM rental_history
                WHERE user_id = ? AND car_id = ? 
                  AND delivery_address IS NOT NULL 
                  AND delivery_price IS NOT NULL
                ORDER BY rent_start DESC
                LIMIT 1
            """, (user_id, car_id))
            delivery_row = cur.fetchone()
            if car_id_raw == "0":

                # ищем записи с car_id IS NULL
                update_query = '''
                    UPDATE bookings
                    SET status = 'confirmed'
                    WHERE service = ? AND car_id IS NULL AND user_id = ? AND date = ? AND time = ?
                '''
                params = (service, telegram_id, date_str, time_str)
            else:
                update_query = '''
                    UPDATE bookings
                    SET status = 'confirmed'
                    WHERE service = ? AND car_id = ? AND user_id = ? AND date = ? AND time = ?
                '''
                params = (service, car_id, telegram_id, date_str, time_str)
            print(service, car_id, telegram_id, date_str, time_str)
            cur.execute(update_query, params)
            conn.commit()




            conn.close()

        service_display = {
            "rent": "аренду",
            "rental": "прокат",
            "taxi": "поездку (такси)",
            "газель": "услугу (Газель)"
        }.get(service, service)

        if delivery_row:
            delivery_address, delivery_price = delivery_row
            payment_text = f"""
💳 *Реквизиты для перевода:*  
Получатель: Нугуманов Даниэль Радикович  
СБП / Телефон: +7 9297107180  
Карта МИР: 2200 7019 0981 4094  
Сумма: *{delivery_price} ₽*  
Комментарий к переводу: `оплата за доставку авто`

📝 После перевода нажмите кнопку ниже или отправьте чек сюда.
"""
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("✅ Я оплатил", callback_data=f"paid_delivery_{user_id}"))

            bot.send_message(
                telegram_id,
                f"✅ Ваша заявка на {service_display} одобрена!\n\n"
                f"📅 Дата: {date_str}\n"
                f"🕒 Время: {time_str}\n"
                f"🚗 Доставка будет выполнена по адресу:\n📍 {delivery_address}\n\n"
                f"{payment_text}",
                parse_mode="Markdown",
                reply_markup=markup
            )
        else:
            OFFICE_ADDRESS = "г. Тольятти, ул. Борковская, д. 59"
            bot.send_message(
                telegram_id,
                f"✅ Ваша заявка на {service_display} одобрена!\n\n"
                f"📅 Дата: {date_str}\n"
                f"🕒 Время: {time_str}\n"
                f"Пожалуйста, приезжайте в офис по адресу:\n📍 {OFFICE_ADDRESS}"
            )

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.answer_callback_query(call.id, "Заявка подтверждена.")

    except Exception as e:
        bot.answer_callback_query(call.id, f"Ошибка подтверждения: {e}")
        print(f"❌ Ошибка в process_approve: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("show_driver_license_"))
def show_driver_license(call):
    try:
        user_id = int(call.data[len("show_driver_license_"):])

        with db_lock:
            conn = get_db_connection()
            cur = conn.cursor()
            print(user_id)

            cur.execute("SELECT driver_license_photo FROM users WHERE telegram_id = ?", (user_id,))
            row = cur.fetchone()
            conn.close()

        if row is None or not row[0]:
            bot.answer_callback_query(call.id, "Фото водительского удостоверения не найдено.")
            return

        photo_file_id = row[0]

        # Кнопка "Скрыть"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("❌ Скрыть", callback_data="hiden_driver_license"))

        bot.send_photo(
            call.message.chat.id,
            photo_file_id,
            caption="Водительское удостоверение пользователя",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    except Exception as e:
        bot.answer_callback_query(call.id, f"Ошибка: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "hiden_driver_license")
def hide_driver_license(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        bot.answer_callback_query(call.id, f"Не удалось скрыть: {e}")




@bot.callback_query_handler(func=lambda call: call.data.startswith("suggest_") and
                                          not call.data.startswith("suggest_time_") and
                                          not call.data.startswith("select_date_"))
def process_suggest(call):
    try:
        data = call.data[len("suggest_"):]
        parts = data.split("_")

        if len(parts) < 2:
            print(f"[ERROR] Недостаточно частей в callback_data: {data}")
            bot.answer_callback_query(call.id, "Ошибка данных.")
            return

        if parts[0] == "None" or not parts[0].isdigit() or not parts[1].isdigit():
            print(f"[INFO] Игнорирован callback с некорректными параметрами: {data}")
            # Просто игнорируем без ответа, чтобы не спамить пользователя
            return

        car_id = int(parts[0])
        user_id = int(parts[1])

        chat_id = call.message.chat.id
        session = get_session(user_id) or {}
        session['suggest_car_id'] = car_id
        session['suggest_user_id'] = user_id
        selected_suggest[chat_id] = (car_id, user_id)
        save_session(user_id, session)

        bot.answer_callback_query(call.id)
        show_admin_suggest_calendar(call.message, car_id, user_id)

    except Exception as e:
        import traceback
        print(f"[EXCEPTION in process_suggest]: {e}")
        traceback.print_exc()
        bot.answer_callback_query(call.id, "Произошла ошибка при обработке.")


def show_admin_suggest_calendar(message, car_id, user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    booked_dates_and_times = get_booked_dates_and_times()
    booked_dates = {date for date, _ in booked_dates_and_times}

    today = datetime.today()
    buttons = []

    for i in range(30):
        day = today + timedelta(days=i)
        day_num = day.day
        month_name = list(MONTHS_RU_GEN.keys())[day.month - 1]  # чтобы в родительном падеже
        button_text = f"{day_num} {month_name}"

        # Можно добавить логику отключения забронированных дат:
        # if day.strftime('%Y-%m-%d') in booked_dates:
        #     buttons.append(types.KeyboardButton(f"❌ {button_text}"))
        # else:
        buttons.append(types.KeyboardButton(button_text))

    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i + 3])

    markup.add(types.KeyboardButton("🔙 Отмена"))

    bot.send_message(message.chat.id, "📅 Выберите дату для предложения клиенту:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text and message.chat.id in selected_suggest)
def handle_suggest_date_choice(message):
    chat_id = message.chat.id
    if chat_id not in selected_suggest:
        bot.send_message(chat_id, "⚠️ Невозможно обработать дату: отсутствуют данные по выбору авто. Пожалуйста, начните заново.")
        return

    text = message.text.strip()
    if text == "🔙 Отмена":
        bot.send_message(chat_id, "Отменено.", reply_markup=types.ReplyKeyboardRemove())
        selected_suggest.pop(chat_id, None)
        return

    chosen_date = parse_russian_date(text)
    if not chosen_date:
        bot.send_message(chat_id, "❌ Неверный формат даты. Пожалуйста, выберите дату с клавиатуры.")
        return

    now = datetime.now()
    # Если выбранная дата уже прошла в этом году — сдвигаем на следующий
    if chosen_date.date() < now.date():
        chosen_date = chosen_date.replace(year=now.year + 1)

    date_str = chosen_date.strftime("%Y-%m-%d")

    car_id, user_id = selected_suggest.pop(chat_id)

    session = get_session(user_id)
    session["suggest_date"] = date_str
    save_session(user_id, session)

    bot.send_message(chat_id, f"📅 Дата выбрана: {text}. Теперь выберите время:", reply_markup=types.ReplyKeyboardRemove())
    show_time_selection(message, car_id, user_id, date_str)

def show_time_selection(message, car_id, user_id, date_str):
    conn = sqlite3.connect('cars.db')
    c = conn.cursor()
    c.execute("SELECT time FROM bookings WHERE car_id=? AND date=? AND status='confirmed'", (car_id, date_str))
    booked_times = [row[0] for row in c.fetchall()]
    conn.close()

    keyboard = types.InlineKeyboardMarkup(row_width=3)
    for hour in range(10, 19):
        time_str = f"{hour:02d}:00"
        if time_str in booked_times:
            btn = types.InlineKeyboardButton(f"⛔ {time_str}", callback_data="busy")
        else:
            btn = types.InlineKeyboardButton(time_str, callback_data=f"suggest_time_{car_id}_{user_id}_{date_str}_{time_str}")
        keyboard.add(btn)

    bot.send_message(message.chat.id, f"Выберите время для {date_str}:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("suggest_time_"))
def process_admin_time_selection(call):
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    try:
        data = call.data[len("suggest_time_"):]
        parts = data.split("_")
        if len(parts) != 4:
            bot.answer_callback_query(call.id, text="❌ Неверный формат данных.")
            return

        car_id = int(parts[0])
        user_id = int(parts[1])
        date_str = parts[2]
        time_str = parts[3]
        bot.answer_callback_query(call.id, text=f"Вы выбрали {date_str} {time_str}")

        conn = sqlite3.connect('cars.db')
        c = conn.cursor()

        # Проверка на занятость времени
        c.execute('''SELECT 1 FROM bookings 
                     WHERE car_id=? AND date=? AND time=? AND status='confirmed' ''',
                  (car_id, date_str, time_str))
        if c.fetchone():
            bot.send_message(call.message.chat.id, "⛔ Это время уже занято.")
            conn.close()
            return

        # Получаем telegram_id по user_id
        c.execute("SELECT telegram_id FROM users WHERE telegram_id = ?", (user_id,))
        result = c.fetchone()
        if not result:
            bot.send_message(call.message.chat.id, "❌ Не найден telegram_id для пользователя.")
            conn.close()
            return

        telegram_id = result[0]

        # Записываем предложенное время
        service = 'rent'  # Можно сделать динамическим при необходимости
        c.execute('''
            INSERT INTO bookings (user_id, car_id, service, date, time, status)
            VALUES (?, ?, ?, ?, ?, 'suggested')
        ''', (user_id, car_id, service, date_str, time_str))
        conn.commit()
        conn.close()

        # Кнопка OK для клиента
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("OK", callback_data=f"ok_{service}_{car_id}_{user_id}_{date_str}_{time_str}"))

        # Отправка клиенту
        bot.send_message(telegram_id, f"📩 Администратор предлагает: {date_str} в {time_str}\nЕсли согласны, нажмите кнопку ниже.", reply_markup=markup)
        bot.send_message(call.message.chat.id, "✅ Предложение отправлено клиенту.")

    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("ok_"))
def process_ok(call):
    try:
        full_data = call.data[len("ok_"):]
        parts = full_data.split("_")
        if len(parts) < 5:
            raise ValueError(f"Недостаточно частей в callback_data: {parts}")

        service = parts[0]
        car_id_raw = parts[1]
        car_id = int(car_id_raw) if car_id_raw != "None" else 0
        user_id = int(parts[2])
        telegram_id = user_id  # Добавлено, чтобы отправлять сообщение в Telegram

        date_str = parts[3]
        time_str = parts[4]

        print(f"service={service}, car_id={car_id}, user_id={user_id}, date={date_str}, time={time_str}")

        with db_lock:
            conn = get_db_connection()
            cur = conn.cursor()

            # Получаем telegram_id по user_id
            cur.execute("SELECT telegram_id FROM users WHERE telegram_id = ?", (user_id,))
            result = cur.fetchone()
            if result is None or result[0] is None:
                raise ValueError(f"Telegram ID не найден для user_id={user_id}")
            telegram_id = result[0]

            # Остальной твой код с выборкой delivery_address и delivery_price
            cur.execute("""
                    SELECT delivery_address, delivery_price 
                    FROM rental_history
                    WHERE user_id = ? AND car_id = ? 
                      AND delivery_address IS NOT NULL 
                      AND delivery_price IS NOT NULL
                    ORDER BY rent_start DESC
                    LIMIT 1
                """, (user_id, car_id))
            delivery_row = cur.fetchone()
            conn.close()

        service_display = {
            "rent": "аренду",
            "rental": "прокат",
            "taxi": "поездку (такси)",
            "газель": "услугу (Газель)"
        }.get(service, service)

        if delivery_row:
            delivery_address, delivery_price = delivery_row
            payment_text = f"""
    💳 *Реквизиты для перевода:*  
    Получатель: Нугуманов Даниэль Радикович  
    СБП / Телефон: +7 9297107180  
    Карта МИР: 2200 7019 0981 4094  
    Сумма: *{delivery_price} ₽*  
    Комментарий к переводу: `оплата за доставку авто`

    📝 После перевода нажмите кнопку ниже или отправьте чек сюда.
    """
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("✅ Я оплатил", callback_data=f"paid_delivery_{user_id}"))

            bot.send_message(
                telegram_id,
                f"✅ Ваша заявка на {service_display} одобрена!\n\n"
                f"📅 Дата: {date_str}\n"
                f"🕒 Время: {time_str}\n"
                f"🚗 Доставка будет выполнена по адресу:\n📍 {delivery_address}\n\n"
                f"{payment_text}",
                parse_mode="Markdown",
                reply_markup=markup
            )
        else:
            OFFICE_ADDRESS = "г. Тольятти, ул. Борковская, д. 59"
            bot.send_message(
                telegram_id,
                f"✅ Ваша заявка на {service_display} одобрена!\n\n"
                f"📅 Дата: {date_str}\n"
                f"🕒 Время: {time_str}\n"
                f"Пожалуйста, приезжайте в офис по адресу:\n📍 {OFFICE_ADDRESS}"
            )

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.answer_callback_query(call.id, "Заявка подтверждена.")

    except Exception as e:
        bot.answer_callback_query(call.id, f"Ошибка подтверждения: {e}")
        print(f"❌ Ошибка в process_ok: {e}")
@bot.callback_query_handler(func=lambda call: call.data.startswith("paid_delivery_"))
def handle_paid_delivery(call):
    user_id = int(call.data.split("_")[-1])

    bot.send_message(call.message.chat.id, "✅ Спасибо! Я проверю оплату и напишу вам.")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)


@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def start_reject_reason_input(call):
    try:
        parts = call.data.split("_")
        if len(parts) != 3:
            bot.answer_callback_query(call.id, "❌ Неверный формат данных.")
            return

        _, car_id_str, telegram_id_str = parts
        car_id = int(car_id_str)
        telegram_id = int(telegram_id_str)
        admin_id = call.from_user.id

        # Создаём reject_buffer, если его нет
        global reject_buffer
        if "reject_buffer" not in globals():
            reject_buffer = {}

        reject_buffer[admin_id] = {
            "car_id": car_id,
            "telegram_id": telegram_id,
            "message_chat_id": call.message.chat.id,
            "message_id": call.message.message_id
        }

        bot.answer_callback_query(call.id)
        bot.send_message(admin_id, "✏️ Напишите причину отказа:")

    except Exception as e:
        bot.answer_callback_query(call.id, "Ошибка при начале ввода причины.")
        print(f"[ERROR in start_reject_reason_input]: {e}")


# 👇 Обработка текста причины отказа
@bot.message_handler(func=lambda message: message.from_user.id in globals().get("reject_buffer", {}))
def handle_reject_reason(message):
    admin_id = message.from_user.id
    data = reject_buffer.pop(admin_id, None)

    if not data:
        bot.send_message(admin_id, "⚠️ Данные для отказа не найдены.")
        return

    car_id = data["car_id"]
    telegram_id = data["telegram_id"]
    chat_id = data["message_chat_id"]
    msg_id = data["message_id"]
    reason = message.text.strip()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Сделать машину снова доступной (если car_id > 0)
        if car_id > 0:
            cursor.execute("UPDATE cars SET is_available = 1 WHERE car_id = ?", (car_id,))

        # 2. Удалить заявку по telegram_id и car_id
        cursor.execute("""
            DELETE FROM bookings
            WHERE user_id = ? AND (car_id = ? OR ? = 0)
        """, (telegram_id, car_id, car_id))

        conn.commit()
        conn.close()

        # 3. Уведомляем клиента
        bot.send_message(telegram_id, f"❌ Ваша заявка отклонена.\nПричина: {reason}")

        # 4. Удаляем inline-кнопки
        bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None)

        # 5. Подтверждаем админу
        bot.send_message(admin_id, "✅ Причина отправлена и заявка удалена.")

        # 6. Очистить состояние (если используешь FSM)
        clear_state(admin_id)

    except Exception as e:
        bot.send_message(admin_id, "❌ Ошибка при обработке отказа.")
        print(f"[ERROR in handle_reject_reason]: {e}")

@bot.message_handler(commands=['list_users'])
def list_all_users(message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, phone, name, birthday_date, telegram_id, status, bonus, driver_license_photo FROM users')
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        bot.send_message(message.chat.id, "Список пользователей пуст.")
        return

    text = "Список пользователей:\n\n"
    for row in rows:
        user_id, phone, name, birthday_date, telegram_id, status, bonus, driver_license_photo = row
        text += (f"ID: {user_id}\n"
                 f"Телефон: {phone}\n"
                 f"Имя: {name}\n"
                 f"Дата рождения {birthday_date}\n"
                 f"Telegram ID: {telegram_id}\n"
                 f"Статус: {status}\n"
                 f"Бонус: {bonus}\n\n"
                 f"ВУ: {driver_license_photo}")
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['list_bookings_taxi'])
def list_users(message):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT user_id, name, job, date, time, status FROM bookings_taxi')
    rows = cursor.fetchall()

    if not rows:
        bot.send_message(message.chat.id, "📭 Список заявок пуст.")
        conn.close()
        return

    def translate_status(status):
        return {
            'confirmed': '✅ Подтверждена',
            'pending': '⏳ В ожидании',
            'reject': '❌ Отклонена'
        }.get(status, '❔ Неизвестно')

    text = "📋 <b>Список заявок:</b>\n\n"

    for row in rows:
        user_id, name, job, date, time, status = row

        # Получаем телефон из таблицы user
        cursor.execute('SELECT phone FROM users WHERE telegram_id = ?', (user_id,))
        phone_row = cursor.fetchone()
        phone = phone_row[0] if phone_row else "неизвестно"

        status_text = translate_status(status)

        text += (f"🆔 ID: <code>{user_id}</code>\n"
                 f"👤 ФИО: {name}\n"
                 f"📞 Телефон: {phone}\n"
                 f"🛠️ Заявка на: {job}\n"
                 f"📅 Дата: {date}\n"
                 f"⏰ Время: {time}\n"
                 f"📌 Статус: {status_text}\n\n")

    conn.close()
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['delete_user'])
def delete_user_handler(message):
    if message.chat.id != ADMIN_ID2:
        bot.reply_to(message, "❌ У вас нет доступа к этой команде.")
        return

    # Команда должна идти в формате: /delete_user 79991234567
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "❗ Используйте команду так: /delete_user <номер_телефона>")
        return

    phone_to_delete = parts[1]
    delete_user_from_db(phone_to_delete)
    bot.reply_to(message, f"✅ Пользователь с номером {phone_to_delete} удалён из базы.")


def delete_user_from_db(phone_number):
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE phone = ?", (phone_number,))
    conn.commit()
    conn.close()



@bot.message_handler(commands=['clear_users'])
def clear_users(message):
    # Только для администратора
    if message.from_user.id != ADMIN_ID2:
        bot.send_message(message.chat.id, "❌ У вас нет прав для этой команды.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM users")
        conn.commit()
        bot.send_message(message.chat.id, "🗑️ Таблица пользователей очищена.")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Ошибка при удалении: {e}")
    finally:
        conn.close()

@bot.callback_query_handler(func=lambda call: call.data == "rent")
def handle_rent(call):
    bot.answer_callback_query(call.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("🚗 Смотреть машины", "❓ Вопросы")
    bot.send_message(call.message.chat.id,
                             f"Хорошо а теперь выберите то что вас интересует",
                             reply_markup=markup)




@bot.message_handler(func=lambda message: message.text == "🚗 Смотреть машины")
def handle_show_cars(message):
    # Вызов команды просмотра машин
    choose_service_type(message)

@bot.message_handler(func=lambda message: message.text == "❓ Вопросы")
def handle_show_questions(message):
    # Вызов команды вопросов
    handle_ask_command(message)

@bot.message_handler(commands=['add_user'])
def admin_add_user(message):
    if message.from_user.id not in ADMIN_ID:
        bot.reply_to(message, "⛔ У тебя нет прав для этого!")
        return

    bot.send_message(message.chat.id, "Введите номер телефона нового пользователя:")
    set_state(message.chat.id, "waiting_for_new_user")


@bot.message_handler(func=lambda m: get_state(m.chat.id) == "waiting_for_new_user")
def handle_new_user(message):
    add_user_to_db(message.text.strip())
    bot.send_message(message.chat.id, "✅ Пользователь добавлен.")
    set_state(message.chat.id, None)


@bot.message_handler(commands=['add_car'])
def admin_add_car(message):
    if message.from_user.id not in ADMIN_ID:
        bot.reply_to(message, "⛔ У тебя нет прав для этого!")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Фольцваген Поло", "Шкода Рапид", "Рено Логан", "Шкода Октавия", "Джили Эмгранд")
    bot.send_message(message.chat.id, "Выберите модель автомобиля:", reply_markup=markup)
    set_state(message.chat.id, "admin_add_car_model")


@bot.message_handler(func=lambda m: get_state(m.chat.id) == "admin_add_car_model")
def admin_add_car_model(message):
    session = get_session(message.chat.id)
    model = message.text.strip()
    session["model"] = model

    # Сохраним варианты коробки в сессию
    transmission_options = {
        "Рено Логан": ["Механика"],
        "Фольцваген Поло": ["Механика"],
        "Шкода Октавия": ["Автомат", "Механика"],
        "Шкода Рапид": ["Автомат", "Механика"],
        "Джили Эмгранд": ["Автомат"]
    }

    options = transmission_options.get(model)
    if not options:
        bot.send_message(message.chat.id, "❌ Неизвестная модель автомобиля.")
        return

    session["transmission_options"] = options  # Сохраняем список доступных коробок в сессию

    # Переходим сразу к выбору года
    bot.send_message(message.chat.id, "Выберите год выпуска (с 2015 по 2025):", reply_markup=generate_year_keyboard())
    set_state(message.chat.id, "admin_add_car_year")

@bot.message_handler(func=lambda m: get_state(m.chat.id) == "admin_add_car_year")
def admin_add_car_year(message):
    year = message.text.strip()
    if not year.isdigit() or not (2015 <= int(year) <= 2025):
        bot.send_message(message.chat.id, "❌ Пожалуйста, выберите год из предложенных.")
        return

    session = get_session(message.chat.id)
    session["year"] = year

    # Проверим, нужно ли спрашивать коробку
    if "transmission" not in session:
        options = session.get("transmission_options", [])
        if len(options) == 1:
            session["transmission"] = options[0]
            bot.send_message(message.chat.id, f"✅ Коробка передач: {options[0]}")
        elif options:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(*options)
            bot.send_message(message.chat.id, "Выберите коробку передач:", reply_markup=markup)
            set_state(message.chat.id, "admin_add_car_transmission")
            return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("аренда", "прокат")
    bot.send_message(message.chat.id, "Выберите тип обслуживания:", reply_markup=markup)
    set_state(message.chat.id, "admin_add_car_service")


@bot.message_handler(func=lambda m: get_state(m.chat.id) == "admin_add_car_transmission")
def admin_add_car_transmission(message):
    session = get_session(message.chat.id)
    session["transmission"] = message.text.strip()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("аренда", "прокат")
    bot.send_message(message.chat.id, "Выберите тип обслуживания:", reply_markup=markup)
    set_state(message.chat.id, "admin_add_car_service")

@bot.message_handler(func=lambda m: get_state(m.chat.id) == "admin_add_car_service")
def admin_add_car_service(message):
    session = get_session(message.chat.id)
    user_input = message.text.strip().lower()

    # Карта перевода
    service_map = {
        "аренда": "rent",
        "прокат": "rental"
    }

    service_code = service_map.get(user_input)
    if not service_code:
        bot.send_message(message.chat.id, "❌ Пожалуйста, выберите 'аренда' или 'прокат' из кнопок.")
        return

    session["service"] = service_code

    bot.send_message(message.chat.id, "Введите номер автомобиля (например, 9АНВ45):")
    set_state(message.chat.id, "admin_add_car_id")
@bot.message_handler(func=lambda m: get_state(m.chat.id) == "admin_add_car_id")
def admin_add_car_id(message):
    session = get_session(message.chat.id)
    car_id = message.text.strip().upper()

    if not car_id or len(car_id) < 5:
        bot.send_message(message.chat.id, "❌ Введите корректный номер автомобиля.")
        return

    # Сохраняем car_id в сессию
    session["number"] = car_id

    bot.send_message(message.chat.id, "Отправьте фото машины:")
    set_state(message.chat.id, "admin_add_car_photo")
@bot.message_handler(func=lambda m: get_state(m.chat.id) == "admin_add_car_photo", content_types=['photo'])
def admin_add_car_photo(message):
    session = get_session(message.chat.id)
    photo_id = message.photo[-1].file_id
    session["photo"] = photo_id
    print(session.get("model"))
    # Сохраняем в БД
    conn = sqlite3.connect("cars.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO cars (number, brand_model, year, transmission, photo_url, service)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        session.get("number"),
        session.get("model"),
        session.get("year"),
        session.get("transmission"),
        photo_id,
        session.get("service")
    ))
    conn.commit()
    conn.close()

    # Подтверждение
    text = (
        f"<b>Номер:</b> {session.get('number')}\n"
        f"<b>Модель:</b> {session.get('model')}\n"
        f"<b>Год:</b> {session.get('year')}\n"
        f"<b>Коробка:</b> {session.get('transmission')}\n"
        f"<b>Тип услуги:</b> {session.get('service')}")
    bot.send_message(message.chat.id, f"✅ Машина добавлена:\n\n{text}", parse_mode="HTML")
    bot.send_photo(message.chat.id, photo_id)

    # Очистка сессии
    user_sessions.pop(message.chat.id, None)

@bot.message_handler(commands=['available_cars'])
def choose_service_type(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🚗 Аренда", callback_data="service_rent"),
        types.InlineKeyboardButton("🏁 Прокат", callback_data="service_rental")
    )
    bot.send_message(message.chat.id, "Выберите тип услуги:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("service_"))
def show_available_cars(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    session = get_session(user_id)

    service_key = call.data.split("_")[1]  # rent или rental
    if service_key not in ["rent", "rental"]:
        bot.send_message(chat_id, "❌ Неизвестный тип услуги.")
        bot.answer_callback_query(call.id)
        return

    session["selected_service"] = service_key
    print(f"🔧 Selected service: {service_key}")

    # Подгружаем доступные машины
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT car_id, brand_model, year 
        FROM cars 
        WHERE is_available = 1 AND LOWER(service) = ?
    """, (service_key,))
    cars = cursor.fetchall()
    conn.close()

    if not cars:
        bot.send_message(chat_id, "🚫 Нет доступных машин для выбранной услуги.")
        bot.answer_callback_query(call.id)
        return

    # Показ фильтра если машин больше 5
    service_titles = {
        "rent": "АРЕНДЫ",
        "rental": "ПРОКАТА"
    }

    service_name = service_titles.get(service_key, service_key.upper())  # на случай, если ключ не в словаре

    if len(cars) > 5:
        filter_markup = types.InlineKeyboardMarkup()
        filter_markup.add(types.InlineKeyboardButton("🔎 Фильтр", callback_data="start_filter"))
        bot.send_message(chat_id, f"📋 Машины для: {service_name}", reply_markup=filter_markup)
    else:
        bot.send_message(chat_id, f"📋 Машины для: {service_name}")

    session["car_message_ids"] = []

    for car_id, brand_model, year in cars:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("ℹ️ Подробнее", callback_data=f"details_{car_id}"),
            types.InlineKeyboardButton("🚗 Выбрать", callback_data=f"choose_{car_id}"),
            types.InlineKeyboardButton("💰 Цена", callback_data=f"price_{car_id}")
        )
        sent_msg = bot.send_message(chat_id, f"{brand_model} ({year})", reply_markup=markup)
        session["car_message_ids"].append(sent_msg.message_id)

    bot.answer_callback_query(call.id)
@bot.callback_query_handler(func=lambda call: call.data.startswith(("details_", "choose_", "hide_", "price_")))
def handle_inline(call):
    action, car_id = call.data.split("_", 1)
    car_id = int(car_id)
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    session = get_session(user_id)

    if action == "hide":
        try:
            bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
        except Exception as e:
            print(f"Ошибка удаления сообщения: {e}")
        return

    if action == "price":
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT brand_model, year, service FROM cars WHERE car_id = ?", (car_id,))
        car = cursor.fetchone()
        conn.close()

        if not car:
            bot.send_message(chat_id, "🚫 Машина не найдена.")
            return

        brand_model, year, service = car
        print(service)
        if service == "rent":
            price = TARIFFS.get(service, {}).get(brand_model, {}).get(year)
            if price:
                bot.send_message(chat_id, f"💰 Цена за сутки аренды {brand_model} ({year}) составляет {price}₽.")
            else:
                bot.send_message(chat_id, f"❌ Нет данных о цене аренды для {brand_model} ({year}).")

        elif service == "rental":
            session["awaiting_days_for_car"] = car_id
            bot.send_message(chat_id, f"📅 На сколько дней хотите взять {brand_model}?")
        else:
            bot.send_message(chat_id, "❌ Тип услуги не распознан.")
        return

    # details / choose общая часть: получаем авто
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT brand_model, year, transmission, photo_url FROM cars WHERE car_id = ?",
        (car_id,))
    car = cursor.fetchone()
    conn.close()

    if not car:
        bot.send_message(chat_id, "🚫 Машина не найдена.")
        return

    brand_model, year, gearbox, photo_url = car

    if action == "details":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Скрыть", callback_data=f"hide_{call.message.message_id}"))

        try:
            bot.send_photo(chat_id, photo=photo_url,
                           caption=f"<b>{brand_model}</b> ({year})\n🕹 Коробка: {gearbox}\nГод: {year}",
                           parse_mode="HTML", reply_markup=markup)
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Ошибка при отправке фото: {e}")






    elif action == "choose":

        # Получаем Telegram ID пользователя

        telegram_id = call.from_user.id

        # Проверка: есть ли уже активная аренда у пользователя

        with sqlite3.connect("cars.db") as conn:

            cursor = conn.cursor()

            cursor.execute("SELECT status FROM users WHERE telegram_id = ?", (telegram_id,))

            row = cursor.fetchone()

        if row and row[0] != "new":
            bot.send_message(chat_id, "🚫 У вас уже есть арендованная машина. Сначала завершите текущую аренду.")

            return

        # Продолжение логики выбора машины

        session["car_id"] = car_id

        session["state"] = "waiting_for_photo"

        current_msg_id = call.message.message_id

        for msg_id in session.get("car_message_ids", []):

            if msg_id != current_msg_id:

                try:

                    bot.delete_message(chat_id, msg_id)

                except Exception as e:

                    print(f"Ошибка удаления карточки: {e}")

        session.pop("car_message_ids", None)

        service = session.get("selected_service")

        if not service:
            bot.send_message(chat_id, "Ошибка: не определён тип услуги.")

            return

        user_data.setdefault(user_id, {})["selected_job"] = service

        bot.send_message(chat_id, "📸 Пожалуйста, отправьте фотографию водительского удостоверения.")
# elif service == "rental":
# session["selected_car_id"] = car_id
# session["state"] = "waiting_for_rental_start"
# bot.send_message(chat_id, "Теперь выберите дату для бронирования:",
#                  reply_markup=create_calendar_markup())
@bot.message_handler(func=lambda message: get_session(message.from_user.id).get("awaiting_days_for_car"))
def handle_rental_days(message):
    user_id = message.from_user.id
    session = get_session(user_id)

    try:
        days = int(message.text)
        car_id = int(session["awaiting_days_for_car"])
    except (ValueError, KeyError):
        bot.send_message(message.chat.id, "Введите число дней, например: 3")
        return

    # Получаем модель авто
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT brand_model FROM cars WHERE car_id = ?", (car_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        bot.send_message(message.chat.id, "🚫 Машина не найдена.")
        return

    brand_model = row[0]
    tariffs = TARIFFS.get("Прокат", {}).get(brand_model)

    if not tariffs:
        bot.send_message(message.chat.id, f"❌ Нет тарифов для модели {brand_model}.")
        return

    # Поиск ближайшего тарифа
    best_match = min(tariffs.keys(), key=lambda d: abs(days - d))
    price = tariffs[best_match]

    total = price * days
    bot.send_message(
        message.chat.id,
        f"💰 Цена за {days} дней: {price}₽/сутки\nИтого: {total}₽."
    )

    # Очистка временных данных
    session.pop("awaiting_days_for_car", None)



@bot.callback_query_handler(func=lambda call: call.data.startswith("hide_"))
def hide_message(call):
    try:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        print(f"Ошибка удаления сообщения: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("rental_") or call.data.startswith("rent_"))
def handle_rental_and_rent(call):
    print(f"[DEBUG] callback received: {call.data}")
    action, car_id = call.data.split("_", 1)
    car_id = int(car_id)
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    session = get_session(user_id)

    if action == "rental":
        session["selected_car_id"] = car_id
        session["state"] = "waiting_for_rental_start"

        bot.send_message(chat_id, "Теперь выберите дату для бронирования:",
                         reply_markup=create_calendar_markup())

    elif action == "rent":
        session["selected_car_id"] = car_id

        bot.answer_callback_query(call.id)
        show_user_calendar(call.message, car_id, user_id)

def show_user_calendar(message, car_id, user_id):
    from datetime import datetime, timedelta
    chat_id = message.chat.id
    session = get_session(user_id)

    # Русские месяцы в родительном падеже
    MONTH_NAMES_RU_GEN = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)

    today = datetime.today()
    buttons = []

    for i in range(30):
        day = today + timedelta(days=i)
        day_num = day.day
        month_name = MONTH_NAMES_RU_GEN[day.month - 1]
        button_text = f"{day_num} {month_name}"  # Пример: "21 июля"
        buttons.append(types.KeyboardButton(button_text))

    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i + 3])

    service = user_data.get(user_id, {}).get("selected_job")
    session["state"] = f"waiting_for_time_selection|{service}|{car_id}"

    bot.send_message(chat_id, "📅 Выберите дату встречи:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rental_days_"))
def rental_days_selected(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    session = get_session(user_id)

    try:
        days = int(call.data.split("_")[-1])
    except ValueError:
        bot.answer_callback_query(call.id, "Некорректное значение дней.")
        return

    model = session.get("model")
    tariffs = TARIFFS.get("Прокат", {}).get(model)

    if not tariffs:
        bot.answer_callback_query(call.id, "Ошибка расчёта.")
        return

    price_per_day = tariffs.get(days)
    if price_per_day:
        total_price = price_per_day * days

        session["price_per_day"] = price_per_day
        session["days"] = days
        session["total_price"] = total_price

        bot.send_message(chat_id, f"Стоимость проката {model} на {days} дней:\n\n💰 {total_price} ₽")

        car_id = session.get("selected_car_id")
        if not car_id:
            bot.send_message(chat_id, "Ошибка: машина не выбрана.")
            bot.answer_callback_query(call.id)
            return

        show_user_rental_calendar(call.message, car_id, user_id)

        session["state"] = "waiting_for_rental_date"
    else:
        bot.send_message(chat_id, "Не удалось рассчитать стоимость.")

    bot.answer_callback_query(call.id)

# ➤ Обработка ответа на вопрос "Нужна ли доставка?"
@bot.message_handler(func=lambda message: get_state(message.from_user.id) == "waiting_for_delivery_choice")
def handle_final_confirmation(message):
    import sqlite3
    user_id = message.from_user.id
    print(user_id)
    chat_id = message.chat.id
    choice = message.text.strip().lower()
    session = get_session(user_id)

    if choice == "да":
        car_id = session.get("car_id")
        price = session.get("price")
        rent_start = session.get("rent_start")
        rent_end = session.get("rent_end")
        db_user_id = session.get("db_user_id")
        print(db_user_id, car_id, rent_start, rent_end, price)
        if not all([car_id, price, rent_start, rent_end, db_user_id]):
            missing = []
            if not car_id: missing.append("car_id")
            if not price: missing.append("price")
            if not rent_start: missing.append("rent_start")
            if not rent_end: missing.append("rent_end")
            if not db_user_id: missing.append("db_user_id")
            bot.send_message(chat_id, f"❌ Ошибка: отсутствуют данные: {', '.join(missing)}")
            return

        # Сохраняем аренду
        with sqlite3.connect("cars.db") as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO rental_history (user_id, car_id, rent_start, rent_end, price)
                VALUES (?, ?, ?, ?, ?)
            ''', (db_user_id, car_id, rent_start, rent_end, price))
            conn.commit()
            print("✅ Данные вставлены в rental_history!")
        # Переход к выбору времени
        date_str = rent_start.split()[0]  # YYYY-MM-DD
        service = "rental"

        set_state(user_id, f"waiting_for_time_pick|{service}|{car_id}|{date_str}")
        bot.send_message(chat_id, "✅ Отлично! Теперь выберите удобное время получения авто:",
                         reply_markup=create_time_markup_calendar(date_str, car_id))

        # Очистка лишнего
        for key in ["car_id", "price", "rent_start_str", "rent_end_str", "db_user_id"]:
            session.pop(key, None)

    elif choice == "нет":
        bot.send_message(chat_id, "Хорошо, давайте выберем дату начала заново.")
        set_state(user_id, "waiting_for_rental_start")
        bot.send_message(chat_id, "📅 Укажите новую дату начала проката:",
                         reply_markup=create_calendar_markup())

    else:
        bot.send_message(chat_id, "Пожалуйста, выберите 'Да' или 'Нет'.")


def create_time_markup_calendar(date_str, car_id):
    from telebot import types
    import sqlite3

    markup = types.InlineKeyboardMarkup(row_width=3)
    conn = sqlite3.connect("cars.db")
    cursor = conn.cursor()

    cursor.execute("SELECT time FROM bookings WHERE date = ? AND car_id = ?", (date_str, car_id))
    booked = set(row[0][:5] for row in cursor.fetchall() if row[0])
    print(f"[DEBUG] Занятые слоты: {booked}")

    conn.close()

    for hour in range(10, 24):  # с 10:00 до 19:59
        for minute in range(0, 60, 10):
            time_str = f"{hour:02}:{minute:02}"
            if time_str not in booked:
                callback_data = f"select_time|rental|{car_id}|{date_str}|{time_str}"
                markup.add(types.InlineKeyboardButton(time_str, callback_data=callback_data))

    return markup

@bot.message_handler(func=lambda message: message.text == "Написать адрес")
def ask_for_address(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    session = get_session(user_id)

    car_id = session.get("selected_car_id")
    if not car_id:
        bot.send_message(chat_id, "❌ Ошибка: не выбрана машина.")
        return

    bot.send_message(chat_id, "Пожалуйста, напишите адрес вашего местоположения.")
    bot.register_next_step_handler(message, lambda m: receive_location(m, car_id))

# Обработчик получения местоположения
@bot.message_handler(content_types=['location'])
def handle_location(message):
    location = message.location
    lat, lon = location.latitude, location.longitude
    chat_id = message.chat.id
    user_id = message.from_user.id

    bot.send_message(chat_id, "Ваша геолокация получена.")

    try:
        address = geolocator.reverse((lat, lon), language='ru')
        if address:
            address_text = address.address
            distance_km = geodesic(OFFICE_COORDS, (lat, lon)).km
            delivery_price = round(distance_km * 100)

            session = get_session(user_id)
            session.update({
                "delivery_address": address_text,
                "delivery_price": delivery_price
            })

            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton('да', callback_data="destination_next"),
                types.InlineKeyboardButton('нет', callback_data="return_location")
            )
            bot.send_message(chat_id, f"Ваш адрес: {address_text}. \nВсё верно?", reply_markup=markup)
        else:
            bot.send_message(chat_id, "Адрес не найден.")
    except GeocoderTimedOut:
        bot.send_message(chat_id, "Время запроса вышло.")

@bot.callback_query_handler(func=lambda call: call.data == "destination_next")
def handle_destination_next(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    session = get_session(user_id)  # Получаем сессию пользователя

    # Проверяем, что в сессии есть все нужные данные
    if not session.get('delivery_address') or not session.get('delivery_price') or not session.get('car_id'):
        bot.send_message(chat_id, "⚠ Не удалось найти адрес. Повторите ввод.")
        return

    car_id = session['car_id']

    # Сохраняем состояние в сессии
    session['state'] = f"waiting_for_meeting_date_{car_id}"
    save_session(user_id, session)  # Сохраняем сессию (ваша функция)

    show_user_rental_calendar(call.message, car_id, chat_id)


def receive_location(message, car_id):
    user_id = message.from_user.id
    session = get_session(user_id)

    destination = message.text
    chat_id = message.chat.id

    bot.send_message(chat_id, f"Вы указали: {destination}. Сейчас найдём координаты...")

    try:
        location = geolocator.geocode(destination)
        if not location:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("Написать адрес"))
            bot.send_message(chat_id, "Адрес не найден. Попробуйте снова", reply_markup=markup)
            return

        lat, lon = location.latitude, location.longitude
        address = geolocator.reverse((lat, lon), language='ru')

        if address:
            address_text = address.address
            distance_km = geodesic(OFFICE_COORDS, (lat, lon)).km
            delivery_price = round(distance_km * 100)

            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton('Да', callback_data=f"meeting_next_{car_id}"),
                types.InlineKeyboardButton('Нет', callback_data="return_location")
            )

            bot.send_message(
                chat_id,
                f"Ваш адрес: {address_text}\n"
                f"Расстояние до офиса: {distance_km:.2f} км\n"
                f"Стоимость доставки: 💸 {delivery_price} ₽\n\nВсё верно?",
                reply_markup=markup
            )

            # Сохраняем данные в сессию
            session['delivery_address'] = address_text
            session['delivery_price'] = delivery_price
            session['car_id'] = car_id

        else:
            bot.send_message(chat_id, "Не удалось определить адрес.")
    except GeocoderTimedOut:
        bot.send_message(chat_id, "Время запроса вышло.")




@bot.message_handler(commands=['history'])
def show_rental_history(message):
    user_id = message.chat.id
    history = get_rental_history(user_id)
    user_id = int(user_id)
    if not history:
        bot.send_message(message.chat.id, "У вас нет истории аренды.")
        return

    history_text = "Ваша история аренды:\n"
    for record in history:
        car_id, rent_start, rent_end, price = record
        car_id = int(car_id)


        # Вы можете дополнительно использовать car_id, чтобы получить информацию о машине
        history_text += f"\nМашина: {car_id} | Начало: {rent_start} | Конец: {rent_end} | Цена: {price}"

    bot.send_message(message.chat.id, history_text)


# --- Админ-панель для удаления машин ---
@bot.message_handler(commands=['delete_car'])
def admin_panel(message):
    if message.from_user.id not in ADMIN_ID:
        bot.reply_to(message, " У тебя нет прав для этого!")
        return

    cursor.execute('SELECT id, brand || " " || model FROM cars')
    cars = cursor.fetchall()

    if not cars:
        bot.send_message(message.chat.id, " Нет машин для удаления.")
        return

    for car_id, brand_model in cars:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f" Удалить {brand_model}", callback_data=f"delete_{car_id}"))
        bot.send_message(message.chat.id, brand_model, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def delete_car(call):
    if call.from_user.id not in ADMIN_ID:
        bot.answer_callback_query(call.id, " Нет прав!")
        return

    car_id = int(call.data.split('_')[1])
    cursor.execute('DELETE FROM cars WHERE id = ?', (car_id,))
    conn.commit()
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="\u2705 Машина удалена.")
    bot.answer_callback_query(call.id, "Удалено!")


# --- Фильтрация по диапазону годов ---
@bot.callback_query_handler(func=lambda call: call.data == 'По году')
def year_range_filter(call):
    bot.send_message(call.message.chat.id, "Введите диапазон годов в формате: `2015-2020`", parse_mode="Markdown")
    bot.register_next_step_handler(call.message, process_year_range)


def process_year_range(message):
    try:
        start_year, end_year = map(int, message.text.split('-'))
        cursor.execute('SELECT id, brand || " " || model, year FROM cars WHERE year BETWEEN ? AND ?',
                       (start_year, end_year))
        cars = cursor.fetchall()

        if not cars:
            bot.send_message(message.chat.id, "\ud83d\ude97 Нет машин в этом диапазоне годов.")
            return

        for car in cars:
            car_id, brand_model, year = car
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("\u2139\ufe0f Подробнее", callback_data=f"details_{car_id}"))
            markup.add(types.InlineKeyboardButton("\ud83d\ude97 Арендовать", callback_data=f"rent_{car_id}"))
            bot.send_message(message.chat.id, f"{brand_model} ({year})", reply_markup=markup)

    except Exception as e:
        bot.send_message(message.chat.id, "\u26a0\ufe0f Неверный формат. Попробуйте снова: `2015-2020`",
                         parse_mode="Markdown")

@bot.message_handler(commands=['clear_cars'])
def clear_cars(message):
    if message.from_user.id not in ADMIN_ID:
        bot.reply_to(message, "⛔ У тебя нет прав для этого!")
        return

    try:
        conn = sqlite3.connect("cars.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cars")
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Таблица машин успешно очищена.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при очистке: {e}")


@bot.message_handler(commands=['list_cars'])
def list_all_cars(message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, brand_model, year, transmission, drive, car_number, photo_url, is_available FROM cars")
    cars = cursor.fetchall()
    conn.close()

    if not cars:
        bot.send_message(message.chat.id, "Машин пока нет.")
    else:
        msg = "🚘 Все автомобили:\n"
        for c in cars:
            status = "Свободна" if c[7] else "Занята"
            car_number = c[5]
            msg += f"{c[0]}. {c[1]} {c[2]} {c[3]} {c[4]} — {status}\nНомер: {car_number}\n\n"
        bot.send_message(message.chat.id, msg)


TARIFFS = {
    "Аренда": {
        "Рено Логан": {2017: 1700, 2018: 1750, 2019: 1800, 2020: 1900, 2021: 1950},
        "Фольцваген Поло": {2018: 2100, 2019: 2200},
        "Шкода Рапид": {2016: 2000, 2018: 2100},
        "Шкода Октавия": {2017: 2900, 2019: 2900, 2020: 3100},
        "Джили Эмгранд": {2023: 2900},
    },
    "Прокат": {
        "Рено Логан": {1: 2400, 7: 2300, 14: 2200, 30: 2100},
        "Джили Эмгранд": {1: 3400, 7: 3300, 14: 3200, 30: 3100},
    }
}


# --- КОМАНДА /calculate ---
@bot.message_handler(commands=['calculate'])
def calculate_command(message):
    user_id = message.from_user.id
    session = get_session(user_id)

    session.clear()  # очищаем предыдущую сессию, если была
    set_state(user_id, "calculate_model")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Рено Логан", "Фольцваген Поло", "Шкода Рапид", "Шкода Октавия")
    bot.send_message(message.chat.id, "Выберите модель автомобиля:", reply_markup=markup)


@bot.message_handler(func=lambda message: get_state(message.from_user.id) == "calculate_model")
def calculate_model(message):
    user_id = message.from_user.id
    session = get_session(user_id)

    session['model'] = message.text.strip()
    set_state(user_id, "calculate_service")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Аренда", "Прокат", "Выкуп")
    bot.send_message(message.chat.id, "Выберите услугу:", reply_markup=markup)


@bot.message_handler(func=lambda message: get_state(message.from_user.id) == "calculate_service")
def calculate_service(message):
    user_id = message.from_user.id
    session = get_session(user_id)

    service = message.text.strip()
    session["service"] = service

    if service == "Прокат":
        model = session.get("model")
        tariffs = TARIFFS.get("Прокат", {}).get(model)
        if not tariffs:
            bot.send_message(message.chat.id, "Нет данных по этой машине для проката.")
            user_sessions.pop(user_id, None)
            return

        markup = types.InlineKeyboardMarkup()
        for days, price in sorted(tariffs.items()):
            markup.add(types.InlineKeyboardButton(f"{days} дней — {price}₽/день", callback_data=f"rental_days_{days}"))
        bot.send_message(message.chat.id, "Выберите срок проката:", reply_markup=markup)

    else:
        bot.send_message(message.chat.id, "Введите год автомобиля (например, 2019):")
        set_state(user_id, "calculate_year")


@bot.message_handler(func=lambda message: get_state(message.from_user.id) == "calculate_year")
def calculate_year(message):
    user_id = message.from_user.id
    session = get_session(user_id)

    try:
        year = int(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите действительный год (цифры).")
        return

    model = session.get("model")
    service = session.get("service")

    if service == "Аренда":
        price = TARIFFS.get("Аренда", {}).get(model, {}).get(year)
        if price:
            bot.send_message(message.chat.id, f"Стоимость аренды {model} {year} года: {price} ₽/день.")
        else:
            bot.send_message(message.chat.id, "Нет данных для выбранного года.")
    elif service == "Выкуп":
        data = TARIFFS.get("Выкуп", {}).get(model, {}).get(year)
        if data:
            price_per_day = data["price_per_day"]
            months = data["months"]
            total_days = months * 30
            total_price = price_per_day * total_days
            bot.send_message(message.chat.id, f"Стоимость выкупа {model} {year} года:\n\n"
                                              f"{price_per_day} ₽/день × {total_days} дней = {total_price} ₽ за весь срок.")
        else:
            bot.send_message(message.chat.id, "Нет данных по этой машине для выкупа.")

    user_sessions.pop(user_id, None)  # очистка после завершения расчета


@bot.callback_query_handler(func=lambda call: call.data.startswith("rental_days_"))
def rental_days_selected(call):
    user_id = call.from_user.id
    session = get_session(user_id)

    try:
        days = int(call.data.split("_")[-1])
    except ValueError:
        bot.answer_callback_query(call.id, "Неверный формат.")
        return

    model = session.get("model")
    tariffs = TARIFFS.get("Прокат", {}).get(model)

    if not tariffs:
        bot.answer_callback_query(call.id, "Ошибка расчета.")
        return

    price_per_day = tariffs.get(days)
    if price_per_day:
        total_price = price_per_day * days
        bot.send_message(call.message.chat.id, f"Стоимость проката {model} на {days} дней:\n\n💰 {total_price} ₽")
    else:
        bot.send_message(call.message.chat.id, "Не удалось рассчитать стоимость.")

    bot.answer_callback_query(call.id)
    user_sessions.pop(user_id, None)




@bot.callback_query_handler(func=lambda call: call.data == "start_filter")
def start_filtering(call):
    user_id = call.from_user.id
    session = get_session(user_id)

    if "selected_service" not in session:
        bot.send_message(call.message.chat.id, "❌ Сначала выберите тип услуги.")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("По году", "По марке-модели")
    markup.add("🔙 Назад")
    bot.send_message(call.message.chat.id, "Выберите тип фильтра:", reply_markup=markup)
    set_state(user_id, "filter_select")

@bot.message_handler(func=lambda m: get_state(m.from_user.id) == "filter_select")
def filter_select(message):
    user_id = message.from_user.id

    if message.text.strip() == "🔙 Назад":
        # Вернуться к выбору услуги
        return choose_service_type(message)

    session = get_session(user_id)
    session["filter_type"] = message.text.strip()
    set_state(user_id, "filter_value")

    if message.text.strip() == "По году":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("2017", "2018", "2019", "2020", "2021", "2022", "2023")
        markup.add("🔙 Назад")
        bot.send_message(message.chat.id, "Выберите год:", reply_markup=markup)

    elif message.text.strip() == "По марке-модели":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Шкода Рапид", "Рено Логан", "Шкода Октавия")
        markup.add("Фольцваген Поло", "Джили Эмгранд")
        markup.add("🔙 Назад")
        bot.send_message(message.chat.id, "Выберите марку и модель:", reply_markup=markup)

@bot.message_handler(func=lambda m: get_state(m.from_user.id) == "filter_value")
def filter_value(message):
    user_id = message.from_user.id

    if message.text.strip() == "🔙 Назад":
        set_state(user_id, "filter_select")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("По году", "По марке-модели")
        markup.add("🔙 Назад")
        bot.send_message(message.chat.id, "Выберите тип фильтра:", reply_markup=markup)
        return

    session = get_session(user_id)
    filter_type = session.get("filter_type")
    value = message.text.strip()

    filter_map = {
        "По году": "year",
        "По марке-модели": "brand_model"
    }

    field = filter_map.get(filter_type)
    if not field:
        bot.send_message(message.chat.id, "❌ Некорректный фильтр!")
        return

    if "selected_service" not in session:
        bot.send_message(message.chat.id, "❌ Сначала выберите тип услуги.")
        return

    try:
        print(field, value, session["selected_service"])
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT car_id, brand_model, year 
            FROM cars 
            WHERE {field} = ? AND is_available = 1 AND LOWER(service) = ?
        """, (value, session["selected_service"]))
        cars = cursor.fetchall()
        conn.close()

        bot.send_message(message.chat.id, "🔍 Результаты поиска:", reply_markup=types.ReplyKeyboardRemove())

        if not cars:
            bot.send_message(message.chat.id, "🚫 Машин не найдено.")
        else:

            for car_id, brand_model, year in cars:
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton("ℹ️ Подробнее", callback_data=f"details_{car_id}"),
                    types.InlineKeyboardButton("🚗 Выбрать", callback_data=f"choose_{car_id}"),
                    types.InlineKeyboardButton("💰 Цена", callback_data=f"price_{car_id}")
                )
                bot.send_message(user_id, f"{brand_model} ({year})", reply_markup=markup)
        back_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        back_markup.add("🔙 Назад")
        bot.send_message(message.chat.id, "Нажмите 'Назад', чтобы вернуться к фильтрам.", reply_markup=back_markup)

    except Exception as e:
        bot.send_message(message.chat.id, f"❗️ Ошибка фильтрации: {str(e)}")





@bot.message_handler(commands=['profile'])
def profile_command(message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.brand_model, r.rent_start
        FROM rentals r
        JOIN cars c ON c.car_id = r.car_id
        WHERE r.user_id = ?
        ORDER BY r.rent_start DESC
    """, (message.from_user.id,))
    rentals = cursor.fetchall()
    conn.close()

    if not rentals:
        bot.send_message(message.chat.id, "У тебя пока нет аренд.")
        return

    text = "🚗 Твои аренды:\n\n"
    for car, start in rentals:
        date = datetime.datetime.fromisoformat(start).strftime("%d.%m.%Y %H:%M")
        text += f"• {car} с {date}\n"

    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['edit_car'])
def edit_car(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "Нет доступа.")

    user_id = message.from_user.id
    session = get_session(user_id)

    session.clear()
    set_state(user_id, "edit_car_id")

    bot.send_message(message.chat.id, "Введите ID машины для редактирования:")


@bot.message_handler(func=lambda m: get_state(m.from_user.id) == "edit_car_id")
def edit_car_id(message):
    user_id = message.from_user.id
    session = get_session(user_id)

    session["edit_id"] = message.text.strip()
    set_state(user_id, "edit_car_field")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Марка и модель", "Год", "Двигатель", "Коробка", "Расход", "Привод")

    bot.send_message(message.chat.id, "Что изменить?", reply_markup=markup)


@bot.message_handler(func=lambda m: get_state(m.from_user.id) == "edit_car_field")
def edit_car_field(message):
    user_id = message.from_user.id
    session = get_session(user_id)

    session["edit_field"] = message.text.strip()
    set_state(user_id, "edit_car_value")

    bot.send_message(message.chat.id, "Введите новое значение:")


@bot.message_handler(func=lambda m: get_state(m.from_user.id) == "edit_car_value")
def edit_car_value(message):
    user_id = message.from_user.id
    session = get_session(user_id)

    field_map = {
        "Марка и модель": "brand_model",
        "Год": "year",
        "Двигатель": "engine",
        "Коробка": "gearbox",
        "Расход": "consumption",
        "Привод": "drive"
    }

    field_key = session.get("edit_field")
    car_id = session.get("edit_id")
    new_value = message.text.strip()
    db_field = field_map.get(field_key)

    if not db_field or not car_id:
        bot.send_message(message.chat.id, "❌ Ошибка данных. Попробуйте снова.")
        user_sessions.pop(user_id, None)
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"UPDATE cars SET {db_field} = ? WHERE id = ?", (new_value, car_id))
        conn.commit()
        conn.close()

        bot.send_message(message.chat.id, f"✅ Обновлено: {db_field} → {new_value}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при обновлении: {str(e)}")

    # Очистить сессию после завершения
    user_sessions.pop(user_id, None)

    # --- ЗАПУСК ---






# --- Обработчик команды /view_questions ---
@bot.message_handler(commands=['view_questions'])
def view_questions(message):
    if message.from_user.id not in ADMIN_ID:
        bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")
        return

    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, question_text, answer_text, answered FROM questions")
    questions = cursor.fetchall()
    conn.close()

    if not questions:
        bot.send_message(message.chat.id, "Нет вопросов в базе данных.")
        return

    response = "Список вопросов:\n"
    for question in questions:
        question_id, username, question_text, answer_text, answered = question
        response += f"\n{question_id}. @{username}:\n{question_text}\n"
        response += f"Ответ: {'Не дан' if not answered else answer_text}\n{'---' * 5}"

    bot.send_message(message.chat.id, response)


@bot.message_handler(commands=['delete_question'])
def delete_question(message):
    if message.from_user.id not in ADMIN_ID:
        bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")
        return

    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, question_text, answer_text, answered FROM questions")
    questions = cursor.fetchall()
    conn.close()

    if not questions:
        bot.send_message(message.chat.id, "Нет вопросов для удаления.")
        return

    for question in questions:
        question_id, username, question_text, answer_text, answered = question
        text = f"<b>ID:</b> {question_id}\n<b>От:</b> @{username or 'без имени'}\n<b>Вопрос:</b> {question_text}\n<b>Ответ:</b> {answer_text if answered else '❌ Ещё нет ответа'}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🗑 Удалить", callback_data=f"delq_{question_id}"))
        bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)



@bot.callback_query_handler(func=lambda call: call.data.startswith("delq_"))
def handle_delete_question(call):
    if call.from_user.id not in ADMIN_ID:
        bot.answer_callback_query(call.id, "Нет доступа.")
        return

    question_id = int(call.data.split("_")[1])
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
    conn.commit()
    conn.close()

    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text="✅ Вопрос удалён.")


@bot.message_handler(commands=['delete_all_question'])
def delete_questions(message):
    if message.from_user.id not in ADMIN_ID:
        bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")
        return

    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()

    # Удаляем таблицу
    cursor.execute('DROP TABLE IF EXISTS questions')

    # Пересоздаём таблицу
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            question_text TEXT,
            answer_text TEXT,
            answered BOOLEAN
        )
    ''')

    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, "✅ Все вопросы удалены, таблица пересоздана.")

@bot.message_handler(commands=['reset_bookings'])
def handle_reset_bookings(message):
    if message.from_user.id == ADMIN_ID2:  # Проверка на админа
        reset_bookings_table()
        bot.reply_to(message, "✅ Таблица `bookings` сброшена.")
    else:
        bot.reply_to(message, "🚫 У вас нет доступа к этой команде.")


def reset_bookings_table():
    try:
        conn = sqlite3.connect('cars.db')
        cursor = conn.cursor()

        # Удаляем таблицу, если она существует
        cursor.execute("DROP TABLE IF EXISTS bookings")

        # Создаём заново
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                car_id INTEGER NOT NULL,
                service TEXT NOT NULL,            -- 'rent' или 'rental'
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT DEFAULT 'pending',   -- pending, confirmed, rejected
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notified INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (car_id) REFERENCES cars(car_id)
            )
        ''')

        conn.commit()
        print("✅ Таблица bookings сброшена и создана заново.")
    except Exception as e:
        print(f"❌ Ошибка при сбросе таблицы: {e}")
    finally:
        conn.close()

@bot.message_handler(commands=['delete_user'])
def delete_user_handler(message):
    if message.chat.id not in ADMIN_ID:
        bot.reply_to(message, "❌ У вас нет доступа к этой команде.")
        return

    # Команда должна идти в формате: /delete_user 79991234567
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "❗ Используйте команду так: /delete_user <номер_телефона>")
        return

    phone_to_delete = parts[1]
    delete_user_from_db(phone_to_delete)
    bot.reply_to(message, f"✅ Пользователь с номером {phone_to_delete} удалён из базы.")

@bot.message_handler(commands=['list_users'])
def list_users_handler(message):
    if message.chat.id not in ADMIN_ID:
        bot.reply_to(message, "❌ У вас нет доступа к этой команде.")
        return

    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("SELECT phone, name, telegram_id, status FROM users")
    users = cursor.fetchall()
    conn.close()

    if not users:
        bot.reply_to(message, "Пользователей в базе нет.")
        return

    status_map = {
        "new": "🚫 нет машины",
        "awaiting_use": "📄 оформление",
        "using_car": "✅ есть машина"
    }

    text = "📋 Список пользователей:\n"
    for phone, name, telegram_id, status in users:
        display_name = name if name else "без имени"
        status_display = status_map.get(status, f"❓ {status}")
        text += f"📞 +{phone} — {display_name}, статус: {status_display}\n"

    bot.send_message(message.chat.id, text)
@bot.message_handler(commands=['view_bookings'])
def view_bookings(message):
    user_id = message.from_user.id

    if user_id != ADMIN_ID2:
        bot.send_message(user_id, "⛔ У вас нет доступа к этой команде.")
        return

    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
            b.id, 
            u.name, 
            c.brand_model, 
            b.date, 
            b.time, 
            b.status,
            b.service,
            b.user_id,
            b.car_id
        FROM bookings b
        JOIN users u ON b.user_id = u.id      -- исправлено
        JOIN cars c ON b.car_id = c.car_id
        ORDER BY b.date, b.time
    ''')
    bookings = cursor.fetchall()
    print(bookings)
    cursor.execute('SELECT * FROM bookings')
    rows = cursor.fetchall()
    print("[DEBUG] Из таблицы bookings:", rows)
    if not bookings:
        bot.send_message(user_id, "📭 Нет запланированных встреч.")
        conn.close()
        return

    text = "📅 <b>Список встреч:</b>\n\n"

    for booking in bookings:
        booking_id, name, car_model, date, time, status, service, user_id_db, car_id_db = booking
        name = html.escape(name)
        car_model = html.escape(car_model)
        service_display = "Аренда" if service == "rent" else "Прокат"

        status_display = '✅ Подтверждена' if status == 'confirmed' else '⏳ В ожидании'

        delivery_info = ""
        if service == 'rental':
            cursor.execute('''
                SELECT delivery_address, delivery_price
                FROM rental_history
                WHERE user_id = ? AND car_id = ?
                ORDER BY id DESC
                LIMIT 1
            ''', (user_id_db, car_id_db))
            rental = cursor.fetchone()
            if rental:
                address, price = rental
                if address:
                    # Сокращаем адрес до улицы и дома
                    address_parts = address.split(',')
                    short_address = ', '.join(address_parts[:2]).strip()
                    address_short = html.escape(short_address)

                    # Экранируем цену
                    try:
                        price_clean = f"{int(price):,}".replace(',', ' ')
                    except:
                        price_clean = str(price)

                    price_clean = html.escape(price_clean)

                    delivery_info = (
                        f"🏠 Адрес: {address_short}\n"
                        f"💵 Доставка: <b>{price_clean} ₽</b>\n"
                    )
                    status_display = "⏳ В ожидании доставки"
                else:
                    status_display = '✅ Подтверждена (самовывоз)'

        text += (
            f"<b>🔹 #{booking_id}</b>\n"
            f"👤 Клиент: <i>{name}</i>\n"
            f"🚗 Машина: {car_model}\n"
            f"🛠 Услуга: <b>{service_display}</b>\n"
            f"📅 Дата: <b>{date}</b>\n"
            f"🕒 Время: <b>{time}</b>\n"
            f"📍 Статус: {status_display}\n"
            f"{delivery_info}\n"
        )

    conn.close()

    MAX_LEN = 4096
    for i in range(0, len(text), MAX_LEN):
        bot.send_message(user_id, text[i:i+MAX_LEN], parse_mode="HTML")



def notify_admin():
    now = datetime.now()
    current_date = now.strftime('%Y-%m-%d')
    print(f"[notify_admin] Поиск встреч: текущая дата и время: {now}")

    matches = []

    # 🔹 Получаем обычные записи из bookings (включая 'rental')
    with db_lock:
        with sqlite3.connect('cars.db', timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT b.id, u.name, u.telegram_id, c.brand_model, b.date, b.time, b.service, b.car_id
                FROM bookings b
                JOIN users u ON b.user_id = u.telegram_id
                JOIN cars c ON b.car_id = c.car_id
                WHERE b.status = 'confirmed' AND b.date = ? AND b.notified = 0
            ''', (current_date,))
            bookings = cursor.fetchall()

    print(f"[notify_admin] Получено записей: {len(bookings)}")

    for booking in bookings:
        booking_id, name, user_id, car_model, date_str, time_str, service, car_id = booking
        booking_datetime_str = f"{date_str} {time_str}"

        try:
            booking_dt = datetime.strptime(booking_datetime_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                booking_dt = datetime.strptime(booking_datetime_str, '%Y-%m-%d %H:%M')
            except ValueError:
                continue

        if now <= booking_dt <= now + timedelta(minutes=5):
            match = {
                "id": booking_id,
                "name": name,
                "user_id": user_id,
                "car_model": car_model,
                "date": date_str,
                "time": time_str,
                "service": service,
                "source": "bookings"
            }

            # Если это аренда — пробуем найти rent_end
            if service == "rental":
                with db_lock:
                    with sqlite3.connect('cars.db', timeout=10) as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            SELECT rent_end
                            FROM rental_history
                            WHERE user_id = ?
                              AND car_id = ?
                              AND DATE(rent_start) = ?
                            ORDER BY rent_start DESC
                            LIMIT 1
                        ''', (user_id, car_id, date_str))
                        rental_row = cursor.fetchone()

                if rental_row:
                    match["end_date"] = rental_row[0]
                else:
                    print(f"[notify_admin] ⚠️ Не найден end_date для проката из bookings: {match}")
            matches.append(match)

    # 🔹 Получаем аренду из rental_history напрямую
    with db_lock:
        with sqlite3.connect('cars.db', timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT rh.id, u.name, u.telegram_id, c.brand_model, rh.rent_start, rh.rent_end
                FROM rental_history rh
                JOIN users u ON rh.user_id = u.telegram_id
                JOIN cars c ON rh.car_id = c.car_id
            ''')
            rental_bookings = cursor.fetchall()

    for rental in rental_bookings:
        rental_id, name, user_id, car_model, rent_start_str, rent_end_str = rental
        try:
            rent_start = datetime.strptime(rent_start_str, '%Y-%m-%d %H:%M')
        except ValueError:
            continue

        if now <= rent_start <= now + timedelta(minutes=5):
            matches.append({
                "id": rental_id,
                "name": name,
                "user_id": user_id,
                "car_model": car_model,
                "date": rent_start_str.split()[0],
                "time": rent_start.strftime('%H:%M'),
                "end_date": rent_end_str,
                "service": "rental",
                "source": "rental_history"
            })
    with db_lock:
        with sqlite3.connect('cars.db', timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT rh.id, u.name, u.telegram_id, c.brand_model, rh.rent_end
                FROM rental_history rh
                JOIN users u ON rh.user_id = u.telegram_id
                JOIN cars c ON rh.car_id = c.car_id
            ''')
            rentals = cursor.fetchall()

    now = datetime.now().replace(second=0, microsecond=0)

    for rental_id, name, telegram_id, car_model, rent_end_str in rentals:
        try:
            rent_end = datetime.strptime(rent_end_str, "%Y-%m-%d %H:%M").replace(second=0, microsecond=0)
        except ValueError:
            continue

        # Если прямо сейчас момент возврата
        if now == rent_end:
            message = (
                f"⏰ Сейчас клиент <b>{html.escape(name)}</b> должен сдать авто <b>{html.escape(car_model)}</b>."
            )
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("🚘 Машина получена", callback_data=f"car_returned_{rental_id}")
            )
            bot.send_message(ADMIN_ID2, message, parse_mode="HTML", reply_markup=markup)
    print(f"[notify_admin] Найдено записей в интервале: {len(matches)}")

    # 🔹 Отправка уведомлений
    for match in matches:
        try:
            booking_id = match["id"]
            name = match["name"]
            user_id = match["user_id"]
            car_model = match["car_model"]
            service = match["service"]
            date_str = match["date"]
            time_str = match["time"]

            if service == "rental" and match.get("source") == "bookings":
                end_date_str = match.get("end_date")

                # Если end_date отсутствует — попробуем найти в rental_history
                if not end_date_str:
                    with db_lock:
                        with sqlite3.connect('cars.db', timeout=10) as conn:
                            cursor = conn.cursor()
                            cursor.execute('''
                                SELECT rent_end FROM rental_history
                                WHERE user_id = ? AND car_id = (
                                    SELECT car_id FROM cars WHERE brand_model = ?
                                ) AND DATE(rent_start) = ?
                                ORDER BY id DESC LIMIT 1
                            ''', (user_id, car_model, date_str))
                            result = cursor.fetchone()
                            if result:
                                end_date_str = result[0]
                            else:
                                print(f"[notify_admin] ⚠️ Не удалось найти end_date в rental_history: {match}")
                                continue  # Пропускаем, если всё ещё нет даты

                message = (
                    f"📣 <b>Начало аренды!</b>\n\n"
                    f"🔹 <b>#{booking_id}</b>\n"
                    f"👤 Клиент: {html.escape(name)}\n"
                    f"🚗 Машина: {html.escape(car_model)}\n"
                    f"📅 Срок: <b>{date_str} ➝ {end_date_str}</b>\n"
                    f"🕒 Время начала: <b>{time_str}</b>\n"
                )
            else:
                message = (
                    f"📣 <b>Время встречи!</b>\n\n"
                    f"🔹 <b>#{booking_id}</b>\n"
                    f"👤 Клиент: {html.escape(name)}\n"
                    f"🚗 Машина: {html.escape(car_model)}\n"
                    f"🛠 Услуга: <b>{service}</b>\n"
                    f"📅 Дата: <b>{date_str}</b>\n"
                    f"🕒 Время: <b>{time_str}</b>\n"
                )

            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("✅ Сделка состоялась", callback_data=f"deal_success_{booking_id}_{user_id}"),
                InlineKeyboardButton("❌ Не состоялась", callback_data=f"deal_fail_{booking_id}_{user_id}")
            )

            bot.send_message(ADMIN_ID2, message, parse_mode="HTML", reply_markup=markup)
            print(f"[notify_admin] Уведомление отправлено: {booking_id}")

            # Обновляем статус уведомления только для bookings
            if match.get("source") == "bookings":
                with db_lock:
                    with sqlite3.connect('cars.db', timeout=10) as conn:
                        conn.execute('UPDATE bookings SET notified = 1 WHERE id = ?', (booking_id,))
                        conn.commit()

        except Exception as e:
            print(f"[notify_admin] ❌ Ошибка при обработке записи: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("car_returned_"))
def handle_car_returned(call):
    rental_id = call.data.split("_")[2]

    try:
        with db_lock:
            with sqlite3.connect("cars.db", timeout=10) as conn:
                cursor = conn.cursor()

                # Получаем аренду
                cursor.execute('''
                    SELECT user_id, car_id
                    FROM rental_history
                    WHERE id = ?
                ''', (rental_id,))
                result = cursor.fetchone()

                if not result:
                    bot.answer_callback_query(call.id, "❌ Запись не найдена.")
                    return

                user_id, car_id = result

                # Освобождаем машину
                cursor.execute('''
                    UPDATE cars SET is_available = 1 WHERE car_id = ?
                ''', (car_id,))

                # Обновляем статус пользователя (если есть поле `status`)
                cursor.execute('''
                    UPDATE users SET status = 'new' WHERE telegram_id = ?
                ''', (user_id,))

                # Можно также удалить или пометить завершённую аренду (если нужно)
                # cursor.execute('DELETE FROM rental_history WHERE id = ?', (rental_id,))
                # или: cursor.execute('UPDATE rental_history SET completed = 1 WHERE id = ?', (rental_id,))

                conn.commit()

        bot.edit_message_text(
            "✅ Машина успешно возвращена и пользователь переведён в статус 'new'.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )

    except Exception as e:
        print(f"[handle_car_returned] Ошибка: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при обновлении.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("deal_"))
def handle_deal_result(call):
    try:
        parts = call.data.split("_")
        if len(parts) != 4:
            raise ValueError("Неверный формат callback_data")

        _, result, booking_id, user_id = parts
        booking_id = int(booking_id)
        user_id = int(user_id)

        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Получим car_id до любых операций с ним
            cursor.execute('SELECT car_id FROM bookings WHERE id = ?', (booking_id,))
            car_row = cursor.fetchone()
            car_id = car_row[0] if car_row else None

            # Обновим статус машины — вернём её в список доступных
            if car_id:
                cursor.execute('UPDATE cars SET is_available = 1 WHERE car_id = ?', (car_id,))

            # Удалим бронирование
            #cursor.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))

            # Если это прокат с доставкой, удалим историю
            # if car_id:
            #     cursor.execute('DELETE FROM rental_history WHERE user_id = ? AND car_id = ?', (user_id, car_id))

            conn.commit()
            conn.close()

        # Уведомление пользователю
        if result == "success":
            feedback_markup = InlineKeyboardMarkup()
            feedback_markup.add(
                InlineKeyboardButton("😕 Не очень", callback_data=f"feedback_bad_{user_id}"),
                InlineKeyboardButton("🙂 Пойдёт", callback_data=f"feedback_ok_{user_id}"),
                InlineKeyboardButton("🤩 Отлично", callback_data=f"feedback_good_{user_id}")
            )
            bot.send_message(user_id, "🎉 Отлично! Как прошла встреча?", reply_markup=feedback_markup)

        elif result == "fail":
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 Вернуться к выбору машины", callback_data="back_to_cars"))
            bot.send_message(
                user_id,
                "😔 Понимаем, что-то пошло не так. Что случилось?",
                reply_markup=markup
            )
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE cars SET is_available = 1 WHERE car_id = ?', (car_id,))
            conn.commit()
            conn.close()
        # Уведомление админа
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.answer_callback_query(call.id, "Заявка завершена.")

    except Exception as e:
        bot.answer_callback_query(call.id, f"Ошибка обработки: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("feedback_"))
def handle_feedback(call):
    try:
        print(f"Получен callback_data: {call.data}")  # лог

        parts = call.data.split("_")
        if len(parts) != 3:
            raise ValueError("Неверный формат callback_data")

        _, feedback_type, user_id = parts
        user_id = int(user_id)

        feedback_map = {
            "bad": ("😕 Спасибо за отзыв. Мы постараемся стать лучше!", 1),
            "ok": ("🙂 Рад, что всё прошло неплохо!", 2),
            "good": ("🤩 Здорово, что всё понравилось! Спасибо!", 3)
        }

        feedback_text, score = feedback_map.get(feedback_type, ("Спасибо за отзыв!", 2))
        print(f"Вставка в feedback: user_id={user_id}, score={score}")
        # Сохраняем в БД
        conn = sqlite3.connect('cars.db', timeout=10)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")  # включаем WAL

        cursor.execute('''
            INSERT INTO feedback (user_id, feedback_type, score)
            VALUES (?, ?, ?)
        ''', (user_id, feedback_type, score))
        cursor.execute('UPDATE users SET status = ? WHERE telegram_id = ?', ('awaiting_use', user_id))
        conn.commit()
        conn.close()

        # Убираем кнопки
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

        # Отвечаем
        start_use_kb = types.InlineKeyboardMarkup()
        start_use_kb.add(types.InlineKeyboardButton("🚀 Начать использование машины", callback_data="start_use"))

        bot.send_message(user_id, feedback_text)
        bot.send_message(user_id, "Нажмите кнопку ниже, чтобы начать использование автомобиля:",
                         reply_markup=start_use_kb)

    except Exception as e:
        print(f"Ошибка в handle_feedback: {e}")
        try:
            bot.answer_callback_query(call.id, f"Ошибка: {str(e)[:40]}")  # telegram ограничивает длину
        except:
            pass
@bot.callback_query_handler(func=lambda c: c.data == "start_use")
def start_use_handler(callback_query):
    user_id = callback_query.from_user.id

    # Удалим последние 100 сообщений (без async — мы используем TeleBot)
    for i in range(100):
        try:
            bot.delete_message(chat_id=user_id, message_id=callback_query.message.message_id - i)
        except:
            continue  # Игнорируем ошибки

    # Обновим статус
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = ? WHERE telegram_id = ?", ('using_car', user_id))
    conn.commit()
    conn.close()

    bot.send_message(user_id, "✅ Машина передана! Введите /start для получения доступа к функциям.")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_cars")
def handle_back_to_cars(call):

    chat_id = call.message.chat.id
    print(f"[DEBUG] chat_id for sending cars: {chat_id}")
    bot.answer_callback_query(call.id)
    send_available_cars(chat_id)
    print(f"[DEBUG] chat_id for sending cars: {chat_id}")
def send_available_cars(chat_id):
    if not isinstance(chat_id, int):
        print(f"[ERROR] Неверный chat_id: {chat_id} ({type(chat_id)})")
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    print(chat_id)
    cursor.execute("SELECT car_id, brand_model, year FROM cars WHERE is_available = 1")
    cars = cursor.fetchall()
    conn.close()

    if not cars:
        bot.send_message(chat_id, "Нет свободных машин.")  # Используем chat_id
        return

    for car in cars:
        car_id, brand_model, year = car
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("ℹ️ Подробнее", callback_data=f"details_{car_id}"))
        markup.add(types.InlineKeyboardButton("🚗 Выбрать", callback_data=f"choose_{car_id}"))
        bot.send_message(chat_id, f"{brand_model} ({year})", reply_markup=markup)

@bot.message_handler(commands=['raw_rental_history'])
def show_raw_rental_history(message):
    import sqlite3

    try:
        conn = sqlite3.connect('cars.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM rental_history ORDER BY id DESC")
        rows = cursor.fetchall()

        if not rows:
            bot.send_message(message.chat.id, "📋 Таблица rental_history пуста.")
            return

        for row in rows:
            text = (
                f"🧾 Аренда #{row['id']}\n"
                f"👤 user_id: {row['user_id']}\n"
                f"🚘 car_id: {row['car_id']}\n"
                f"📅 rent_start: {row['rent_start']}\n"
                f"📅 rent_end: {row['rent_end']}\n"
                f"💰 price: {row['price']}\n"
                f"🚚 delivery_price: {row['delivery_price']}\n"
                f"📍 delivery_address: {row['delivery_address']}"
            )

            bot.send_message(message.chat.id, text)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")
    finally:
        conn.close()
@bot.message_handler(commands=['rental_history'])
def show_rental_history(message):
    import sqlite3

    user_telegram_id = message.from_user.id
    chat_id = message.chat.id

    try:
        conn = sqlite3.connect('cars.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Получение ID пользователя
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (user_telegram_id,))
        user = cursor.fetchone()

        if not user:
            bot.send_message(chat_id, "❌ Пользователь не найден.")
            return

        user_id = user["id"]

        # Получение истории аренд
        cursor.execute('''
            SELECT h.id, h.car_id, c.brand_model, c.year, h.rent_start, h.rent_end,
                   h.price, h.delivery_price, h.delivery_address
            FROM rental_history h
            JOIN cars c ON h.car_id = c.car_id
            WHERE h.user_id = ?
            ORDER BY h.id DESC
        ''', (user_id,))

        rentals = cursor.fetchall()

        if not rentals:
            bot.send_message(chat_id, "📋 У вас пока нет истории аренд.")
            return

        for rental in rentals:
            text = (
                f"<b>📄 Аренда #{rental['id']}</b>\n"
                f"🚘 <b>Авто:</b> {rental['brand_model']} ({rental['year']})\n"
                f"🆔 <b>car_id:</b> {rental['car_id']}\n"
                f"📆 <b>Период:</b> {rental['rent_start']} – {rental['rent_end']}\n"
                f"💰 <b>Цена:</b> {rental['price']:,} ₽"
            )

            if rental["delivery_price"] and rental["delivery_address"]:
                text += (
                    f"\n🚚 <b>Доставка:</b> {rental['delivery_price']:,} ₽"
                    f"\n📍 <b>Адрес:</b> {rental['delivery_address']}"
                )

            bot.send_message(chat_id, text, parse_mode="HTML")

    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при получении истории аренд: {e}")
    finally:
        conn.close()


@bot.message_handler(commands=['feedback_stats'])
def feedback_stats(message):
    if message.from_user.id != ADMIN_ID2:
        return bot.send_message(message.chat.id, "⛔ У вас нет доступа к этой команде.")

    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*), AVG(score) FROM feedback')
    total, avg = cursor.fetchone()
    conn.close()

    if total == 0:
        bot.send_message(message.chat.id, "Пока нет ни одного отзыва.")
    else:
        avg_text = f"{avg:.2f}".replace('.', ',')
        bot.send_message(message.chat.id, f"📝 Всего отзывов: <b>{total}</b>\n⭐ Средняя оценка: <b>{avg_text} / 3</b>", parse_mode="HTML")

@bot.message_handler(commands=['users'])
def handle_users_command(message):
    conn = sqlite3.connect("cars.db")  # Замените на имя вашей базы данных
    cursor = conn.cursor()

    cursor.execute("SELECT id, phone, name, telegram_id, status FROM users")
    users = cursor.fetchall()

    if not users:
        bot.send_message(message.chat.id, "❗️Пользователи не найдены.")
        conn.close()
        return

    text = "📋 Список пользователей:\n\n"

    for user in users:
        user_id, phone, name, telegram_id, status = user
        user_info = (
            f"🆔 ID: {user_id}\n"
            f"📱 Телефон: {phone}\n"
            f"👤 Имя: {name}\n"
            f"💬 Telegram ID: {telegram_id}\n"
            f"📌 Статус: {status}\n"
        )

        if status == 'using_car':
            # Получаем подтвержденное бронирование
            cursor.execute('''
                SELECT car_id, service, date, time, status
                FROM bookings
                WHERE user_id = ? AND status = 'confirmed'
                ORDER BY created_at DESC
                LIMIT 1
            ''', (user_id,))
            booking = cursor.fetchone()

            if booking:
                car_id, service, date, time, booking_status = booking

                # Получаем данные об авто
                cursor.execute('''
                    SELECT brand_model, year
                    FROM cars
                    WHERE car_id = ?
                ''', (car_id,))
                car = cursor.fetchone()

                if car:
                    model, year = car
                    user_info += f"🚗 Машина: {model} ({year})\n"
                else:
                    user_info += f"🚗 Машина: ID {car_id} (информация не найдена)\n"

                user_info += (
                    f"🔧 Сервис: {service}\n"
                    f"📅 Дата: {date}\n"
                    f"⏰ Время: {time}\n"
                    f"✅ Статус брони: {booking_status}\n"
                )

                # Если аренда через 'rental', получаем данные из rental_history
                if service == 'rental':
                    cursor.execute('''
                        SELECT rent_start, rent_end, price, delivery_price, delivery_address
                        FROM rental_history
                        WHERE user_id = ? AND car_id = ?
                        ORDER BY id DESC
                        LIMIT 1
                    ''', (user_id, car_id))
                    rental = cursor.fetchone()

                    if rental:
                        rent_start, rent_end, price, delivery_price, delivery_address = rental
                        user_info += (
                            f"📆 Аренда с: {rent_start} по {rent_end}\n"
                            f"💰 Стоимость: {price} ₽\n"
                        )
                        if delivery_price:
                            user_info += f"🚚 Доставка: {delivery_price} ₽\n"
                        if delivery_address:
                            user_info += f"📍 Адрес доставки: {delivery_address}\n"
                    else:
                        user_info += "⚠️ Инфо об аренде не найдена\n"

            else:
                user_info += "⚠️ Бронирование не найдено\n"

        text += user_info + "\n"

    conn.close()

    # Отправляем текст частями, если он большой
    for i in range(0, len(text), 4000):
        bot.send_message(message.chat.id, text[i:i+4000])





















import sqlite3
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

@bot.message_handler(commands=['set_status'])
def set_status_command(message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) != 2:
        return bot.send_message(message.chat.id, "Использование: /set_status <status>")

    new_status = args[1]

    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = ? WHERE telegram_id = ?", (new_status, user_id))
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, f"✅ Ваш статус обновлён на: {new_status}")


def show_main_menu(chat_id, edit_message_id=None):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("Профиль", callback_data="menu_profile"),
        types.InlineKeyboardButton("Помощь", callback_data="menu_help"),
        types.InlineKeyboardButton("Заправки", callback_data="menu_fuel"),
        types.InlineKeyboardButton("Смотреть авто", callback_data="menu_cars"),
        types.InlineKeyboardButton("Заказать такси", callback_data="taxi")
    )

    if edit_message_id:
        bot.edit_message_text("Выберите что вам хочется", chat_id, edit_message_id, reply_markup=kb)
    else:
        bot.send_message(chat_id, "Выберите что вам хочется", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def handle_main_menu_inline(call):
    data = call.data.replace("menu_", "")

    if data == "profile":
        send_profile_info(call.from_user.id, call.message.chat.id)
    elif data == "help":
        send_help_menu(call.message)
    elif data == "fuel":
        handle_gas(call)
    elif data == "cars":
        choose_service_type(call.message)  # передаём message, а не chat_id

    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


def send_profile_info(user_telegram_id, chat_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    print(user_telegram_id)
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (user_telegram_id,))
    user = cursor.fetchone()

    if not user:
        bot.send_message(chat_id, "❌ Пользователь не найден.")
        return

    user_id = user[0]
    print(user_id)
    cursor.execute('''
        SELECT b.car_id, c.brand_model, c.year, c.transmission,
               b.service, b.date, b.time
        FROM bookings b
        JOIN cars c ON b.car_id = c.car_id
        WHERE b.user_id = ? AND b.status = 'confirmed'
        ORDER BY b.created_at DESC
        LIMIT 1
    ''', (user_telegram_id,))
    booking = cursor.fetchone()

    if booking:
        car_id, brand_model, year, trans, service, date, time = booking
        rent_start = date  # дата аренды
        rent_end = date    # по умолчанию, но ниже можно будет заменить
        print(car_id)
        # Если прокат — ищем период в rental_history
        if service == "rental":
            cursor.execute('''
                SELECT rent_start, rent_end FROM rental_history
                WHERE user_id = ? AND car_id = ?
                ORDER BY id DESC LIMIT 1
            ''', (user_telegram_id, car_id))
            rent_info = cursor.fetchone()
            print(rent_info)
            if rent_info:
                rent_start, rent_end = rent_info

        total_price = calculate_rent_price(service, brand_model, year, rent_start, rent_end)
        price_line = f"\n💰 <b>Стоимость:</b> {total_price:,} ₽ в день" if total_price else ""

        if service == "rent":
            date_line = f"📆 Дата начала: {rent_start}"
        else:
            date_line = f"📆 Срок: {rent_start} - {rent_end}"

        text = (
            f"<b>Условия аренды:</b>\n"
            f"{date_line}\n\n"

            f"<b>Характеристики автомобиля:</b>\n"
            f"🚘 {brand_model} ({year})\n"
            f"🕹 Коробка: {trans}\n"
            f"{price_line}"
        )

        bot.send_message(chat_id, text, parse_mode="HTML")
    else:
        bot.send_message(chat_id, "❌ Вы пока не арендуете машину.")

    conn.close()

def calculate_rent_price(service, brand_model, year, rent_start, rent_end):
    if service == "rent":
        tariff_group = TARIFFS.get("Аренда", {})
        model_tariffs = tariff_group.get(brand_model, {})
        return model_tariffs.get(int(year))

    elif service == "rental":
        start = datetime.strptime(rent_start, "%Y-%m-%d")
        end = datetime.strptime(rent_end, "%Y-%m-%d")
        days = (end - start).days
        if days <= 0:
            return None

        tariff_group = TARIFFS.get("Прокат", {}).get(brand_model, {})
        best_match_price = None
        for min_days, price_per_day in sorted(tariff_group.items(), reverse=True):
            if days >= min_days:
                best_match_price = days * price_per_day
                break
        return best_match_price

    elif service == "buyout":
        tariff_group = TARIFFS.get("Выкуп", {}).get(brand_model, {})
        data = tariff_group.get(int(year))
        if data:
            return data["price_per_day"] * data["months"] * 30
    return None


def send_help_menu(message):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("Ремонт", callback_data="help_repair"),
        types.InlineKeyboardButton("Записаться на мойку", callback_data="help_wash"),
        types.InlineKeyboardButton("ДТП", callback_data="help_accident"),
        types.InlineKeyboardButton("Задать админу вопрос", callback_data="help_question"),
    )
    bot.send_message(message.chat.id, "🛠Выберите вариант помощи:", reply_markup=kb)
temp_data = {}

@bot.message_handler(commands=['clear_rental_history'])
def clear_rental_history(message):
    if message.from_user.id != ADMIN_ID2:
        bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")
        return

    try:
        conn = sqlite3.connect('cars.db')
        cursor = conn.cursor()

        cursor.execute("DELETE FROM rental_history")
        conn.commit()

        bot.send_message(message.chat.id, "✅ История аренд успешно очищена.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при очистке истории аренд: {e}")
    finally:
        conn.close()
@bot.callback_query_handler(func=lambda call: call.data == "help_accident")
def handle_help_accident(call):
    chat_id = call.message.chat.id

    # 1. Сообщение с телефоном
    bot.send_message(chat_id, "📞 Телефон экстренной помощи: +79297107180")

    # 2. Кнопка с инструкцией
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📹 Как правильно снять видео", callback_data="accident_video_guide"))

    bot.send_message(chat_id, "Если ты попал в ДТП, пожалуйста, ознакомься с инструкцией ниже:", reply_markup=markup)

# 3. Обработка кнопки-инструкции
@bot.callback_query_handler(func=lambda call: call.data == "accident_video_guide")
def handle_video_guide(call):
    chat_id = call.message.chat.id

    instruction = (
        "📹 *Инструкция по съёмке места ДТП:*\n\n"
        "1. Снимите общую сцену с разных сторон.\n"
        "2. Покажите номера автомобилей.\n"
        "3. Запишите повреждения крупным планом.\n"
        "4. Зафиксируйте дорожные знаки, разметку, перекрестки.\n"
        "5. Важно: чтобы видео было *чётким и без пауз*.\n\n"
        "После съёмки — отправьте видео прямо сюда."
    )

    bot.send_message(chat_id, instruction, parse_mode="Markdown")
# Обработка входящего видео

@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_id = message.from_user.id

    # Подключение к базе данных
    conn = sqlite3.connect('cars.db')  # Укажи правильный путь к БД
    cursor = conn.cursor()

    # Поиск имени и телефона по telegram_id
    cursor.execute("SELECT name, phone FROM users WHERE telegram_id = ?", (user_id,))
    result = cursor.fetchone()

    if result:
        full_name, phone = result
    else:
        full_name, phone = "Неизвестный пользователь", "Телефон не найден"

    # Текст сообщения админу
    caption = (
        f"📹 Получено видео ДТП\n"
        f"👤 Имя: {full_name}\n"
        f"📱 Телефон: {phone}\n"
        f"🆔 Telegram ID: {user_id}"
    )

    try:
        # Отправляем админу
        bot.send_message(ADMIN_ID2, caption)
        bot.forward_message(ADMIN_ID2, message.chat.id, message.message_id)

        # Ответ пользователю
        bot.send_message(message.chat.id, "Спасибо, видео получено! Мы передали его специалистам. 🚗✅")
    except Exception as e:
        print(f"Ошибка при отправке сообщения админу: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при обработке. Попробуйте позже.")

    conn.close()
@bot.callback_query_handler(func=lambda call: call.data == "help_repair")
def show_repair_options(call):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📅 Записаться на ремонт", callback_data="repair_book"),
        types.InlineKeyboardButton("📞 Связаться с механиком", callback_data="repair_contact"),
        types.InlineKeyboardButton("📘 Инструкция по уходу за авто", callback_data="repair_guide"),
        types.InlineKeyboardButton("🛠 Сообщить о поломке", callback_data="report_breakdown")
    )
    bot.edit_message_text("🔧 Выберите опцию ремонта:", chat_id=call.message.chat.id,
                          message_id=call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "repair_guide")
def send_repair_guide(call):
    chat_id = call.message.chat.id

    guide_text = (
        "🛠 <b>Инструкция по уходу и обслуживанию автомобиля</b>\n\n"
        "Правильный уход за автомобилем — залог его надёжной работы, безопасности и экономии на ремонте.\n"
        "Наша компания предоставляет <b>бесплатный доступ</b> к <b>собственному СТО и автомойке</b>. "
        "Вы можете записаться через бота или связаться с поддержкой.\n\n"

        "<b>🔧 Регулярное обслуживание</b>\n"
        "• Замена масла и фильтров каждые 5 000–10 000 км\n"
        "• Контроль тормозной системы и жидкостей\n"
        "• Проверка аккумулятора и охлаждающей жидкости\n\n"

        "<b>🚗 Уход за кузовом</b>\n"
        "• Мойка автомобиля 1–2 раза в неделю\n"
        "• Полировка — 2 раза в год\n"
        "• Уход за стёклами и дисками\n\n"

        "<b>🧼 Уход за салоном</b>\n"
        "• Пылесос и чистка обивки\n"
        "• Протирка панели и элементов управления\n"
        "• Обработка кондиционера и замена фильтров\n\n"

        "<b>🌦 Сезонное обслуживание</b>\n"
        "• Зима: замена шин, проверка антифриза и АКБ\n"
        "• Лето: проверка кондиционера, тормозов, замена масла\n\n"

        "<b>🔍 Самостоятельно можно:</b>\n"
        "• Проверять масло и давление в шинах\n"
        "• Доливать стеклоомыватель и менять щётки\n\n"

        "❗ Если слышите шумы, вибрации, видите протечки или ошибки на панели — <b>обратитесь в СТО</b>.\n\n"
        "📞 Для записи используйте кнопку «📅 Записаться на ремонт» в меню или напишите в поддержку."
    )

    # Кнопка возврата
    buttons = types.InlineKeyboardMarkup(row_width=1)
    buttons.add(
        types.InlineKeyboardButton("📅 Записаться на СТО", callback_data="repair_book"),
        types.InlineKeyboardButton("🧼 Записаться на мойку", callback_data="help_wash"),
        types.InlineKeyboardButton("⬅️ Назад", callback_data="help_repair")
    )

    bot.send_message(chat_id, guide_text, parse_mode="HTML", reply_markup=buttons)
@bot.callback_query_handler(func=lambda call: call.data == "repair_contact")
def send_mechanic_contact(call):
    bot.send_message(call.message.chat.id,
                     "📞 Позвоните механику по номеру: +79991234567")
def get_last_confirmed_car_id(user_id):
    cursor.execute('''
        SELECT b.car_id, c.brand_model, c.year, c.transmission
        FROM bookings b
        JOIN cars c ON b.car_id = c.car_id
        WHERE b.user_id = ? AND b.status = 'confirmed'
        ORDER BY b.created_at DESC
        LIMIT 1
    ''', (user_id,))
    return cursor.fetchone()  # вернёт (car_id, brand_model, year, transmission) или None

def send_time_selection(chat_id, service, car_id, date_str):
    booked_times = get_booked_times(date_str)
    markup = types.InlineKeyboardMarkup(row_width=3)
    has_available = False

    for hour in range(10, 19):  # с 10:00 до 18:00
        time_str = f"{hour:02}:00"
        if time_str not in booked_times:
            has_available = True
            callback_data = f"chosen_time_{service}_{car_id}_{date_str}_{time_str}"
            markup.add(types.InlineKeyboardButton(time_str, callback_data=callback_data))

    if not has_available:
        bot.send_message(chat_id, "⏰ Все слоты на выбранную дату заняты, выберите другую дату.")
        return False
    else:
        bot.send_message(chat_id, "⏰ Выберите удобное время:", reply_markup=markup)
        return True

def get_booked_times(date_str):
    conn = sqlite3.connect('cars.db')
    c = conn.cursor()
    c.execute("""
        SELECT time FROM bookings
        WHERE date = ? AND status = 'confirmed'
    """, (date_str,))
    booked_times = set(t[0] for t in c.fetchall())
    conn.close()
    return booked_times

def get_repair_booked_dates_and_times():
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("SELECT date, time FROM repair_bookings")
    booked_dates_and_times = cursor.fetchall()
    conn.close()
    return booked_dates_and_times

def get_connection():
    # timeout=10 даёт время ждать, если база занята
    return sqlite3.connect(DB_PATH, timeout=10)

def execute_query(query, params=(), fetchone=False, commit=False):
    with db_lock:
        with sqlite3.connect('cars.db', timeout=10) as conn:
            c = conn.cursor()
            c.execute(query, params)
            if commit:
                conn.commit()
            if fetchone:
                return c.fetchone()
            return c.fetchall()

@bot.callback_query_handler(func=lambda call: call.data == "report_breakdown")
def report_breakdown(call):
    chat_id = call.message.chat.id

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    issues = [
        ("🔋 Машина не заводится", "issue_not_starting"),
        ("🛞 Пробито колесо", "issue_flat_tire"),
        ("🛠️ Странный шум", "issue_noise"),
        ("🚫 Не работают тормоза", "issue_brakes"),
        ("💨 Кондиционер не работает", "issue_ac"),
        ("⚙️ Check Engine / Ошибка на панели", "issue_check_engine"),
        ("🧾 Другое", "issue_other")
    ]

    for text, callback in issues:
        keyboard.add(types.InlineKeyboardButton(text, callback_data=callback))

    bot.edit_message_text("🚨 Выберите проблему с автомобилем:", chat_id=chat_id,
                          message_id=call.message.message_id, reply_markup=keyboard)

# Ответы на конкретные поломки
BREAKDOWN_RESPONSES = {
    "issue_not_starting": "🔋 Пожалуйста, проверьте, что автомобиль в 'P' и тормоз зажат. Механик уже уведомлён.",
    "issue_flat_tire": "🛞 Понял, спасибо! Мы свяжемся с вами и заменим колесо при первой возможности.",
    "issue_noise": "🛠️ Спасибо, мы зафиксировали жалобу. Наши специалисты проверят автомобиль.",
    "issue_brakes": "🚫 Это серьёзно. Пожалуйста, не продолжайте движение. Механик будет направлен к вам.",
    "issue_ac": "💨 Уведомили техслужбу. Кондиционер будет проверен при следующем ТО.",
    "issue_check_engine": "⚙️ Спасибо. Индикатор ошибки записан. Мы свяжемся с вами при необходимости.",
}

# Обработчик кнопок поломок
@bot.callback_query_handler(func=lambda call: call.data.startswith("issue_"))
def handle_issue_selected(call):
    issue_code = call.data
    user_name = call.from_user.first_name
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if issue_code == "issue_other":
        msg = bot.send_message(chat_id, "📝 Опишите проблему с автомобилем:")
        bot.register_next_step_handler(msg, handle_question)
        return

    # Автоматический ответ пользователю
    response = BREAKDOWN_RESPONSES.get(issue_code, "🚧 Проблема зарегистрирована.")
    bot.send_message(chat_id, response)

    # Описание для админа
    issue_text = dict([
        ("issue_not_starting", "🔋 Машина не заводится"),
        ("issue_flat_tire", "🛞 Пробито колесо"),
        ("issue_noise", "🛠️ Странный шум"),
        ("issue_brakes", "🚫 Не работают тормоза"),
        ("issue_ac", "💨 Не работает кондиционер"),
        ("issue_check_engine", "⚙️ Check Engine / Ошибка на панели")
    ])[issue_code]

    # Кнопка для ответа админу
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✉️ Ответить", callback_data=f"reply_{user_id}"))

    bot.send_message(
        ADMIN_ID2,
        f"❗ Поломка от {user_name}:\n{issue_text}",
        reply_markup=markup
    )

# Обработка "другое"
def handle_question(message):
    if message.from_user.id == ADMIN_ID:
        return  # Игнорируем сообщения от самого админа

    user_id = message.from_user.id
    username = message.from_user.username or "пользователь"
    question = message.text.strip()

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✉ Ответить", callback_data=f"broke_answer_{user_id}"))

    bot.send_message(ADMIN_ID3, f"❓ Вопрос от @{username} (ID: {user_id}):\n{question}", reply_markup=markup)
    bot.send_message(user_id, "✅ Ваш вопрос отправлен администратору. Ожидайте ответа.")

# Обработка кнопки "Ответить"
@bot.callback_query_handler(func=lambda call: call.data.startswith("broke_answer_"))
def handle_answer_button(call):
    if call.from_user.id != ADMIN_ID3:
        bot.answer_callback_query(call.id, "⛔ Нет доступа.")
        return

    user_id = int(call.data.split("_")[2])  # третий элемент — user_id

    msg = bot.send_message(call.message.chat.id, "✍ Введите ответ пользователю:")
    bot.register_next_step_handler(msg, send_answer_to_user, user_id)

# Отправка ответа пользователю
def send_answer_to_user(message, user_id):
    try:
        user_id = int(user_id)
        print(f"➡️ Отправка ответа пользователю: {user_id}")
        bot.send_message(user_id, f"📩 Ответ администратора на поломку:\n{message.text}")
        bot.send_message(message.chat.id, "✅ Ответ отправлен пользователю.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Не удалось отправить ответ: {e}")
        print(f"❌ Ошибка отправки пользователю {user_id}: {e}")
@bot.callback_query_handler(func=lambda call: call.data == "repair_book")
def handle_repair_book(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    start_repair_request(user_id, chat_id, call.message)  # Передаем call.message для register_next_step_handler

def start_repair_request(user_id, chat_id, message):
    print("User ID:", user_id)
    booking = get_last_confirmed_car_id(user_id)

    if booking is None:
        bot.send_message(chat_id, "❌ У вас нет подтверждённых бронирований автомобиля. Сначала забронируйте машину.")
        return

    car_id, brand_model, year, transmission = booking
    temp_data[chat_id] = {'car_id': car_id}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    today = datetime.today()
    buttons = []

    for i in range(30):
        day = today + timedelta(days=i)
        day_num = day.day
        month_name = MONTH_NAMES_RU_GEN[day.month - 1]
        button_text = f"{day_num} {month_name}"  # Пример: "21 июля"
        buttons.append(types.KeyboardButton(button_text))

    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i + 3])

    bot.send_message(
        chat_id,
        f"🚗 Ремонт автомобиля {brand_model} {year} ({transmission})\n📅 Выберите дату встречи:",
        reply_markup=markup
    )
    bot.register_next_step_handler(message, get_repair_date)


def get_repair_date(message):
    date_raw = message.text.strip()
    parsed = parse_russian_date(date_raw)
    if not parsed:
        bot.send_message(message.chat.id, "❌ Неверный формат даты. Пожалуйста, выберите дату с клавиатуры.")
        bot.register_next_step_handler(message, get_repair_date)
        return

    date_str = parsed.strftime('%Y-%m-%d')  # сохранить как ISO
    temp_data[message.chat.id]['date'] = date_str
    car_id = temp_data[message.chat.id]['car_id']

    # Отправляем инлайн-клавиатуру с выбором времени
    service = 'repair'
    if not send_time_selection(message.chat.id, service, car_id, date_str):
        bot.send_message(message.chat.id, "⛔ Нет доступных времён на этот день. Попробуйте выбрать другую дату.")
        bot.register_next_step_handler(message, get_repair_date)


@bot.callback_query_handler(func=lambda call: call.data.startswith('chosen_time'))
def callback_select_time(call):
    parts = call.data.split('_', 5)  # максимум 6 элементов
    if len(parts) != 6:
        bot.answer_callback_query(call.id, "❌ Некорректный формат данных.")
        return

    _, _, service, car_id, date_str, time_str = parts
    chat_id = call.message.chat.id

    if chat_id not in temp_data:
        temp_data[chat_id] = {}
    temp_data[chat_id].update({
        'service': service,
        'car_id': int(car_id),
        'date': date_str,
        'time': time_str
    })

    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)
    bot.send_message(chat_id, f"✅ Вы выбрали дату {date_str} и время {time_str}.\nОформляем заявку...")

    conn = get_db_connection()
    cursor = conn.cursor()

    user_id = call.from_user.id
    cursor.execute("SELECT id, name FROM users WHERE telegram_id = ?", (user_id,))
    user_row = cursor.fetchone()
    if not user_row:
        bot.send_message(chat_id, "⚠️ Вы не зарегистрированы. Нажмите /start.")
        return

    user_id_db, name = user_row
    cursor.execute("SELECT brand_model, year FROM cars WHERE car_id=?", (car_id,))
    car = cursor.fetchone()

    cursor.execute('''
        INSERT INTO repair_bookings (user_id, car_id, service, date, time, status)
        VALUES (?, ?, ?, ?, ?, 'pending')
    ''', (user_id_db, int(car_id), service, date_str, time_str))
    conn.commit()
    conn.close()

    bot.send_message(chat_id, "✅ Ваша заявка на ремонт принята и ожидает подтверждения.")
    temp_data.pop(chat_id, None)
    encoded_date = urllib.parse.quote(date_str)  # "20%20Jun"
    encoded_time = urllib.parse.quote(time_str)  # "18%3A00"


    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Принять",
                                   callback_data = f"repair_approve_{car_id}_{user_id_db}_{encoded_date}_{encoded_time}"),
        types.InlineKeyboardButton("🕒 Предложить другое время",
                                   callback_data=f"repair_suggest_{car_id}_{user_id_db}"),
    )
    markup.add(
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"repair_reject_{car_id}_{user_id_db}_{encoded_date}_{encoded_time}"),
    )

    if car:
        brand_model, year = car
        bot.send_message(
            ADMIN_ID3,
            f"Заявка на ремонт:\n\n"
            f"Авто: {brand_model} {year}\n"
            f"Дата: {date_str}\n"
            f"Время: {time_str}\n"
            f"Имя: {name}",
            reply_markup=markup
        )

@bot.message_handler(commands=['show_bookings'])
def show_bookings(message):
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, service, car_id, user_id, date, time, status FROM bookings ORDER BY created_at DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        bot.send_message(message.chat.id, "Таблица bookings пуста.")
        return

    text = "Последние 20 записей в bookings:\n\n"
    for row in rows:
        booking_id, service, car_id, user_id, date_, time_, status = row
        text += (f"ID: {booking_id}, Service: {service}, Car ID: {car_id}, User ID: {user_id}, "
                 f"Date: {date_}, Time: {time_}, Status: {status}\n")

    bot.send_message(message.chat.id, text)
@bot.callback_query_handler(func=lambda call: call.data.startswith("repair_approve_"))
def process_repair_approve(call):
    try:
        full_data = call.data[len("repair_approve_"):]
        parts = full_data.split("_")

        if len(parts) != 4:
            raise ValueError(f"Недостаточно частей в callback_data: {parts}")


        car_id = int(parts[0])
        user_id = int(parts[1])
        date_str = urllib.parse.unquote(parts[2])
        time_str = urllib.parse.unquote(parts[3])
        print(car_id, user_id, date_str, time_str)
        with db_lock:
            conn = get_db_connection()
            cur = conn.cursor()

            # Можно добавить логику блокировки машины, если нужно
            # cur.execute('UPDATE cars SET is_available = 0 WHERE car_id = ?', (car_id,))
            cur.execute("SELECT telegram_id FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            if not row:
                bot.answer_callback_query(call.id, "❌ Пользователь с таким ID не найден.")
                conn.close()
                return

            telegram_id = row[0]  # 👈 Используется только для отправки сообщения
            print(user_id)
            # ✅ Здесь нужно использовать user_id, а не telegram_id
            cur.execute('''
                UPDATE repair_bookings
                SET status = 'confirmed'
                WHERE car_id = ? AND user_id = ? AND date = ? AND time = ?
            ''', (car_id, user_id, date_str, time_str))
            # Получаем telegram_id пользователя
            conn.commit()

            conn.close()

        service_display = "ремонт"

        bot.send_message(
            telegram_id,
            f"✅ Ваша заявка на {service_display} одобрена!\n\n"
            f"📅 Дата: {date_str}\n"
            f"🕒 Время: {time_str}\n"
            f"Ждем вас в нашем сервисном центре."
        )

        # Удаляем кнопки у администратора
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.answer_callback_query(call.id, "Заявка подтверждена.")

    except Exception as e:
        bot.answer_callback_query(call.id, f"Ошибка подтверждения: {e}")
        print(f"❌ Ошибка в process_repair_approve: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("repair_suggest_") and
                                                  not call.data.startswith("repair_suggest_time_") and
                                                  not call.data.startswith("repair_select_date_"))
def process_repair_suggest(call):
    data = call.data[len("repair_suggest_"):]
    parts = data.split("_")
    if len(parts) < 2:
        bot.answer_callback_query(call.id, "Ошибка данных.")
        return

    try:
        car_id = int(parts[0])
        user_id = int(parts[1])
    except ValueError:
        bot.answer_callback_query(call.id, "Некорректный формат данных.")
        return

    chat_id = call.message.chat.id

    session = get_session(user_id) or {}
    date_str = session.get('repair_suggest_date')
    if not date_str:
        bot.send_message(chat_id, "❌ Не найдена дата для предложения ремонта.")
        return

    session['repair_suggest_car_id'] = car_id
    session['repair_suggest_user_id'] = user_id
    repair_selected_suggest[chat_id] = (car_id, user_id)
    save_session(user_id, session)

    bot.answer_callback_query(call.id)
    show_repair_admin_suggest_calendar(call.message, car_id, user_id, date_str)

def show_repair_admin_suggest_calendar(message, car_id, user_id, date_str):
    conn = sqlite3.connect('cars.db')
    c = conn.cursor()
    c.execute("SELECT time FROM repair_bookings WHERE car_id=? AND date=? AND status='confirmed'", (car_id, date_str))
    booked_times = [row[0] for row in c.fetchall()]
    conn.close()

    keyboard = types.InlineKeyboardMarkup(row_width=3)
    for hour in range(10, 19):
        time_str = f"{hour:02d}:00"
        if time_str in booked_times:
            btn = types.InlineKeyboardButton(f"⛔ {time_str}", callback_data="busy")
        else:
            btn = types.InlineKeyboardButton(time_str,
                callback_data=f"repair_suggest_time_{car_id}_{user_id}_{date_str}_{time_str}")
        keyboard.add(btn)

    bot.send_message(message.chat.id, f"Выберите время для ремонта:", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text and message.chat.id in repair_selected_suggest)
def handle_repair_suggest_date_choice(message):
    text = message.text.strip()
    if text == "🔙 Отмена":
        bot.send_message(message.chat.id, "Отменено.", reply_markup=types.ReplyKeyboardRemove())
        repair_selected_suggest.pop(message.chat.id, None)
        return

    try:
        now = datetime.now()
        chosen_date = datetime.strptime(text, "%d %b").replace(year=now.year)
        if chosen_date.date() < now.date():
            chosen_date = chosen_date.replace(year=now.year + 1)
        date_str = chosen_date.strftime("%Y-%m-%d")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный формат даты. Пожалуйста, выберите дату с клавиатуры.")
        return

    car_id, user_id = repair_selected_suggest[message.chat.id]
    repair_selected_suggest.pop(message.chat.id, None)

    session = get_session(user_id)
    session["repair_suggest_date"] = date_str
    save_session(user_id, session)

    bot.send_message(message.chat.id, f"Дата выбрана: {text}. Теперь выберите время:",
                     reply_markup=types.ReplyKeyboardRemove())
    show_repair_time_selection(message, car_id, user_id, date_str)

def show_repair_time_selection(message, car_id, user_id, date_str):
    with sqlite3.connect('cars.db', timeout=10) as conn:
        c = conn.cursor()
        c.execute("SELECT time FROM repair_bookings WHERE car_id=? AND date=? AND status='confirmed'", (car_id, date_str))
        booked_times = [row[0] for row in c.fetchall()]
    # conn закрыт автоматически здесь

    keyboard = types.InlineKeyboardMarkup(row_width=3)
    for hour in range(10, 19):
        time_str = f"{hour:02d}:00"
        if time_str in booked_times:
            btn = types.InlineKeyboardButton(f"⛔ {time_str}", callback_data="busy")
        else:
            btn = types.InlineKeyboardButton(time_str,
                                             callback_data=f"repair_suggest_time_{car_id}_{user_id}_{date_str}_{time_str}")
        keyboard.add(btn)

    bot.send_message(message.chat.id, f"Выберите время для ремонта:", reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("repair_suggest_time_"))
    def process_repair_time_selection(call):
        print("callback received:", call.data)
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

        try:
            data = call.data[len("repair_suggest_time_"):]
            parts = data.split("_")
            if len(parts) != 4:
                bot.answer_callback_query(call.id, "❌ Некорректные данные.")
                return

            car_id = int(parts[0])
            telegram_id = int(parts[1])
            date_str = parts[2]
            time_str = parts[3]

            bot.answer_callback_query(call.id, text=f"Вы выбрали {date_str} {time_str}")

            with db_lock:
                with sqlite3.connect('cars.db', timeout=10) as conn:
                    c = conn.cursor()

                    c.execute("SELECT telegram_id FROM users WHERE id = ?", (telegram_id,))
                    result = c.fetchone()
                    if not result:
                        bot.send_message(call.message.chat.id, "❌ Не найден пользователь с таким telegram_id.")
                        return

                    user_id = result[0]

                    service = 'repair'

                    c.execute('''INSERT INTO repair_bookings (user_id, car_id, service, date, time, status)
                                 VALUES (?, ?, ?, ?, ?, 'suggested')''',
                              (user_id, car_id, service, date_str, time_str))
                    conn.commit()

            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("OK",
                                                  callback_data=f"repair_ok_{service}_{car_id}_{user_id}_{date_str}_{time_str}"))
            bot.send_message(user_id,
                             f"📩 Администратор предлагает: {date_str} в {time_str}\nЕсли согласны, нажмите кнопку ниже.",
                             reply_markup=markup)
            bot.send_message(call.message.chat.id, "✅ Предложение отправлено клиенту.")

        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Ошибка: {e}")


    @bot.callback_query_handler(func=lambda call: call.data.startswith("repair_ok_"))
    def process_repair_ok(call):
        try:
            parts = call.data[len("repair_ok_"):].split("_")
            if len(parts) < 5:
                raise ValueError("Недостаточно частей в callback_data")

            service = parts[0]
            car_id = int(parts[1])
            user_id = int(parts[2])
            date_str = parts[3]
            time_str = parts[4]
            print(user_id)
            with db_lock:
                conn = get_db_connection()
                cur = conn.cursor()

                # Обновляем статус брони ремонта
                cur.execute('''
                    UPDATE repair_bookings
                    SET status = 'confirmed'
                    WHERE service = ? AND car_id = ? AND user_id = ? AND date = ? AND time = ?
                ''', (service, car_id, user_id, date_str, time_str))
                conn.commit()

                cur.execute("SELECT telegram_id FROM users WHERE telegram_id = ?", (user_id,))
                result = cur.fetchone()
                if not result:
                    bot.answer_callback_query(call.id, "❌ Пользователь с таким ID не найден.")
                    conn.close()
                    return
                telegram_id = result[0]
                conn.close()

            service_display = "ремонт"

            bot.send_message(
                telegram_id,
                f"✅ Ваша заявка на {service_display} одобрена!\n\n"
                f"📅 Дата: {date_str}\n"
                f"🕒 Время: {time_str}\n"
                f"Ждем вас в нашем сервисном центре."
            )

            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            bot.answer_callback_query(call.id, "Заявка подтверждена.")

        except Exception as e:
            bot.answer_callback_query(call.id, f"Ошибка подтверждения: {e}")
            print(f"❌ Ошибка в process_repair_ok: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("repair_reject_"))
def process_repair_reject(call):
    print("CALL DATA:", call.data)
    try:
        full_data = call.data[len("repair_reject_"):]
        parts = full_data.split("_")

        if len(parts) != 4:
            raise ValueError(f"Недостаточно частей в callback_data: {parts}")

        car_id = int(parts[0])
        user_id = int(parts[1])
        date_str = urllib.parse.unquote(parts[2])
        time_str = urllib.parse.unquote(parts[3])

        # Проверка telegram_id пользователя
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            bot.answer_callback_query(call.id, "❌ Пользователь не найден.")
            return
        telegram_id = row[0]
        conn.close()

        # Сохраняем ожидание причины
        repair_reject_reasons[call.from_user.id] = {
            "car_id": car_id,
            "user_id": user_id,
            "date_str": date_str,
            "time_str": time_str,
            "telegram_id": telegram_id,
            "chat_id": call.message.chat.id,
            "message_id": call.message.message_id
        }

        bot.send_message(call.from_user.id, "❌ Введите причину отказа пользователя.")
        bot.answer_callback_query(call.id)

    except Exception as e:
        bot.answer_callback_query(call.id, "Произошла ошибка.")
        print(f"[ERROR in process_repair_reject]: {e}")
@bot.message_handler(func=lambda message: message.from_user and message.from_user.id in globals().get("repair_reject_reasons", {}))
def handle_repair_rejection_reason(message):
    admin_id = message.from_user.id
    reason = message.text.strip()

    data = repair_reject_reasons.pop(admin_id, None)
    if not data:
        return

    car_id = data["car_id"]
    user_id = data["user_id"]
    date_str = data["date_str"]
    time_str = data["time_str"]
    telegram_id = data["telegram_id"]
    chat_id = data["chat_id"]
    message_id = data["message_id"]

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Удаление заявки
        cursor.execute('''
            DELETE FROM repair_bookings
            WHERE car_id = ? AND user_id = ? AND date = ? AND time = ?
        ''', (car_id, user_id, date_str, time_str))

        # Освобождение машины

        conn.commit()
        conn.close()

        # Уведомление пользователя
        bot.send_message(telegram_id,
                         f"❌ Ваша заявка на ремонт отклонена.\nПричина: {reason}")

        # Удаление inline кнопок
        bot.edit_message_reply_markup(chat_id, message_id, reply_markup=None)

        bot.send_message(admin_id, "✅ Отказ обработан. Заявка удалена, автомобиль снова доступен.")

    except Exception as e:
        bot.send_message(admin_id, "❌ Ошибка при обработке отказа.")
        print(f"[ERROR in handle_repair_rejection_reason]: {e}")
@bot.message_handler(commands=["view_repair_bookings"])
def send_repair_requests(message):
    chat_id = message.chat.id
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Получаем заявки
        cursor.execute('''
            SELECT rb.id, u.name, c.brand_model, c.year, rb.date, rb.time, rb.status
            FROM repair_bookings rb
            JOIN users u ON rb.user_id = u.id
            JOIN cars c ON rb.car_id = c.car_id
            ORDER BY rb.date, rb.time
        ''')
        requests = cursor.fetchall()
        conn.close()

    if not requests:
        bot.send_message(chat_id, "❌ Нет новых заявок на ремонт.")
        return

    for req in requests:
        req_id, user_name, brand_model, year, date_str, time_str, status = req

        # Галочка, если подтверждено
        status_display = "✅ confirmed" if status == "confirmed" else status

        message_text = (
            f"🆔 Заявка #{req_id}\n"
            f"👤 Клиент: {user_name}\n"
            f"🚗 Авто: {brand_model} {year}\n"
            f"📅 Дата: {date_str}\n"
            f"🕒 Время: {time_str}\n"
            f"⏳ Статус: {status_display}"
        )

        bot.send_message(chat_id, message_text)



@bot.message_handler(commands=['set_new'])
def set_user_status_new(message):
    if message.from_user.id != ADMIN_ID2:
        bot.reply_to(message, "⛔️ У вас нет доступа к этой команде.")
        return

    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            bot.reply_to(message, "⚠️ Использование: /set_new <telegram_id>")
            return

        telegram_id = int(parts[1])

        with sqlite3.connect("cars.db") as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET status = 'new' WHERE telegram_id = ?", (telegram_id,))
            conn.commit()

        bot.reply_to(message, f"✅ Статус пользователя {telegram_id} установлен как 'new'.")

    except Exception as e:
        print(f"[set_user_status_new] Ошибка: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при обновлении статуса.")


@bot.callback_query_handler(func=lambda call: call.data == "help_wash")
def handle_help_wash(call):
    user_id = call.from_user.id
    session = get_session(user_id)

    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "📅 Выберите дату:", reply_markup=create_date_markup_wash())

    session.clear()
    set_state(user_id, "carwash_waiting_for_date")


@bot.message_handler(func=lambda msg: get_state(msg.from_user.id) == "carwash_waiting_for_date")
def handle_carwash_date(message):
    user_id = message.from_user.id
    session = get_session(user_id)
    text = message.text.strip().lower()

    selected_date_obj = parse_russian_date(text)

    if not selected_date_obj:
        bot.send_message(message.chat.id, "❗ Неверный формат даты. Пример: 21 июля.")
        return

    selected_date = selected_date_obj.strftime('%Y-%m-%d')
    today = datetime.today().date()

    if selected_date_obj.date() == today and datetime.now().time() > datetime.strptime("19:30", "%H:%M").time():
        bot.send_message(message.chat.id, "⛔️ На сегодня запись уже закрыта. Выберите другую дату.")
        return

    session["selected_date"] = selected_date
    set_state(user_id, "carwash_waiting_for_time")
    bot.send_message(message.chat.id, "⏰ Выберите время:", reply_markup=create_time_markup(selected_date))

@bot.message_handler(func=lambda msg: get_state(msg.from_user.id) == "carwash_waiting_for_time")
def handle_carwash_time(message):
    user_id = message.from_user.id
    session = get_session(user_id)

    selected_date = session.get("selected_date")
    selected_time = message.text.strip()
    call_sign = session.get("driver_call_sign", "Без имени")

    if selected_date:
        add_booking_wash(user_id, selected_date, selected_time, call_sign)
        bot.send_message(message.chat.id, f"✅ Вы записаны на мойку {selected_date} в {selected_time}.", reply_markup=clear_keyboard())
    else:
        bot.send_message(message.chat.id, "❌ Ошибка: дата не выбрана.")

    user_sessions.pop(user_id, None)  # очищаем сессию после записи

# ==== Функция добавления записи ====
def add_booking_wash(user_id, date, time, name):
    conn = sqlite3.connect("cars.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO bookings_wash (user_id, name, date, time, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, name or "Без имени", date, time, "confirmed"))
    conn.commit()
    conn.close()


def has_available_slots(date_str):
    booked = get_booked_dates_and_times_wash()
    time_slots = [f"{h:02d}:{m:02d}" for h in range(9, 19) for m in (0, 30)]

    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

    for slot in time_slots:
        slot_time = datetime.strptime(slot, "%H:%M").time()

        if (date_str, slot) not in booked:
            if date_obj > datetime.today().date():
                return True
            elif date_obj == datetime.today().date() and slot_time > datetime.now().time():
                return True
    return False


def create_date_markup_wash():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    today = datetime.today().date()

    for i in range(0, 14):  # Следующие 14 дней
        date = today + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')

        if has_available_slots(date_str):
            # Формируем вид даты как "21 июля"
            day = date.day
            month_name = list(MONTHS_RU_GEN.keys())[date.month - 1]
            readable = f"{day} {month_name}"
            markup.add(types.KeyboardButton(readable))

    return markup

# ==== Клавиатура времени ====
def create_time_markup(selected_date: str):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    booked = get_booked_dates_and_times_wash()

    # Преобразуем дату
    selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
    now = datetime.now()

    # Временные слоты с 9:00 до 19:30
    time_slots = [f"{h:02d}:{m:02d}" for h in range(9, 20) for m in (0, 30)]

    available = []
    for slot in time_slots:
        slot_time = datetime.strptime(slot, "%H:%M").time()

        # Убираем прошлые слоты, если выбрана сегодняшняя дата
        if selected_date_obj == now.date() and slot_time <= now.time():
            continue

        if (selected_date, slot) not in booked:
            available.append(slot)

    for slot in available:
        markup.add(types.KeyboardButton(slot))

    return markup

# ==== Проверка занятых слотов ====
def get_booked_dates_and_times_wash():
    conn = sqlite3.connect("cars.db")
    c = conn.cursor()
    c.execute("SELECT date, time FROM bookings_wash WHERE status = 'confirmed'")
    booked = c.fetchall()
    conn.close()
    return set(booked)


def send_booking_reminder():
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M")

    try:
        conn = sqlite3.connect("cars.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # --- Обработка записей на мойку ---
        cursor.execute("SELECT id, user_id, date, time FROM bookings_wash WHERE status = 'confirmed'")
        bookings = cursor.fetchall()

        for booking in bookings:
            booking_id = booking["id"]
            user_id = booking["user_id"]
            date = booking["date"]
            time_ = booking["time"]

            booking_time = datetime.strptime(f"{date} {time_}", "%Y-%m-%d %H:%M")
            seconds_until = (booking_time - now).total_seconds()
            seconds_after = (now - booking_time).total_seconds()

            # Напоминание за 1 час
            if 3500 < seconds_until <= 3600:
                bot.send_message(user_id, f"🔔 Напоминание: через 1 час мойка на {date} в {time_}.")

            # Благодарность после 20-30 мин
            elif 1340 < seconds_after <= 1440:
                bot.send_message(user_id, f"✅ Спасибо! Ваша мойка на {date} в {time_} завершена.")
                cursor.execute("DELETE FROM bookings_wash WHERE id = ?", (booking_id,))
                conn.commit()

        # --- Обработка напоминаний о сдаче авто ---
        cursor.execute("""
            SELECT h.id, h.user_id, h.rent_end, u.telegram_id
            FROM rental_history h
            JOIN users u ON h.user_id = u.id
        """)
        rentals = cursor.fetchall()

        for rental in rentals:
            rent_end_str = rental["rent_end"]
            rent_end = datetime.strptime(rent_end_str, "%Y-%m-%d %H:%M")
            telegram_id = rental["telegram_id"]

            # Напоминание за 1 сутки
            notify_day_before = rent_end - timedelta(days=1)
            if notify_day_before.strftime("%Y-%m-%d %H:%M") == now_str:
                bot.send_message(telegram_id, f"📅 Напоминание: завтра вы должны сдать автомобиль в {rent_end.strftime('%H:%M')}.")

            # Напоминание в 08:00 утра в день сдачи
            notify_morning = rent_end.replace(hour=8, minute=0)
            if notify_morning.strftime("%Y-%m-%d %H:%M") == now_str:
                bot.send_message(telegram_id, f"🚗 Сегодня сдача автомобиля в {rent_end.strftime('%H:%M')} — не забудьте сообщить администратору!")

    except Exception as e:
        print(f"[ERROR] Ошибка в send_booking_reminder: {e}")
    finally:
        conn.close()


@bot.callback_query_handler(func=lambda c: c.data.startswith("help_question"))
def handle_unknown_messages(call):
    bot.send_message(call.message.chat.id, "Задавай вопрос")
    bot.register_next_step_handler(call.message, question_function)












@bot.message_handler(commands=["rental_history"])
def rental_history(message):
    telegram_id = message.from_user.id

    try:
        with sqlite3.connect("cars.db") as conn:
            c = conn.cursor()

            # Получаем user_id
            c.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
            row = c.fetchone()
            if not row:
                bot.send_message(telegram_id, "❌ Вы не зарегистрированы.")
                return

            user_id = row[0]

            # Получаем ВСЕ аренды пользователя
            c.execute("""
                SELECT rh.rent_start, rh.rent_end, rh.price, rh.delivery_price, rh.delivery_address,
                       c.brand_model, c.year
                FROM rental_history rh
                JOIN cars c ON rh.car_id = c.car_id
                WHERE rh.user_id = ?
                ORDER BY rh.rent_end DESC
                LIMIT 10
            """, (user_id,))

            rows = c.fetchall()
            if not rows:
                bot.send_message(telegram_id, "📭 У вас пока нет аренд.")
                return

            msg = "📘 *История ваших аренд:*\n\n"
            for rent_start, rent_end, price, delivery_price, delivery_address, brand_model, year in rows:
                msg += (
                    f"🚗 {brand_model} {year}\n"
                    f"🗓 С {rent_start} по {rent_end}\n"
                    f"💸 Аренда: {price} ₽\n"
                )
                print(delivery_price, delivery_address)
                # Добавляем информацию о доставке, если есть
                if delivery_price is not None and delivery_address:
                    msg += (
                        f"🚚 Доставка: {delivery_price} ₽\n"
                        f"📍 Адрес доставки: {delivery_address}\n"
                    )
                msg += "\n"

            bot.send_message(telegram_id, msg, parse_mode="Markdown")

    except Exception as e:
        bot.send_message(telegram_id, f"❗ Ошибка при получении истории: {e}")


@bot.message_handler(func=lambda message: get_state(message.from_user.id) and get_state(message.from_user.id).startswith("waiting_for_time_pick|"))
def handle_time_pick(message):
    from datetime import datetime
    from types import SimpleNamespace

    user_id = message.from_user.id
    chat_id = message.chat.id
    selected_time = message.text.strip()

    state = get_state(user_id)
    try:
        _, service, car_id, date_str = state.split("|")
        car_id = int(car_id)
    except (ValueError, AttributeError):
        bot.send_message(chat_id, "⚠️ Ошибка состояния. Попробуйте ещё раз.")
        clear_state(user_id)
        return

    try:
        datetime.strptime(selected_time, "%H:%M")
    except ValueError:
        bot.send_message(chat_id, "❌ Неверный формат времени. Введите в формате ЧЧ:ММ, например 14:30.")
        return

    fake_call = SimpleNamespace(
        id='manual_time_pick',
        from_user=message.from_user,
        message=message,
        data=f"select_time|{service}|{car_id}|{date_str}|{selected_time}"
    )

    handle_time_selection(fake_call)



from apscheduler.schedulers.background import BackgroundScheduler

# Создаём глобальный scheduler


from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread
import signal
import time
import sys

scheduler = BackgroundScheduler()


def shutdown_scheduler(signum, frame):
    print("🛑 Останавливаем scheduler...")
    if scheduler.running:
        scheduler.shutdown(wait=False)
    sys.exit(0)



def start_scheduler():
    # Добавляем задачи
    if not scheduler.get_job('notify_admin_job'):
        scheduler.add_job(notify_admin, 'interval', minutes=1, id='notify_admin_job')
    if not scheduler.get_job('reminder_job'):
        scheduler.add_job(send_booking_reminder, 'interval', seconds=60, id='reminder_job')
    if not scheduler.running:
        scheduler.start()



   
if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_scheduler)
    signal.signal(signal.SIGTERM, shutdown_scheduler)


    # Настройка и запуск планировщика
    start_scheduler()
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    print(f"✅ Вебхук установлен: {WEBHOOK_URL}")
    setup_tables()
    print("✅ Бот запущен") 
    app.run(host="0.0.0.0", port=10000)
   


