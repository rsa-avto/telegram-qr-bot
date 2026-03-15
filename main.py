# -*- coding: utf-8 -*
import pandas as pd
import html
import difflib
import re
import sqlite3
import telebot
from apscheduler.schedulers.background import BackgroundScheduler
import signal
import sys
import schedule
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
from types import SimpleNamespace
import os


#6332859587
# --- НАСТРОЙКИ ---
API_TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(API_TOKEN)
ADMIN_ID = [6040726738, 5035760364 ]  # <-- ЗАМЕНИ на свой Telegram ID
#
ADMIN_ID2 = 6040726738
ADMIN_ID3 =  1033210773#сто
ADMIN_IDS = [5035760364, 6040726738,755909251]
ADMINS = [6332859587, 755909251]
DIRECTOR_ID =755909251
MASTER_CHAT_ID = 6486837861 #рихтовка
DAN_TELEGRAM_ID = 5035760364
OFFICE_COORDS = (53.548713,49.292195)
TAXI_SETUP_MANAGER_ID = 1226760421
OPERATORS_IDS = [8406093193, 7956696604, 8411184981, 8340223502]
BONUS_PER_LITRE = 1
STATION_OPERATORS = {
    "Южное шоссе 129": 8340223502,
    "Южное шоссе 12/2": 7956696604,
    "Лесная 66А": 8411184981,
    "Борковская 72/1": 8406093193
}
STATION_CODES_TO_ADDRESSES = {
    "station_1": "Южное шоссе 129",
    "station_2": "Южное шоссе 12/2",
    "station_3": "Лесная 66А",
    "station_4": "Борковская 72/1"
}
STATION_ADDRESSES_TO_CODES = {v: k for k, v in STATION_CODES_TO_ADDRESSES.items()}
PUBLIC_ID = 'cloudpayments-public-id'
API_KEY = 'cloudpayments-api-key'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Для Windows и локальной разработки
if os.name == "nt":  # Windows
    DB_PATH = os.path.join(BASE_DIR, "cars.db")
else:  # Linux / Docker
    DB_PATH = "/app/cars.db"

# Подключение к базе
import sqlite3
conn = sqlite3.connect(DB_PATH, check_same_thread=False)

from flask import Flask
app = Flask(__name__)

# === Scheduler ===
scheduler = BackgroundScheduler()

# === Locks ===
db_lock = threading.Lock()

bot.add_custom_filter(custom_filters.StateFilter(bot))

geolocator = Nominatim(user_agent="tolyatti_car_rental_bot", timeout=20)
booked_slots = {}
ADMIN_REPLY_STATE = {}
user_data = {}
active_reports = {}
repair_reject_reasons = {}
pending_replies = {}
temp_data = {}
selected_service = {}
USER_SELECTED_RENT_START = {}
user_sessions = {}
USER_SELECTED_RENT_END = {}
admin_waiting_for_fullname = {}
USER_DRIVER_CALL_SIGN = {}
USER_PHONE_NUMBER = {}
rent_start_dates = {}
selected_car_ids = {}
selected_dates = {}
USER_SELECTED_DATE = {}
selected_suggest = {}
repair_selected_suggest = {}
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
admin_report_messages = {}
user_car_messages = {}
session = {}
admin_reply_targets = {}
user_purposes = {}



# --- БАЗА ДАННЫХ ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")  # Включить поддержку внешних ключей
    return conn


def get_db():
    return sqlite3.connect(DB_PATH)


def setup_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    # cursor.execute("PRAGMA foreign_keys = OFF;")
    #cursor.execute("DROP TABLE IF EXISTS fuel;")
    # cursor.execute("PRAGMA foreign_keys = ON;")
    # cursor.execute('DROP TABLE rental_history')
    # cursor.execute("ALTER TABLE bookings_wash ADD COLUMN notified INTEGER DEFAULT 0")
    # cursor.execute("ALTER TABLE shifts ADD COLUMN sold_sum INTEGER DEFAULT 0")
    # cursor.execute("ALTER TABLE bookings ADD COLUMN contract_file_id TEXT")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE,
            name TEXT,
            full_name TEXT,
            birthday_date TEXT,
            telegram_id INTEGER UNIQUE,
            driver_license_photo TEXT,
            passport_front_photo TEXT,
            passport_back_photo TEXT,
            status TEXT DEFAULT 'new',
            bonus INTEGER DEFAULT 0,
            purpose TEXT
        )
    ''')

    cursor.execute('''
                CREATE TABLE IF NOT EXISTS fuel (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fuel_type TEXT NOT NULL,   
                    price_per_litre REAL NOT NULL, 
                    payment_method TEXT DEFAULT 'both', 
                    bonuses INTEGER DEFAULT 0 )
            ''')
    # cursor.execute('''INSERT
    # INTO
    # fuel(fuel_type, price_per_litre, payment_method, bonuses)
    # VALUES
    # ('benzin', 45.9, 'card', 0.2),
    # ('gaz', 25.9, 'card', 0.5),
    # ('benzin', 45.9, 'cash', 0.5),
    # ('gaz', 25.9, 'cash', 1)''')
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
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            profession TEXT NOT NULL,
            description TEXT  )''')
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
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        car_id TEXT,
        service TEXT DEFAULT 'rent',
        target TEXT DEFAULT 'personal',
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notified INTEGER DEFAULT 0,
        broken_notified INTEGER DEFAULT 0,
        deposit_status TEXT DEFAULT 'unpaid',
        docs_given INTEGER DEFAULT 0,
        keys_given INTEGER DEFAULT 0,
        contract_file_id TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    ''')
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
            status TEXT DEFAULT 'pending',
            notified INTEGER DEFAULT 0
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
            station TEXT,
            price INTEGER,
            photo_url TEXT,
            is_available INTEGER DEFAULT 0,
            is_broken INTEGER DEFAULT 0,
            fix_date TEXT
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
            end_time TEXT NOT NULL,
            start_time TEXT NOT NULL,
            status TEXT DEFAULT active,
            sum_status TEXT DEFAULT unpaid,
            delivery_price REAL,
            delivery_address TEXT,
    FOREIGN KEY(car_id) REFERENCES cars(car_id) ON DELETE SET NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
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
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS operators (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        station TEXT,
        pin TEXT,
        registered INTEGER DEFAULT 0,
        active INTEGER DEFAULT 0
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operator_id INTEGER,
        station TEXT,
        active INTEGER DEFAULT 0,
        gasoline_liters INTEGER DEFAULT 0,
        gas_liters INTEGER DEFAULT 0,
        sales_sum INTEGER DEFAULT 0,
        bonus_sum REAL DEFAULT 0,
        cars_sold INTEGER DEFAULT 0,
        sold_sum INTEGER DEFAULT 0,
        start_time TEXT,
        end_time TEXT
    )
    """)
    conn.commit()
    conn.close()
from telebot.types import InputFile
@bot.message_handler(commands=["export"])
def export_to_excel(message):
    if message.from_user.id != DAN_TELEGRAM_ID:
        bot.reply_to(message, "⛔ У вас нет доступа к этой команде.")
        return

    try:
        db_path = "cars.db"
        if not os.path.exists(db_path):
            bot.reply_to(message, "⚠️ Файл базы данных не найден.")
            return

        conn = sqlite3.connect(db_path)
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
        excel_path = f"cars_export_{date_str}.xlsx"

        tables_to_export = ['users', 'operators', 'fuel', 'shifts', 'history']

        with pd.ExcelWriter(excel_path) as writer:
            for table_name in tables_to_export:
                try:
                    df = pd.read_sql(f"SELECT * FROM {table_name};", conn)

                    # 🔹 Обработка только для history
                    if table_name == "history":
                        fuel_df = pd.read_sql("SELECT * FROM fuel;", conn)
                        users_df = pd.read_sql("SELECT * FROM users;", conn)

                        # Добавляем номер телефона
                        df = df.merge(
                            users_df[["telegram_id", "phone"]],
                            how="left",
                            left_on="Telegram_ID",
                            right_on="telegram_id"
                        )
                        df.rename(columns={"phone": "Телефон"}, inplace=True)
                        df.drop(columns=["telegram_id"], inplace=True, errors="ignore")

                        # 🔸 Функция расчета баллов
                        def calc_points(row):
                            # нормализуем топливо
                            fuel_name = str(row["Топливо"]).strip().lower()
                            if fuel_name in ["газ", "gas"]:
                                fuel_name = "gaz"
                            elif fuel_name in ["бензин", "petrol", "gasoline"]:
                                fuel_name = "benzin"

                            # нормализуем оплату
                            pay = str(row["Оплата"]).strip().lower()
                            if "карта" in pay or "💳" in pay:
                                pay = "card"
                            elif "нал" in pay or "💵" in pay:
                                pay = "cash"

                            # ищем бонус
                            f = fuel_df[
                                (fuel_df["fuel_type"].str.lower() == fuel_name) &
                                ((fuel_df["payment_method"].str.lower() == pay) |
                                 (fuel_df["payment_method"].str.lower() == "both"))
                            ]

                            if not f.empty:
                                # заменяем запятую на точку, чтобы не было ошибок
                                bonus_percent = float(str(f.iloc[0]["bonuses"]).replace(",", "."))
                                points = round(float(row["Литры"]) * bonus_percent, 2)
                                return points
                            else:
                                return 0

                        # Добавляем столбец Баллы
                        df["Баллы"] = df.apply(calc_points, axis=1)

                    # 💾 Сохраняем таблицу в Excel
                    df.to_excel(writer, sheet_name=table_name, index=False)

                except Exception as e:
                    print(f"⚠️ Не удалось выгрузить таблицу {table_name}: {e}")

        conn.close()

        with open(excel_path, "rb") as f:
            bot.send_document(
                message.chat.id,
                InputFile(f),
                caption=f"📊 Экспорт из базы cars.db ({date_str})",
                timeout=300
            )

        os.remove(excel_path)
        bot.send_message(message.chat.id, "✅ Экспорт успешно выполнен.")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при экспорте: {e}")

months = {
    '01': 'Январь', '02': 'Февраль', '03': 'Март',
    '04': 'Апрель', '05': 'Май', '06': 'Июнь',
    '07': 'Июль', '08': 'Август', '09': 'Сентябрь',
    '10': 'Октябрь', '11': 'Ноябрь', '12': 'Декабрь'
}
OPERATORS = {
    'station_1': 8340223502,
    'station_2': 7956696604,
    'station_3': 8411184981,
    'station_4': 8406093193
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

import logging
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from threading import Lock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Лок для защиты user_sessions / price_change_sessions при записи
sessions_lock = Lock()


# Безопасные обёртки над Telegram-методами чтобы не 'молчать' в случае ошибок
def safe_send(chat_id, text=None, **kwargs):
    try:
        if chat_id is None:
            logger.error("safe_send: chat_id is None, message not sent. text=%s", text)
            notify_admin(f"[CRIT] Попытка отправить сообщение с None chat_id. Текст: {text}")
            return None
        return bot.send_message(chat_id, text, **kwargs)
    except Exception as e:
        logger.exception("safe_send() failed for chat_id=%s text=%s", chat_id, text)
        notify_admin(f"[ERROR] Не удалось отправить сообщение {chat_id}: {e}\nТекст: {text}")
        return None

def safe_edit_text(chat_id, message_id, text):
    try:
        return bot.edit_message_text(text, chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logger.exception("safe_edit_text failed: chat_id=%s message_id=%s", chat_id, message_id)
        notify_admin(f"[ERROR] Не удалось отредактировать сообщение {chat_id}/{message_id}: {e}")
        return None

def safe_edit_reply_markup(chat_id, message_id):
    try:
        return bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
    except Exception as e:
        logger.exception("safe_edit_reply_markup failed: %s/%s", chat_id, message_id)
        notify_admin(f"[ERROR] Не удалось убрать кнопки {chat_id}/{message_id}: {e}")
        return None

def notify_admin(text):
    try:
        # если ADMIN_ID2 не задан, логируем
        admin = globals().get('ADMIN_ID2')
        if admin:
            bot.send_message(admin, text)
        else:
            logger.warning("notify_admin: no ADMIN_ID2 set. text=%s", text)
    except Exception:
        logger.exception("notify_admin failed")

# helper получения цены (возвращает float)
def get_price_per_litre_safe(fuel, payment_method=None):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            if payment_method:
                cur.execute("SELECT price_per_litre FROM fuel WHERE fuel_type = ? AND payment_method = ? LIMIT 1", (fuel, payment_method))
                row = cur.fetchone()
                if row and row[0] is not None:
                    return float(row[0])
            cur.execute("SELECT price_per_litre FROM fuel WHERE fuel_type = ? LIMIT 1", (fuel,))
            row = cur.fetchone()
            if row and row[0] is not None:
                return float(row[0])
    except Exception as e:
        logger.exception("get_price_per_litre_safe DB error")
    return 0.0
# очистка заявок
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
            print(f"[ERROR] Ошибка 403: {e}")

        # Проверять каждые 5 минут
        time.sleep(300)


sent_notifications = set()


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


def clear_state(user_id):
    user_states.pop(user_id, None)


def get_session(chat_id):
    """Получить сессию пользователя"""
    if chat_id not in sessions:
        sessions[chat_id] = {}
    if isinstance(sessions[chat_id], str):
        try:
            sessions[chat_id] = json.loads(sessions[chat_id])
        except json.JSONDecodeError:
            sessions[chat_id] = {}
    return sessions[chat_id]


def set_session(chat_id, **kwargs):
    """Обновить или создать сессию"""
    session = get_session(chat_id)
    session.update(kwargs)
    sessions[chat_id] = session


def clear_session(chat_id):
    """Очистить сессию"""
    sessions.pop(chat_id, None)


def set_state(chat_id, state):
    """Записать состояние"""
    session = get_session(chat_id)
    session["state"] = state
    sessions[chat_id] = session
    print(f"[DEBUG] state set for {chat_id} = {state}")


def get_state(chat_id):
    """Получить состояние"""
    return get_session(chat_id).get("state")


def add_rental_history(user_id, car_id, rent_start, rent_end, price):
    try:
        connection = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT car_id, rent_start, rent_end, price FROM rental_history WHERE user_id = ?", (user_id,))
    history = cursor.fetchall()
    conn.close()
    return history


def update_user_name(phone, name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET name = ? WHERE phone = ?', (name, phone))
    conn.commit()
    conn.close()


sessions = {}  # или твое хранилище
import json


def get_sessions(chat_id):
    # Если сессии нет — создаём
    if chat_id not in sessions:
        sessions[chat_id] = {}
    # Если вдруг сохранили как JSON-строку — парсим
    if isinstance(sessions[chat_id], str):
        try:
            sessions[chat_id] = json.loads(sessions[chat_id])
        except json.JSONDecodeError:
            sessions[chat_id] = {}
    return sessions[chat_id]


def save_session(user_id, session):
    user_sessions[user_id] = session


def delete_user_from_db(phone_number):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE phone = ?", (phone_number,))
    conn.commit()
    conn.close()


def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT phone, name, telegram_id FROM users")
    users = cursor.fetchall()  # список кортежей (phone, name)
    conn.close()
    return users


def get_booked_dates_and_times_repair():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT date, time FROM repair_bookings")
    booked_dates_and_times = cursor.fetchall()
    conn.close()
    return booked_dates_and_times


def get_booked_dates_and_times():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT date, time FROM bookings")
    booked_dates_and_times = cursor.fetchall()
    conn.close()
    return booked_dates_and_times


def get_booked_dates_and_times():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT date, time FROM bookings WHERE status IN ('pending', 'confirmed', 'suggested')")
    data = c.fetchall()
    conn.close()
    return data


def get_user_name_by_id(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM users WHERE telegram_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def update_user_telegram_id(phone, telegram_id):
    try:
        conn = sqlite3.connect(DB_PATH)
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
    except Exception as e:
        print(f"[ERROR] Ошибка 592: {e}")


def sending_time_selection(chat_id, service, car_id, date_str):
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT time FROM repair_bookings WHERE date=? AND status='confirmed'",
                (date_str,)
            )
            booked_times = [row[0] for row in c.fetchall()]
            print(booked_times)
        markup = types.InlineKeyboardMarkup(row_width=3)
        for hour in range(10, 19):  # с 10:00 до 18:00 включительно
            time_str = f"{hour:02d}:00"
            if time_str in booked_times:
                # Кнопка забронированного времени, помечена и неактивна
                btn = types.InlineKeyboardButton(f"⛔ {time_str}", callback_data="busy")
            else:
                # Свободное время — callback_data с выбором времени
                btn = types.InlineKeyboardButton(time_str,
                                                 callback_data=f"chosen_time_{service}_{car_id}_{date_str}_{time_str}")
            markup.add(btn)

        bot.send_message(chat_id, "⏰ Выберите время встречи:", reply_markup=markup)

        # Возвращаем True, если есть свободные слоты, иначе False
        return any(time_str not in booked_times for time_str in [f"{hour:02d}:00" for hour in range(10, 19)])
    except Exception as e:
        print(f"[ERROR] Ошибка 622: {e}")
    # Получаем занятые времена из базы


def add_rental_history(user_id, car_id, rent_start, rent_end, price):
    try:
        connection = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT car_id, rent_start, rent_end, price FROM rental_history WHERE user_id = ?", (user_id,))
    history = cursor.fetchall()
    conn.close()
    return history


def get_booked_dates_and_times():
    conn = sqlite3.connect(DB_PATH)
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
        markup.row(*years[i:i + 3])
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
        cursor.execute("INSERT OR IGNORE INTO users (phone, telegram_id, name) VALUES (?, ?, ?)",
                       (phone_number, telegram_id, name))
        conn.commit()


ADMIN_STATE = {}
session = {}


def send_long_message(chat_id, text, chunk_size=4000):
    for i in range(0, len(text), chunk_size):
        bot.send_message(chat_id, text[i:i + chunk_size])


@bot.message_handler(commands=['delete_history'])
def delete_history(message):
    try:
        parts = message.text.split()

        # Проверка формата
        if len(parts) != 2:
            bot.reply_to(message, "❗ Формат:\n/delete_history <номер>\nНапример:\n/delete_history 3")
            return

        record_id = int(parts[1])

        import sqlite3
        conn = sqlite3.connect("cars.db")
        cursor = conn.cursor()

        # Проверяем, есть ли такая запись
        cursor.execute('SELECT * FROM history WHERE "№" = ?', (record_id,))
        row = cursor.fetchone()

        if not row:
            bot.reply_to(message, f"❗ Запись №{record_id} не найдена.")
            conn.close()
            return

        # Удаляем запись
        cursor.execute('DELETE FROM history WHERE "№" = ?', (record_id,))
        conn.commit()
        conn.close()

        bot.reply_to(message, f"✔ Запись №{record_id} удалена.")

    except ValueError:
        bot.reply_to(message, "❗ Номер должен быть числом.\nПример: /delete_history 2")
    except Exception as e:
        bot.reply_to(message, f"⚠ Ошибка: {e}")


@bot.message_handler(commands=['bonuses'])
def show_fuel_list(message):
    try:
        # Проверяем, что только директор может смотреть
        if message.from_user.id != DAN_TELEGRAM_ID:
            return bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM fuel ORDER BY fuel_type, payment_method")
            fuels = cursor.fetchall()

        if not fuels:
            bot.send_message(DIRECTOR_ID, "⛽ В таблице fuel пока нет данных.")
            return

        text = "⛽ <b>Список топлива:</b>\n\n"
        for fuel in fuels:
            text += (
                f"🆔 ID: {fuel['id']}\n"
                f"⛽ Топливо: {fuel['fuel_type']}\n"
                f"💰 Цена: {fuel['price_per_litre']} ₽/л\n"
                f"💳 Метод оплаты: {fuel['payment_method']}\n"
                f"⭐ Бонусы: {fuel['bonuses']} баллов/л\n"
                "───────────────\n"
            )

        bot.send_message(DIRECTOR_ID, text, parse_mode="HTML")

    except Exception as e:
        print(f"[ERROR] Ошибка при выводе топлива: {e}")
        bot.send_message(message.chat.id, f"❌ Ошибка при выводе топлива: {e}")

@bot.message_handler(commands=['history'])
def show_history(message):
    try:

        if message.from_user.id not in ADMIN_IDS:
            return bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM history ORDER BY 'Дата' DESC LIMIT 100")  # например, 100 записей
            rows = cur.fetchall()

        if not rows:
            return bot.send_message(message.chat.id, "История пуста.")

        text = "📜 История заправок:\n\n"
        for row in rows:
            text += (f"📅 {row['Дата']}\n"
                 f"🏪 {STATION_CODES_TO_ADDRESSES.get(row['Адрес'], row['Адрес'])}\n"
                 f"⛽ {row['Топливо']} — {row['Литры']} л\n"
                 f"💰 {row['Рубли']} руб\n"
                 f"💳 {row['Оплата']}\n"
                 f"👤 ID: {row['Telegram_ID']}\n\n")

        send_long_message(message.chat.id, text)
    except Exception as e:
        print(f"Ошибка 750: {e}")

def add_bonus1(telegram_id: int, amount: int):
    conn = sqlite3.connect("cars.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET bonus = bonus + ? WHERE telegram_id = ?",
        (amount, telegram_id)
    )
    conn.commit()
    conn.close()

# --- команда для добавления бонусов ---
@bot.message_handler(commands=['bonus'])
def handle_bonus(message):
    # проверяем, что команду вызвал админ
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "⛔ У тебя нет прав для этой команды")
        return

    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.reply_to(message, "Использование: /bonus <telegram_id> <сумма>")
            return

        target_id = int(parts[1])
        amount = int(parts[2])

        add_bonus1(target_id, amount)

        bot.reply_to(message, f"✅ Пользователю {target_id} начислено {amount} бонусов")

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")





@bot.message_handler(commands=['raw_rental_history'])
def show_raw_rental_history(message):
    import sqlite3
    if message.from_user.id not in ADMIN_IDS:
        return bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")

    try:
        conn = sqlite3.connect(DB_PATH)
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
                f"status: {row['status']}\n"
                f"end_time {row['end_time']}\n"
                f"🚚 delivery_price: {row['delivery_price']}\n"
                f"📍 delivery_address: {row['delivery_address']}"
            )

            bot.send_message(message.chat.id, text)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")
    finally:
        conn.close()


@bot.message_handler(commands=['list_users'])
def list_users_handler(message):
    try:
        if message.from_user.id not in ADMIN_IDS:
            return bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, phone, name, full_name, birthday_date, telegram_id, 
                   driver_license_photo, passport_front_photo, passport_back_photo,
                   status, bonus
            FROM users
        ''')
        users = cursor.fetchall()
        conn.close()

        if not users:
            bot.reply_to(message, "Пользователей в базе нет.")
            return

        text = "📋 Полный список пользователей:\n\n"
        for user in users:
            (
                user_id, phone, name, full_name, birthday, telegram_id,
                dl_photo, pass_front, pass_back, status, bonus
            ) = user

            text += (
                f"🆔 ID: {user_id}\n"
                f"📞 Телефон: +{phone}\n"
                f"👤 Имя: {name or '—'}\n"
                f" ФИО: {full_name}\n"
                f"💬 Telegram ID: {telegram_id}\n"
                f"📸 ВУ: {'✅' if dl_photo else '❌'}\n"
                f"📄 Паспорт (лицо): {'✅' if pass_front else '❌'}\n"
                f"📄 Паспорт (оборот): {'✅' if pass_back else '❌'}\n"
                f"📌 Статус: {status or '—'}\n"
                f"🎁 Бонусы: {bonus}\n"
                f"----------------------\n"
            )

        # Ограничение по длине Telegram-сообщений
        for chunk_start in range(0, len(text), 4000):
            bot.send_message(message.chat.id, text[chunk_start:chunk_start + 4000])

    except Exception as e:
        print(f"Ошибка 839: {e}")

@bot.message_handler(commands=['update_bookings'])
def command_update_booking(message):
    try:
        # Например, бот получает ID брони и новый статус через текст команды:
        # /update_booking 123 confirmed
        parts = message.text.split()
        if len(parts) != 3:
            bot.reply_to(message, "Использование: /update_booking <booking_id> <new_status>")
            return

        booking_id = int(parts[1])
        new_status = parts[2]

        success = update_booking_status(booking_id=booking_id, new_status=new_status)
        if success:
            bot.reply_to(message, f"✅ Статус брони {booking_id} обновлён на '{new_status}'.")
        else:
            bot.reply_to(message, "❌ Ошибка: брони с таким ID нет.")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при обновлении: {e}")
def update_booking_status(booking_id=None, user_id=None, car_id=None, new_status="confirmed"):
    """
    Обновляет статус брони в таблице bookings.

    Args:
        booking_id (int, optional): ID конкретной брони.
        user_id (int, optional): ID пользователя (для обновления всех его броней на конкретной машине).
        car_id (int, optional): ID машины (для обновления брони конкретной машины пользователя).
        new_status (str): Новый статус ('pending', 'confirmed', 'rejected', и т.д.).

    Returns:
        bool: True если запись обновлена, False если ничего не найдено.
    """
    if not booking_id and not (user_id and car_id):
        raise ValueError("Нужно указать booking_id или комбинацию user_id и car_id")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if booking_id:
            cursor.execute("UPDATE bookings SET status = ? WHERE id = ?", (new_status, booking_id))
        else:
            cursor.execute("UPDATE bookings SET status = ? WHERE user_id = ? AND car_id = ?", (new_status, user_id, car_id))

        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated

    except Exception as e:
        print(f"Ошибка update_booking_status: {e}")
        return False
@bot.message_handler(commands=['show_bookings'])
def show_bookings(message):
    if message.from_user.id not in ADMIN_IDS:
        return bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Сортировка по возрастанию ID
        cursor.execute("SELECT * FROM bookings ORDER BY id ASC")
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
                f"Status: {b['status']}, Deposit_status: {b['deposit_status']}\n"
            )

        for part in split_message(response):
            bot.send_message(message.chat.id, part)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при получении бронирований: {e}")
    finally:
        conn.close()


@bot.message_handler(func=lambda message: ADMIN_STATE.get(message.chat.id) == 'waiting_for_delivery_amount')
def handle_delivery_amount(message):
    try:
        amount = float(message.text.strip())

        conn = sqlite3.connect(DB_PATH)
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
    try:
        chat_id = message.chat.id

        conn = sqlite3.connect(DB_PATH)
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


    except Exception as e:
        print(f"Ошибка 961: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("show_answer_") or call.data == "ask_new")
def handle_ask_buttons(call):
    try:
        chat_id = call.message.chat.id

        if call.data == "ask_new":
            bot.send_message(chat_id, "✏ Введите ваш вопрос:")
            bot.register_next_step_handler(call.message, question_function)
            bot.answer_callback_query(call.id)
            return

        # Показываем ответ на выбранный вопрос
        question_id = int(call.data.replace("show_answer_", ""))
        conn = sqlite3.connect(DB_PATH)
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

    except Exception as e:
        print(f"Ошибка 991: {e}")

def question_function(message):
    import difflib
    import re
    try:
        user_id = message.from_user.id
        raw_text = message.text.strip()

        if raw_text.startswith('/'):
            return

        conn = get_db_connection()
        conn.row_factory = sqlite3.Row  # ← Добавь это
        cur = conn.cursor()
        cur.execute("SELECT name, phone FROM users WHERE telegram_id = ?", (user_id,))
        user_info = cur.fetchone()
        name = user_info["name"] if user_info else "Имя не указано"
        phone = user_info["phone"] if user_info else "Телефон не указан"

        # Нормализация текста
        normalized_text = re.sub(r'\s+', ' ', raw_text).lower()
        normalized_text = re.sub(r'[^\w\s]', '', normalized_text)

        if len(normalized_text) < 3:
            bot.send_message(user_id, "Пожалуйста, задайте более конкретный вопрос.")
            return

        cur.execute("SELECT id, user_id, question_text, answer_text, answered FROM questions")
        all_questions = cur.fetchall()

        threshold = 0.7
        for q_id, q_user_id, q_text, q_answer, q_answered in all_questions:
            q_norm = re.sub(r'\s+', ' ', q_text.lower())
            q_norm = re.sub(r'[^\w\s]', '', q_norm)
            similarity = difflib.SequenceMatcher(None, normalized_text, q_norm).ratio()

            if similarity >= threshold:
                if q_answer and str(q_answer).strip():
                    bot.send_message(user_id, f"✉ Похожий вопрос уже был, вот ответ:\n\n{q_answer}")
                else:
                    bot.send_message(user_id,
                                     "Похожий вопрос уже был, но на него пока нет ответа. Пожалуйста, подождите.")
                return

        # Сохраняем новый вопрос
        cur.execute('''
                INSERT INTO questions (user_id, username, question_text, answer_text, answered)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, name, raw_text, None, False))
        question_id = cur.lastrowid
        conn.commit()
        conn.close()

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Ответить", callback_data=f"answer_{question_id}_{user_id}"))

        bot.send_message(
            ADMIN_ID[0],
            f"❓ Новый вопрос от {name} ({phone}):\n{raw_text}",
            reply_markup=markup
        )
    except Exception as e:
        print(f"Ошибка 1054: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("answer_"))
def handle_answer_callback(call):
    try:

        if call.from_user.id not in ADMIN_ID:
            bot.answer_callback_query(call.id, "У вас нет доступа")
            return

        _, question_id, user_id = call.data.split("_")
        question_id, user_id = int(question_id), int(user_id)

        msg = bot.send_message(call.from_user.id, f"Введите ответ на вопрос #{question_id}:")
        bot.register_next_step_handler(msg, process_admin_answer, question_id, user_id)
    except Exception as e:
        print(f"Ошибка 1070: {e}")

# --- Обработка ответа от админа ---
def process_admin_answer(message, question_id, user_id):
    try:

        answer = message.text

        conn = sqlite3.connect(DB_PATH)
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
    except Exception as e:
        print(f"Ошибка 1101: {e}")

@bot.message_handler(commands=['set_status'])
def set_status_command(message):
    try:
        if message.from_user.id not in ADMIN_IDS:
            return bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")

        import sqlite3
        user_id = message.from_user.id
        args = message.text.split()

        if len(args) != 2:
            return bot.send_message(message.chat.id, "Использование: /set_status <status>")

        new_status = args[1].strip().lower()

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Обновляем статус
            cursor.execute("UPDATE users SET status = ? WHERE telegram_id = ?", (new_status, user_id))

            # Если статус 'new' — удаляем бронирования и историю аренды
            if new_status == "new":
                cursor.execute("DELETE FROM bookings WHERE user_id = ?", (user_id,))
                cursor.execute("DELETE FROM rental_history WHERE user_id = ?", (user_id,))

            conn.commit()

        if new_status == "new":
            bot.send_message(message.chat.id,
                             f"✅ Ваш статус обновлён на: {new_status}\n🗑 Все ваши бронирования и история аренды удалены.")
        else:
            bot.send_message(message.chat.id, f"✅ Ваш статус обновлён на: {new_status}")

    except Exception as e:
        print(f"Ошибка 1138: {e}")

@bot.message_handler(commands=['set_status'])
def set_status_command(message):
    try:
        if message.from_user.id not in ADMIN_IDS:
            return bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")

        user_id = message.from_user.id
        args = message.text.split()

        if len(args) != 2:
            return bot.send_message(message.chat.id, "Использование: /set_status <status>")

        new_status = args[1]

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET status = ? WHERE telegram_id = ?", (new_status, user_id))
        conn.commit()
        conn.close()

        bot.send_message(message.chat.id, f"✅ Ваш статус обновлён на: {new_status}")

    except Exception as e:
        print(f"Ошибка 1163: {e}")


@bot.message_handler(commands=['list_cars'])
def list_all_cars(message):
    try:
        if message.from_user.id not in ADMIN_IDS:
            return bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")

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

    except Exception as e:
        print(f"Ошибка 1188: {e}")

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

def get_reset_booked_dates(car_id: int, user_id: int = None) -> set:
    """
    Получает занятые даты для всех машин такой же модели и года.
    Если user_id указан, занятые этим пользователем даты будут исключены (считаются свободными).
    """
    try:
        booked_dates = None

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # 1. Получаем модель и год выбранного автомобиля
            cursor.execute("SELECT brand_model, year FROM cars WHERE car_id = ?", (car_id,))
            car = cursor.fetchone()
            if not car:
                return set()
            brand_model, year = car

            # 2. Все car_id с той же моделью и годом
            cursor.execute("SELECT car_id FROM cars WHERE brand_model = ? AND year = ?", (brand_model, year))
            all_car_ids = [row[0] for row in cursor.fetchall()]

            # 3. Получаем занятые даты каждой машины
            for cid in all_car_ids:
                cursor.execute("""
                    SELECT rent_start, rent_end, user_id FROM rental_history
                    WHERE car_id = ? AND status = 'confirmed'
                """, (cid,))
                rows = cursor.fetchall()

                car_booked = set()
                for start, end, uid in rows:
                    # если это арендатор текущего user_id, пропускаем
                    if user_id and uid == user_id:
                        continue
                    start_date = datetime.strptime(start, "%Y-%m-%d")
                    end_date = datetime.strptime(end, "%Y-%m-%d")
                    current = start_date
                    while current <= end_date:
                        car_booked.add(current.strftime('%Y-%m-%d'))
                        current += timedelta(days=1)

                if booked_dates is None:
                    booked_dates = car_booked
                else:
                    booked_dates &= car_booked

        return booked_dates if booked_dates else set()
    except Exception as e:
        print(f"Ошибка get_booked_dates: {e}")
        return set()


def create_reset_calendar_markup(car_id=None, user_id=None):
    """
    Создает клавиатуру с календарем.
    Если передан user_id → даты занятые этим пользователем будут считаться свободными.
    """
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        today = datetime.today()
        calendar_buttons = []

        booked = get_reset_booked_dates(car_id, user_id) if car_id else set()
        print("Занятые даты (с учётом пользователя):", booked)

        booked_dates = {datetime.strptime(d, "%Y-%m-%d").date() for d in booked}

        # Добавляем соседние дни для "буфера"
        extended_booked = set(booked_dates)
        for d in booked_dates:
            extended_booked.add(d - timedelta(days=1))
            extended_booked.add(d + timedelta(days=1))

        # Даты от завтра до +30 дней
        for i in range(1, 31):
            day = (today + timedelta(days=i)).date()
            day_num = day.day
            month_name = MONTH_NAMES_RU_GEN[day.month - 1]

            if day in extended_booked:
                button_text = f"❌ {day_num} {month_name}"
            else:
                button_text = f"{day_num} {month_name}"

            calendar_buttons.append(types.KeyboardButton(button_text))

        # Разбиваем по 3 в ряд
        for i in range(0, len(calendar_buttons), 3):
            markup.row(*calendar_buttons[i:i + 3])

        return markup
    except Exception as e:
        print(f"Ошибка create_calendar_markup: {e}")
        return types.ReplyKeyboardMarkup()
@bot.message_handler(func=lambda message: get_state(message.chat.id) == "waiting_for_rental_start")
def handle_date_selection(message):
    try:
        user_id = message.chat.id
        text = message.text.strip().lower()

        # Возможность отменить процесс
        if text in ["отмена", "выход", "/cancel"]:
            set_state(user_id, None)  # сбрасываем состояние
            bot.send_message(user_id, "🚪 Вы вышли из выбора даты аренды.", reply_markup=types.ReplyKeyboardRemove())
            return

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

    except Exception as e:
        print(f"Ошибка 1253: {e}")

@bot.message_handler(func=lambda message: get_state(message.chat.id) == "waiting_for_rent_end")
def handle_rent_end_date(message):
    from datetime import datetime
    import sqlite3

    try:
        user_id = message.chat.id
        text = message.text.strip().lower()

        # Возможность отменить процесс
        if text in ["отмена", "выход", "/cancel"]:
            set_state(user_id, None)
            bot.send_message(
                user_id,
                "🚪 Вы вышли из выбора даты аренды.",
                reply_markup=types.ReplyKeyboardRemove()
            )
            return

        session = get_session(user_id)

        if text == "🔙 назад":
            set_state(user_id, "waiting_for_rent_start")
            bot.send_message(user_id, "📅 Выберите дату начала аренды ещё раз.")
            return

        end_date_str = message.text.strip()
        start_date_str = session.get("rent_start")
        car_id = session.get("car_id")

        if not start_date_str or not car_id:
            bot.send_message(user_id, "❌ Ошибка: не выбрана дата начала или автомобиль.")
            return

        parsed_end = parse_russian_date(end_date_str)
        if not parsed_end:
            bot.send_message(
                user_id,
                "❌ Неверный формат даты. Пожалуйста, выберите дату или выйдите с помощью /cancel."
            )
            return

        rent_start = datetime.strptime(start_date_str, "%Y-%m-%d")
        rent_end = parsed_end.replace(year=rent_start.year)

        # 🚫 Проверка: дата окончания не раньше и не совпадает с датой начала
        if rent_end <= rent_start:
            bot.send_message(
                user_id,
                "❌ Дата окончания аренды должна быть позже даты начала. "
                "Пожалуйста, выберите корректную дату."
            )
            return

        rent_start_str = rent_start.strftime("%Y-%m-%d")
        rent_end_str = rent_end.strftime("%Y-%m-%d")

        # --- проверка свободной машины ---
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT brand_model, year, service, price FROM cars WHERE car_id = ?", (car_id,))
            car_info = cursor.fetchone()
            if not car_info:
                bot.send_message(user_id, "❌ Автомобиль не найден.")
                return

            brand_model, year, service, base_price = car_info

            cursor.execute(
                """ SELECT car_id FROM cars WHERE brand_model = ? AND year = ? """,
                (brand_model, year)
            )
            candidate_cars = [row[0] for row in cursor.fetchall()]

            free_car_id = None
            for cid in candidate_cars:
                cursor.execute(
                    """
                    SELECT 1 FROM rental_history
                    WHERE car_id = ?
                      AND status = 'confirmed'
                      AND user_id != ?
                      AND (
                        (? BETWEEN rent_start AND rent_end)
                        OR (? BETWEEN rent_start AND rent_end)
                        OR (rent_start BETWEEN ? AND ?)
                        OR (rent_end BETWEEN ? AND ?)
                      )
                    """,
                    (cid, user_id, rent_start_str, rent_end_str,
                     rent_start_str, rent_end_str,
                     rent_start_str, rent_end_str)
                )
                if not cursor.fetchone():
                    free_car_id = cid
                    break

            if not free_car_id:
                bot.send_message(user_id, "🚫 Нет свободных машин этой модели и года на выбранные даты.")
                return

            days = (rent_end - rent_start).days
            total_price = calculate_price(base_price, days)

            session.update({
                "car_id": free_car_id,
                "rent_end": rent_end_str,
                "rent_start": rent_start_str,
                "days": days,
                "price": total_price,
                "car_model": brand_model,
                "car_year": year,
                "service": service,
                "db_user_id": user_id
            })

        old_msg_id = session.get("last_calendar_msg_id")
        if old_msg_id:
            try:
                bot.edit_message_reply_markup(
                    chat_id=user_id,
                    message_id=old_msg_id,
                    reply_markup=None
                )
            except telebot.apihelper.ApiTelegramException as e:
                print(f"Не удалось удалить inline-кнопки: {e}")

        bot.send_message(
            user_id,
            f"✅ Свободный {brand_model} ({year}) найден!\n"
            f"📅 Аренда с {rent_start_str} по {rent_end_str}\n"
            f"💰 Стоимость: {total_price} ₽ ({days} дн.)",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardRemove()
        )

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Да", "Нет")
        bot.send_message(user_id, "Все верно?", reply_markup=markup)

        set_state(user_id, "waiting_for_delivery_choice")

    except Exception as e:
        bot.send_message(user_id, f"❌ Ошибка при обработке даты: {e}")
        print(f"Ошибка 1381: {e}")

def calculate_price(base_price, days):
    if base_price is None:
        raise ValueError("base_price не должен быть None")

    if days < 7:
        per_day = base_price
    elif 7 <= days < 14:
        per_day = base_price - 100
    elif 14 <= days < 21:
        per_day = base_price - 200
    elif 21 <= days < 28:
        per_day = base_price - 300
    else:
        per_day = base_price - 400

    if per_day < 0:
        per_day = 0

    return per_day * days


def get_booked_dates(car_id: int) -> set:
    try:
        booked_dates = None  # будет пересечение занятых дат всех машин

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # 1. Получаем модель и год выбранного автомобиля
            cursor.execute("SELECT brand_model, year FROM cars WHERE car_id = ?", (car_id,))
            car = cursor.fetchone()
            if not car:
                return set()
            brand_model, year = car

            # 2. Все car_id с той же моделью и годом
            cursor.execute("SELECT car_id FROM cars WHERE brand_model = ? AND year = ?", (brand_model, year))
            all_car_ids = [row[0] for row in cursor.fetchall()]

            # 3. Получаем занятые даты каждой машины
            for cid in all_car_ids:
                cursor.execute("""
                        SELECT rent_start, rent_end FROM rental_history
                        WHERE car_id = ? AND status = 'confirmed'
                    """, (cid,))
                rows = cursor.fetchall()

                car_booked = set()
                for start, end in rows:
                    start_date = datetime.strptime(start, "%Y-%m-%d")
                    end_date = datetime.strptime(end, "%Y-%m-%d")
                    current = start_date
                    while current <= end_date:
                        car_booked.add(current.strftime('%Y-%m-%d'))
                        current += timedelta(days=1)

                # пересечение: оставляем только те даты, когда заняты все машины
                if booked_dates is None:
                    booked_dates = car_booked
                else:
                    booked_dates &= car_booked

        return booked_dates if booked_dates else set()
    except Exception as e:
        print(f"Ошибка 1448: {e}")



def create_calendar_markup(car_id=None):
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        today = datetime.today()
        calendar_buttons = []

        booked = get_booked_dates(car_id) if car_id else set()
        print("Занятые даты:", booked)

        # Превращаем в set дат-объектов
        booked_dates = {datetime.strptime(d, "%Y-%m-%d").date() for d in booked}

        # Добавляем соседние даты
        extended_booked = set(booked_dates)
        for d in booked_dates:
            extended_booked.add(d - timedelta(days=1))
            extended_booked.add(d + timedelta(days=1))

        # Показываем дни от вчера до +28 дней
        for i in range(1, 31):
            day = (today + timedelta(days=i)).date()
            day_str = day.strftime('%Y-%m-%d')
            day_num = day.day
            month_name = MONTH_NAMES_RU_GEN[day.month - 1]

            if day in extended_booked:
                button_text = f"❌ {day_num} {month_name}"
            else:
                button_text = f"{day_num} {month_name}"

            calendar_buttons.append(types.KeyboardButton(button_text))

        # Расставляем кнопки по рядам
        for i in range(0, len(calendar_buttons), 3):
            markup.row(*calendar_buttons[i:i + 3])

        return markup
    except Exception as e:
        print(f"Ошибка 1490: {e}")


@bot.message_handler(commands=['set_new'])
def set_user_status_new(message):
    if message.from_user.id != ADMIN_ID2 or message.from_user.id != DAN_TELEGRAM_ID:
        bot.reply_to(message, "⛔️ У вас нет доступа к этой команде.")
        return

    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            bot.reply_to(message, "⚠️ Использование: /set_new <telegram_id>")
            return

        telegram_id = int(parts[1])

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET status = 'new' WHERE telegram_id = ?", (telegram_id,))
            conn.commit()

        bot.reply_to(message, f"✅ Статус пользователя {telegram_id} установлен как 'new'.")

    except Exception as e:
        print(f"[set_user_status_new] Ошибка: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при обновлении статуса.")


@bot.message_handler(commands=['start'])
def start(message):
    try:
        user_id = message.from_user.id
        print(user_id)

        # --- Подключение к базе ---
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT name, status FROM users WHERE telegram_id = ?", (user_id,))
        result = cursor.fetchone()

        service_map = {
            "rent": "Аренда",
            "rental": "Аренда",
            "repair": "Ремонт"
        }
        status_map = {
            "pending": "В ожидании",
            "confirmed": "Подтверждено",
            "rejected": "Отклонено"
        }

        # --- Если админ ---
        if user_id == ADMIN_ID3:
            cursor.execute("""
                SELECT id, user_id, car_id, service, date, time, status
                FROM repair_bookings
                ORDER BY date ASC, time ASC
            """)
            rows = cursor.fetchall()
            now = datetime.now()
            fresh_requests = []

            for row in rows:
                dt_str = f"{row['date']} {row['time']}"
                try:
                    booking_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                except ValueError:
                    continue
                if booking_dt >= now:
                    fresh_requests.append((row, booking_dt))

            if not fresh_requests:
                bot.send_message(user_id, "📭 Нет актуальных заявок на ремонт.")
                return

            text = "🛠 Актуальные заявки:\n\n"
            for row, booking_dt in fresh_requests:
                cursor.execute("SELECT phone FROM users WHERE id = ?", (row['user_id'],))
                user_data = cursor.fetchone()
                phone = user_data['phone'] if user_data else "—"

                service_ru = service_map.get(row['service'], row['service'])
                status_ru = status_map.get(row['status'], row['status'])

                text += (
                    f"🆔 {row['id']}\n"
                    f"👤 Пользователь ID: {row['user_id']}\n"
                    f"📞 Телефон: {phone}\n"
                    f"🚘 Авто ID: {row['car_id']}\n"
                    f"📅 Дата: {row['date']} {row['time']}\n"
                    f"⚙️ Услуга: {service_ru}\n"
                    f"📌 Статус: {status_ru}\n"
                    f"{'-'*25}\n"
                )

            bot.send_message(user_id, text)
            return

        # --- Для операторов ---
        if user_id in OPERATORS_IDS:
            station_address = next((addr for addr, uid in STATION_OPERATORS.items() if uid == user_id), None)
            if not station_address:
                bot.send_message(message.chat.id, "Ошибка: станция не найдена для этого пользователя.")
                return

            station_code = next((code for code, addr in STATION_CODES_TO_ADDRESSES.items() if addr == station_address), None)
            if not station_code:
                bot.send_message(message.chat.id, "Ошибка: код станции не найден.")
                return

            cursor.execute("SELECT id, name, active FROM operators WHERE station=?", (station_code,))
            operators = cursor.fetchall()
            active_operator = next((op for op in operators if op[2] == 1), None)

            markup = types.InlineKeyboardMarkup()
            if active_operator:
                markup.add(types.InlineKeyboardButton(
                    "Завершить смену",
                    callback_data=f"end_shift:{active_operator[0]}"
                ))
                bot.send_message(message.chat.id, "Когда закончите смену, нажмите на кнопку ниже:", reply_markup=markup)
            else:
                for op_id, name, _ in operators:
                    markup.add(types.InlineKeyboardButton(name, callback_data=f"operator_choose:{op_id}"))
                bot.send_message(message.chat.id, "Выберите своё имя:", reply_markup=markup)
            return

        conn.close()

        # --- Для обычных пользователей ---
        if result:
            name, status = result["name"], result["status"]

            if status == 'awaiting_use':
                start_use_kb = types.InlineKeyboardMarkup()
                start_use_kb.add(types.InlineKeyboardButton("🚀 Начать использование машины", callback_data="start_use"))
                bot.send_message(
                    message.chat.id,
                    f"Привет, {name}! Готовы начать использование автомобиля?",
                    reply_markup=start_use_kb
                )

            elif status == 'using_car':
                show_main_menu(message.chat.id)

            elif status == 'waiting_car':
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT rh.rent_start, b.service, b.deposit_status
                    FROM rental_history rh
                    JOIN bookings b ON rh.user_id = b.user_id AND rh.car_id = b.car_id
                    WHERE rh.user_id = ?
                    ORDER BY rh.id DESC LIMIT 1
                """, (user_id,))
                rental = cursor.fetchone()

                cursor.execute("""
                    SELECT id, docs_given, service, date
                    FROM bookings
                    WHERE user_id = ? AND status = 'confirmed'
                    ORDER BY id DESC LIMIT 1
                """, (user_id,))
                booking = cursor.fetchone()
                conn.close()

                # --- Если ключи уже выданы ---
                if booking and booking["docs_given"]:
                    booking_id = booking["id"]
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton(
                        "➡️ Осмотр авто",
                        callback_data=f"continue_inspection_{booking_id}_{user_id}"
                    ))
                    bot.send_message(
                        message.chat.id,
                        "📄 Копии договора уже выданы. Давайте продолжим процесс осмотра автомобиля.",
                        reply_markup=markup
                    )
                    return

                today = datetime.today().date()
                # --- Проверка аренды ---
                if rental and rental["service"] == "rental":
                    rent_start_date = datetime.strptime(rental["rent_start"], "%Y-%m-%d").date()
                    deposit_status = rental["deposit_status"]

                    reply_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                    if rent_start_date == today and deposit_status == "paid":
                        reply_kb.add("ℹ️ Информация об аренде", "📍 Я на месте")
                        reply_kb.add("❌ Отменить аренду")
                        bot.send_message(
                            message.chat.id,
                            f"🚗 Привет, {name}! Сегодня начинается ваша аренда. Выберите действие:",
                            reply_markup=reply_kb
                        )
                        return
                    else:
                        reply_kb.add("💳 Оплатить онлайн", "ℹ️ Информация об аренде")
                        bot.send_message(
                            message.chat.id,
                            f"🚗 Привет, {name}! Ваша машина зарезервирована. Ожидаем дату начала аренды.",
                            reply_markup=reply_kb
                        )
                        return

                elif booking and booking["service"] == "rent":
                    booking_date = datetime.strptime(booking["date"], "%Y-%m-%d").date()
                    rent_start_date = booking_date + timedelta(days=1)

                    reply_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                    if rent_start_date == today:
                        reply_kb.add("ℹ️ Информация об аренде", "📍 Я на месте")
                        bot.send_message(
                            message.chat.id,
                            f"🚗 Привет, {name}! Сегодня вы можете забрать машину. Выберите действие:",
                            reply_markup=reply_kb
                        )
                    else:
                        reply_kb.add("💳 Оплатить онлайн", "ℹ️ Информация об аренде")
                        bot.send_message(
                            message.chat.id,
                            f"🚗 Привет, {name}! Ваша машина зарезервирована. Ожидаем дату начала аренды.",
                            reply_markup=reply_kb
                        )
                    return

                # --- Админские кнопки ---
                markup = types.InlineKeyboardMarkup()
                if user_id == DIRECTOR_ID:
                    markup.add(types.InlineKeyboardButton("💰 Сменить цену топлива", callback_data="admin_set_price"))
                    markup.add(types.InlineKeyboardButton("🎁 Сменить бонусы", callback_data="admin_set_bonus"))
                    markup.add(types.InlineKeyboardButton("💸 Список вакансий", callback_data="admin_set_job"))
                    markup.add(types.InlineKeyboardButton("👤 Добавить оператора", callback_data="admin_set_operator"))
                    markup.add(types.InlineKeyboardButton("📢 Сделать рассылку", callback_data="admin_set_broadcast"))
                if user_id in ADMIN_IDS:
                    markup.add(types.InlineKeyboardButton("📋 Таблицы", callback_data="admins_tables"))
                    markup.add(types.InlineKeyboardButton("🚗 Добавить машину", callback_data="admins_add_car"))

            elif status == 'new':
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(
                    "🏠 Бронировать квартиры Тольятти",
                    url="https://homereserve.ru/RRNTTTVoul?tag=%D1%82%D0%B5%D0%BB%D0%B5%D0%B3%D1%80%D0%B0%D0%BC"
                ))
                markup.add(types.InlineKeyboardButton("🚕 Заказать такси", callback_data="taxi"))
                markup.add(types.InlineKeyboardButton("🏎 Аренда авто", callback_data="rent"))
                markup.add(types.InlineKeyboardButton("⛽ Заправки", callback_data="gas"))
                markup.add(types.InlineKeyboardButton("🔧 Ремонт авто", callback_data="rext"))
                markup.add(types.InlineKeyboardButton("💼 Вакансии", callback_data="jobs"))
                markup.add(types.InlineKeyboardButton("📩 Написать директору", url="https://t.me/Dagman42"))

                if user_id == DIRECTOR_ID:
                    markup.add(types.InlineKeyboardButton("💰 Сменить цену топлива", callback_data="admin_set_price"))
                    markup.add(types.InlineKeyboardButton("🎁 Сменить бонусы", callback_data="admin_set_bonus"))
                    markup.add(types.InlineKeyboardButton("💸 Список вакансий", callback_data="admin_set_job"))
                    markup.add(types.InlineKeyboardButton("👤 Добавить оператора", callback_data="admin_set_operator"))
                    markup.add(types.InlineKeyboardButton("📢 Сделать рассылку", callback_data="admin_set_broadcast"))
                if user_id in ADMIN_IDS:
                    markup.add(types.InlineKeyboardButton("📋 Таблицы", callback_data="admins_tables"))
                    markup.add(types.InlineKeyboardButton("🚗 Добавить машину", callback_data="admins_add_car"))

                bot.send_message(user_id, "📋 Всё что вам нужно здесь", reply_markup=markup)

            elif status == 'waiting_rental':
                rental_menu_kb = types.InlineKeyboardMarkup()
                rental_menu_kb.add(
                    types.InlineKeyboardButton("🚕 Заказать такси", callback_data="taxi"),
                    types.InlineKeyboardButton("🏎 Аренда", callback_data="rent")
                )
                rental_menu_kb.add(
                    types.InlineKeyboardButton("⛽ Заправки", callback_data="gas"),
                    types.InlineKeyboardButton("🔧 Ремонт авто", callback_data="rext")
                )
                rental_menu_kb.add(
                    types.InlineKeyboardButton("💼 Вакансии", callback_data="jobs"),
                    types.InlineKeyboardButton("📩 Написать директору", url="https://t.me/Dagman42")
                )
                rental_menu_kb.add(
                    types.InlineKeyboardButton("❌ Отменить аренду", callback_data="cancel_rental"),
                    types.InlineKeyboardButton("📅 Перенести аренду", callback_data="reschedule_rental")
                )
                rental_menu_kb.add(
                    types.InlineKeyboardButton("🧾 Моя аренда", callback_data="my_rental")
                )

                if message.chat.id == DIRECTOR_ID:
                    rental_menu_kb.add(types.InlineKeyboardButton("💰 Сменить цену топлива", callback_data="admin_set_price"))
                    rental_menu_kb.add(types.InlineKeyboardButton("🎁 Сменить бонусы", callback_data="admin_set_bonus"))
                    rental_menu_kb.add(types.InlineKeyboardButton("💸 Список вакансий", callback_data="admin_set_job"))
                    rental_menu_kb.add(types.InlineKeyboardButton("👤 Добавить оператора", callback_data="admin_set_operator"))
                    rental_menu_kb.add(types.InlineKeyboardButton("📢 Сделать рассылку", callback_data="admin_set_broadcast"))
                if user_id in ADMIN_IDS:
                    rental_menu_kb.add(types.InlineKeyboardButton("📋 Таблицы", callback_data="admins_tables"))
                    rental_menu_kb.add(types.InlineKeyboardButton("🚗 Добавить машину", callback_data="admins_add_car"))

                bot.send_message(message.chat.id, "🚗 Выберите действие:", reply_markup=rental_menu_kb)

            else:
                print('Ошибка: неизвестный статус')

        else:
            # Новый пользователь
            try:
                bot.send_message(
                    user_id,
                    "👋 Добро пожаловать в официальный бот компании ЭЛИТ!\n\n"
                    "Здесь ты можешь арендовать авто и квартиру, заказать такси и многое другое.\n\n"
                    "Для начала давай познакомимся.\n\n"
                    "Как тебя зовут? 😊",
                    parse_mode='HTML'
                )
                bot.register_next_step_handler(message, get_name)
                return
            except Exception as e:
                print(f"Ошибка отправки сообщения новому пользователю: {e}")

    except Exception as e:
        print(f"Ошибка обработчика /start: {e}")


def get_name(message):
    try:
        chat_id = message.chat.id

        if not message.text or not message.text.strip():
            bot.send_message(chat_id, "❌ Пожалуйста, отправь имя текстом.")
            bot.register_next_step_handler(message, get_name)
            return

        user_data[chat_id] = {'name': message.text.strip()}

        # Запрос номера телефона
        contact_markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        contact_button = types.KeyboardButton(text="Отправить номер телефона", request_contact=True)
        contact_markup.add(contact_button)

        bot.send_message(chat_id, "Пожалуйста, поделись своим номером телефона:", reply_markup=contact_markup)
    except Exception as e:
        print(f"Ошибка 1804: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("admins_"))
def handle_admin_callbacks(call):
    user_id = call.from_user.id

    # проверка прав
    if user_id not in ADMIN_IDS:
        return bot.answer_callback_query(call.id, "⛔ У вас нет прав!")

    try:
        if call.data == "admins_tables":
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📋 Заявки", callback_data="admin_bookings"))
            markup.add(types.InlineKeyboardButton("👤 Пользователи", callback_data="admin_users"))
            markup.add(types.InlineKeyboardButton("Операторы", callback_data="admin_operators"))
            markup.add(types.InlineKeyboardButton("📊 Смены", callback_data="admin_shifts"))
            markup.add(types.InlineKeyboardButton("⛽ Заправки", callback_data="admin_gas"))
            markup.add(types.InlineKeyboardButton("🧼 Мойки", callback_data="admin_wash"))
            markup.add(types.InlineKeyboardButton(" 🚗 Машины", callback_data="admin_avtopark"))
            markup.add(types.InlineKeyboardButton("❓ Вопросы", callback_data="admin_questions"))
            bot.send_message(call.message.chat.id, "🛠 Админ-панель", reply_markup=markup)

        elif call.data == "admins_add_car":
            try:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                markup.add("Фольцваген Поло", "Шкода Рапид", "Рено Логан", "Шкода Октавия", "Джили Эмгранд")
                bot.send_message(call.message.chat.id, "Выберите модель автомобиля:", reply_markup=markup)
                set_state(call.message.chat.id, "admin_add_car_model")
            except Exception as e:
                print(f"Ошибка 7678: {e}")
    except Exception as e:
        print(f"[admin_callbacks] Ошибка: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "reschedule_rental")
def handle_reschedule_rental(call):
    try:
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        # Получаем последнюю бронь
        booking_id = get_last_booking_id(user_id)
        if not booking_id:
            bot.send_message(chat_id, "❌ Не найдено активной брони для переноса.")
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT car_id FROM bookings WHERE id = ?", (booking_id,))
        row = cursor.fetchone()
        if not row:
            bot.send_message(chat_id, "❌ Не удалось получить информацию о машине.")
            return

        car_id = row[0]

        # Сохраняем данные в сессии
        session = get_session(user_id)
        session["selected_car_id"] = car_id
        session["state"] = "waiting_for_rental_start"

        # Отправляем календарь для выбора новой даты
        bot.send_message(
            chat_id,
            "Теперь выберите дату для бронирования:",
            reply_markup=create_reset_calendar_markup(car_id, user_id)  # функция генерации календаря
        )

    except Exception as e:
        print(f"Ошибка handle_reschedule_rental: {e}")
        bot.send_message(chat_id, "❌ Произошла ошибка при переносе аренды.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("returning_deposit_booking_"))
def handle_return_deposit(call):
    try:
        # Разбираем данные callback
        parts = call.data[len("returning_deposit_booking_"):].split("_")
        booking_id = int(parts[0])
        user_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
        print(booking_id, user_id)
        # Вызываем cancel_booking безопасно
        cancel1_booking(booking_id, user_id)
        print(booking_id, user_id)
        bot.answer_callback_query(call.id, "Вы начали процесс возврата залога")

    except Exception as e:
        # Если user_id неизвестен, уведомляем админа или в лог
        if user_id:
            bot.send_message(user_id, f"❌ Ошибка при возврате залога: {e}")
        else:
            print(f"Ошибка при возврате залога для booking_id={booking_id}: {e}")


@bot.message_handler(func=lambda m: m.text == "❌ Отменить аренду")
def handle_cancel_rent(msg):
    try:
        chat_id = msg.chat.id

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("✅ Подтвердить отмену", "↩️ Назад")

        bot.send_message(
            chat_id,
            "⚠️ <b>Вы уверены, что хотите отменить аренду?</b>\n\n"
            "❗ При отмене в день начала аренды залог может быть возвращён не сразу или удержан частично, "
            "в зависимости от условий бронирования.\n\n"
            "Продолжить?",
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка 1846: {e}")
@bot.callback_query_handler(func=lambda call: call.data == "cancel_rental")
def handle_cancel_rental_callback(call):
    try:
        chat_id = call.message.chat.id
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("✅ Подтвердить отмену", "↩️ Назад")

        bot.send_message(
            chat_id,
            "⚠️ <b>Вы уверены, что хотите отменить аренду?</b>\n\n"
            "❗ При отмене в день начала аренды залог может быть возвращён не сразу или удержан частично, "
            "в зависимости от условий бронирования.\n\n"
            "Продолжить?",
            reply_markup=markup,
            parse_mode="HTML"
        )
        bot.answer_callback_query(call.id)

    except Exception as e:
        print(f"Ошибка 1846: {e}")

admin_states = {}  # {admin_id: {"state": "waiting_sum"/"waiting_reason", "booking_id": ..., "user_id": ..., "phone": ...}}

# --- 1. Клиент нажал "✅ Подтвердить отмену" ---
@bot.message_handler(func=lambda m: m.text == "✅ Подтвердить отмену")
def handle_confirm_cancel(msg):
    try:
        chat_id = msg.chat.id
        booking_id = get_last_booking_id(chat_id)
        if booking_id is None:
            bot.send_message(chat_id, "❌ Не найдено активной брони для отмены.")
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        # --- Достаём бронь + пользователя + машину ---
        cursor.execute("""
            SELECT b.id, b.user_id, b.car_id, b.date, b.time, b.service, 
                   u.phone, u.name, u.full_name, 
                   c.brand_model, c.number
            FROM bookings b
            JOIN users u ON b.user_id = u.telegram_id
            LEFT JOIN cars c ON b.car_id = c.car_id
            WHERE b.id = ?
        """, (booking_id,))
        booking = cursor.fetchone()
        conn.close()

        if not booking:
            bot.send_message(chat_id, "❌ Бронь не найдена.")
            return

        (booking_id, user_id, car_id, book_date, book_time, service,
         phone, name, full_name, brand_model, number) = booking

        today = datetime.now().date()
        bot.send_message(chat_id,
                         "✅ Ваша заявка на отмену аренды принята. Подождите одобрения возврата залога от администратора.")

        if service == "rent":
            rent_start = datetime.strptime(book_date, "%Y-%m-%d").date() + timedelta(days=1)
            text_admin = (
                f"⚠️ Клиент <b>{full_name or name}</b> (тел: {phone})\n"
                f"отменил аренду машины <b>{brand_model} {number}</b>\n"
                f"⏰ Сейчас: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                f"📅 Аренда должна была начаться: {rent_start.strftime('%d.%m.%Y')}\n\n"
                f"❓ Какой залог вернуть клиенту?"
            )
            # Сохраняем состояние админа
            admin_states[ADMIN_ID2] = {
                "state": "waiting_sum",
                "booking_id": booking_id,
                "user_id": user_id,
                "car_id": car_id
            }
            bot.send_message(ADMIN_ID2, text_admin, parse_mode="HTML")

        elif service == "rental":
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT rent_start FROM rental_history
                WHERE user_id = ? AND car_id = ? AND status = 'confirmed'
                ORDER BY id DESC LIMIT 1
            """, (user_id, car_id))
            rent_row = cursor.fetchone()
            conn.close()

            rent_start = datetime.strptime(rent_row[0], "%Y-%m-%d").date() if rent_row else None

            if rent_start and (rent_start == today or rent_start == today + timedelta(days=1)):
                text_admin = (
                    f"⚠️ Клиент <b>{full_name or name}</b> (тел: {phone})\n"
                    f"отменил аренду машины <b>{brand_model} {number}</b>\n"
                    f"⏰ Сейчас: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"📅 Аренда должна была начаться: {rent_start.strftime('%d.%m.%Y')}\n\n"
                    f"❓ Какой залог вернуть клиенту?"
                )
                admin_states[ADMIN_ID2] = {
                    "state": "waiting_sum",
                    "booking_id": booking_id,
                    "user_id": user_id,
                    "car_id": car_id
                }
                bot.send_message(ADMIN_ID2, text_admin, parse_mode="HTML")
            else:
                cancel1_booking(booking_id, chat_id)

        else:
            cancel1_booking(booking_id, chat_id)

    except Exception as e:
        print(f"Ошибка handle_confirm_cancel: {e}")
# --- 2. Обработка кнопок суммы ---
@bot.callback_query_handler(func=lambda c: c.data.startswith("deposit_"))
def handle_admin_deposit(c):
    try:
        parts = c.data.split("_")
        deposit_type = parts[1]
        booking_id = int(parts[2])
        user_id = int(parts[3])
        admin_id = c.from_user.id

        if deposit_type == "10000":
            cancel1_booking(booking_id, user_id)
            bot.send_message(admin_id, "✅ Аренда отменена, залог возвращён полностью.")
        elif deposit_type == "custom":
            # Запоминаем состояние для ввода суммы вручную
            admin_states[admin_id] = {"state": "waiting_sum", "booking_id": booking_id, "user_id": user_id}
            bot.send_message(admin_id, "Введите сумму залога вручную:")
        bot.answer_callback_query(c.id)
    except Exception as e:
        print(f"[ERROR] Ошибка 2305: {e}")

refund_states = {}
# --- 3. Обработка сообщений админа для ручного ввода суммы и причины ---
@bot.message_handler(func=lambda message: admin_states.get(message.from_user.id, {}).get("state") in ["waiting_sum", "waiting_reason"])
def handle_admin_refund(message):
    try:
        admin_id = message.from_user.id
        state_data = admin_states.get(admin_id)
        if not state_data:
            return

        text = message.text.strip()
        booking_id = state_data["booking_id"]
        user_id = state_data["user_id"]
        car_id = state_data.get("car_id")

        # --- Ждём сумму ---
        if state_data["state"] == "waiting_sum":
            if not text.isdigit():
                bot.send_message(admin_id, "⚠️ Введите сумму числом или напишите 'отмена'.")
                return

            deposit_sum = int(text)
            if deposit_sum <= 0:
                bot.send_message(admin_id, "⚠️ Сумма должна быть больше нуля.")
                return

            if deposit_sum == 10000:
                cancel1_booking(booking_id, user_id)
                admin_states.pop(admin_id, None)
                bot.send_message(admin_id, "✅ Аренда отменена, залог возвращён полностью.")
            else:
                state_data["sum"] = deposit_sum
                state_data["state"] = "waiting_reason"
                admin_states[admin_id] = state_data
                bot.send_message(admin_id, f"❓ Укажите причину удержания из {deposit_sum} руб. или напишите 'отмена'.")

        # --- Ждём причину ---
        elif state_data["state"] == "waiting_reason":
            reason = text
            if len(reason) < 5:
                bot.send_message(admin_id, "⚠️ Причина должна содержать хотя бы 5 символов или напишите 'отмена'.")
                return

            deposit_sum = state_data["sum"]

            # Сохраняем для кассира
            refund_states[booking_id] = {
                "user_id": user_id,
                "deposit_sum": deposit_sum,
                "reason": reason,
                "car_id": car_id
            }

            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("💸 Вернуть залог", callback_data=f"refund_{booking_id}"))

            # Получаем телефон клиента
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT phone FROM users WHERE telegram_id=?", (user_id,))
            phone_row = cursor.fetchone()
            phone = phone_row[0] if phone_row else "неизвестен"
            conn.close()

            text_dan = (
                f"📢 Пожалуйста, отправьте на номер <b>{phone}</b>\n"
                f"залог в размере <b>{deposit_sum} руб.</b>\n\n"
                f"Причина штрафа: {reason}"
            )
            bot.send_message(DAN_TELEGRAM_ID, text_dan, parse_mode="HTML", reply_markup=kb)

            admin_states.pop(admin_id, None)
            bot.send_message(admin_id, "✅ Информация передана кассиру.")

    except Exception as e:
        print(f"Ошибка handle_admin_refund: {e}")

# --- 4. Кнопка "Вернуть залог" кассиру ---

def get_last_booking_id(user_id):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM bookings WHERE user_id = ? AND status = 'confirmed' ORDER BY id DESC LIMIT 1",
                (user_id,)
            )
            row = cursor.fetchone()
            if row:
                return row["id"]
            return None
    except Exception as e:
        bot.send_message(user_id, f"❌ Ошибка при получении брони: {e}")
        return None

@bot.callback_query_handler(func=lambda call: call.data.startswith("refund_"))
def handle_refund_confirm(call):
    try:
        booking_id = int(call.data.split("_")[1])

        if booking_id not in refund_states:
            bot.answer_callback_query(call.id, "❌ Данные для этой заявки не найдены.")
            return

        data = refund_states.pop(booking_id)
        user_id = data["user_id"]
        deposit_sum = data["deposit_sum"]
        reason = data["reason"]
        car_id = data.get("car_id")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Освобождаем машину
        if car_id:
            cursor.execute("UPDATE cars SET is_available=1 WHERE car_id=?", (car_id,))

        # Удаляем бронь
        cursor.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
        cursor.execute("DELETE FROM rental_history WHERE user_id=? AND car_id=? AND status='confirmed'", (user_id, car_id))

        # Меняем статус пользователя
        cursor.execute("UPDATE users SET status='new' WHERE telegram_id=?", (user_id,))
        conn.commit()
        conn.close()

        # Сообщение клиенту
        bot.send_message(user_id, f"✅ Вам вернули залог в размере <b>{deposit_sum} руб.</b>\nПричина: {reason}", parse_mode="HTML")
        bot.send_message(DAN_TELEGRAM_ID, "✅ Залог возвращён, заявка закрыта.")
        bot.answer_callback_query(call.id, "Залог успешно возвращён.")

    except Exception as e:
        print(f"Ошибка handle_refund_confirm: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при возврате.")
def cancel1_booking(booking_id, user_id):
    try:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Если user_id не передан, получаем его из брони
                if user_id is None:
                    cursor.execute("SELECT user_id FROM bookings WHERE id = ?", (booking_id,))
                    row = cursor.fetchone()
                    if row is None:
                        return
                    user_id = row["user_id"]

                # Отменяем бронь
                cursor.execute("UPDATE bookings SET status = 'reject' WHERE id = ?", (booking_id,))
                conn.commit()

                # Сбрасываем статус пользователя
                cursor.execute("UPDATE users SET status = 'new' WHERE telegram_id = ?", (user_id,))
                conn.commit()

                # Получаем данные клиента
                cursor.execute("SELECT name, phone FROM users WHERE telegram_id = ?", (user_id,))
                user = cursor.fetchone()

        except Exception as e:
            bot.send_message(user_id, f"❌ Ошибка при отмене: {e}")
            return

        bot.send_message(user_id, "❌ Аренда отменена. Залог вернётся в течение 5 суток.",
                         reply_markup=types.ReplyKeyboardRemove())

        if user:
            name = user['name']
            phone = user['phone']
            admin_text = (
                f"🚫 <b>Клиент отменил аренду</b>\n\n"
                f"👤 Имя: <b>{name}</b>\n"
                f"📞 Телефон: <b>{phone}</b>\n"
                f"🧾 Telegram ID: <code>{user_id}</code>"
            )
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("💸 Залог возвращён", callback_data=f"deposit_returned_{user_id}"))
            bot.send_message(ADMIN_ID2, admin_text, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка 1927: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("deposit_returned_"))
def handle_deposit_returned(call):
    client_id = int(call.data.split("_")[-1])

    try:
        bot.send_message(client_id, "✅ Ваш залог был возвращён!")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Не удалось уведомить клиента: {e}")


@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    try:
        chat_id = message.chat.id
        phone = message.contact.phone_number

        if chat_id not in user_data:
            bot.send_message(chat_id, "❗ Произошла ошибка: данные не найдены. Пожалуйста, начни сначала /start")
            return

        name = user_data[chat_id]['name']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                    INSERT OR IGNORE INTO users (telegram_id, name, phone, status)
                    VALUES (?, ?, ?, ?)
                ''', (chat_id, name, phone, 'new'))
            conn.commit()
        except Exception as e:
            bot.send_message(chat_id, f"❗ Ошибка при сохранении данных: {e}")
            return
        finally:
            conn.close()

        bot.send_message(
            chat_id,
            f"📱 Спасибо за номер, <b>{name}</b>!\n"
            f"Телефон: {phone}\n\n"
            "Теперь ты готов пользоваться нашим сервисом — выбирай! 🚗",
            parse_mode='HTML',
            reply_markup=types.ReplyKeyboardRemove()
        )

        # Единый список кнопок
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                "🏠 Смотреть квартиры Тольятти",
                url="https://homereserve.ru/RRNTTTVoul?tag=%D1%82%D0%B5%D0%BB%D0%B5%D0%B3%D1%80%D0%B0%D0%BC"
            )
        )
        markup.add(InlineKeyboardButton("🚕 Заказать такси", callback_data="taxi"))
        markup.add(InlineKeyboardButton("🏎 Аренда", callback_data="rent"))
        markup.add(InlineKeyboardButton("⛽ Заправки", callback_data="gas"))
        markup.add(InlineKeyboardButton("🔧 Ремонт авто", callback_data="rext"))
        markup.add(InlineKeyboardButton("💼 Вакансии", callback_data="jobs"))
        markup.add(types.InlineKeyboardButton("📩 Написать директору", url="https://t.me/Dagman42"))

        bot.send_message(chat_id, "📋 Выберите действие:", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка 1993: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "elite_cars")
def handle_elite_main_menu(call):
    try:
        rental_menu_kb = InlineKeyboardMarkup()
        rental_menu_kb.add(
            InlineKeyboardButton("🚕 Заказать такси", callback_data="taxi"),
            InlineKeyboardButton("🏎 Аренда", callback_data="rent")
        )
        rental_menu_kb.add(
            InlineKeyboardButton("⛽ Заправки", callback_data="gas"),
            InlineKeyboardButton("🔧 Ремонт авто", callback_data="rext")
        )
        rental_menu_kb.add(
            InlineKeyboardButton("💼 Вакансии", callback_data="jobs"),
            InlineKeyboardButton("📩 Написать директору", url="https://t.me/Dagman42")
        )
        rental_menu_kb.add(

            InlineKeyboardButton("❌ Отменить аренду", callback_data="cancel_rental"),
            InlineKeyboardButton("📅 Перенести аренду", callback_data="reschedule_rental")  # новая кнопка
        )
        rental_menu_kb.add(
            InlineKeyboardButton("🧾 Моя аренда", callback_data="my_rental")
        )
        bot.send_message(
            call.message.chat.id,
            "🚗 Выберите действие:",
            reply_markup=rental_menu_kb
        )
    except Exception as e:
        print(f"Ошибка 1812: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "my_rental")
def handle_my_rental(call):
    try:
        user_id = call.from_user.id

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # 1️⃣ Проверяем длительную аренду
            cur.execute("""
                    SELECT rh.rent_start, rh.rent_end, rh.car_id,
                           c.brand_model, c.price
                    FROM rental_history rh
                    JOIN cars c ON rh.car_id = c.car_id
                    WHERE rh.user_id = ? AND rh.status = 'confirmed'
                    ORDER BY rh.id DESC LIMIT 1
                """, (user_id,))
            row = cur.fetchone()

            if row:  # Есть rental
                rent_start = datetime.strptime(row["rent_start"], "%Y-%m-%d").date()
                rent_end = datetime.strptime(row["rent_end"], "%Y-%m-%d").date()
                base_price = row["price"]

                days = (rent_end - rent_start).days
                total_price = calculate_price(base_price, days)

                text = (
                    f"🚗 <b>Ваша аренда:</b>\n\n"
                    f"📅 Срок: с {rent_start.strftime('%d.%m.%Y')} по {rent_end.strftime('%d.%m.%Y')} ({days} дней)\n"
                    f"💰 Стоимость аренды: <b>{total_price:,} ₽</b>\n"
                    f"🔒 <b>Залог 10 000 ₽</b> (вернётся сразу после сдачи и проверки автомобиля)\n\n"
                    f"❓ Оплата арендной платы происходит в назначенную дату"
                )
                bot.send_message(call.message.chat.id, text, parse_mode="HTML")
                return

            # 2️⃣ Проверяем краткосрочную аренду (rent)
            cur.execute("""
                    SELECT b.created_at, b.deposit_status, c.brand_model, c.year
                    FROM bookings b
                    JOIN cars c ON b.car_id = c.car_id
                    WHERE b.user_id = ?
                      AND b.service = 'rent'
                      AND b.status = 'confirmed'
                    ORDER BY b.id DESC LIMIT 1
                """, (user_id,))
            booking = cur.fetchone()

            if booking:
                created_date = datetime.strptime(booking["created_at"], "%Y-%m-%d %H:%M:%S").date()
                rent_start_date = created_date + timedelta(days=1)  # аренда завтра
                deposit_status = "Оплачен" if booking["deposit_status"] == "paid" else "Не оплачен"

                text = (
                    f"🚗 <b>Ваша аренда:</b>\n\n"
                    f"🚘 {booking['brand_model']} ({booking['year']})\n"
                    f"💳 Залог: <b>{deposit_status}</b>\n"
                    f"📅 Начало аренды: {rent_start_date.strftime('%d.%m.%Y')} (завтра)\n\n"
                    f"Забрать автомобиль можно с 12:00."
                )
                bot.send_message(call.message.chat.id, text, parse_mode="HTML")
                return

            # 3️⃣ Если ничего нет
            bot.send_message(call.message.chat.id, "🚫 У вас нет активной аренды.")

            # markup = InlineKeyboardMarkup()
            # markup.add(
            #     InlineKeyboardButton("💳 Оплатить сейчас", callback_data="pay_now"),
            #     InlineKeyboardButton("🕒 Оплатить на месте", callback_data="pay_on_spot")
            # )
    except Exception as e:
        print(f"Ошибка 2095: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "pay_now")
def handle_pay_now(call):
    try:
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "💳 Отлично! Чтобы оплатить аренду онлайн, перейдите по ссылке ниже:\n\n"
            "<a href='https://your-payment-link.com'>Перейти к оплате</a>\n\n"
            "📸 После оплаты отправьте скриншот чека.",
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Ошибка 2111: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "pay_on_spot")
def handle_pay_on_spot(call):
    try:
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "🕒 Хорошо, аренду можно будет оплатить на месте в день начала проката.\n\n"
            "📲 Мы заранее сообщим, когда и куда подъехать."
        )
    except Exception as e:
        print(f"Ошибка 2124: {e}")


@bot.message_handler(commands=['clear_all_user'])
def clear_all_users(message):
    admin_id = message.from_user.id

    if admin_id != ADMIN_ID2:
        bot.send_message(message.chat.id, "❌ У вас нет прав для этой команды.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
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
    try:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🎁 Баллы", callback_data="fuel_bonuses"))
        markup.add(InlineKeyboardButton("📍 Точки", callback_data="fuel_locations"))
        markup.add(InlineKeyboardButton("⛽️ Заправиться", callback_data="choose_address"))
        bot.send_message(call.message.chat.id, "Заправки Элит Газ:", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка 2165: {e}")


def reset_state(chat_id):
    try:
        user_sessions[chat_id] = {
            "station": None,
            "column": None,
            "fuel": None,
            "amount_type": None,
            "amount": None,
            "payment_method": None
        }
    except Exception as e:
        print(f"Ошибка 2179: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("fuel_"))
def handle_fuel(call):
    try:
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        data = call.data.replace("fuel_", "")

        # 🔹 Если была сессия изменения цены — очищаем
        if chat_id in price_change_sessions:
            print(1)
            del price_change_sessions[chat_id]

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

            user_sessions[chat_id]['amount'] = None  # 🔹 сброс суммы при новой заправке

            user_sessions[chat_id]['amount_type'] = None  # 🔹 можно сбросить и тип (чтобы точно не было мусора)

            markup = InlineKeyboardMarkup()

            markup.add(

                InlineKeyboardButton("₽ Рубли", callback_data="amount_rub"),

                InlineKeyboardButton("Литры", callback_data="amount_litres"),

                InlineKeyboardButton("Полный бак", callback_data="fulltank")

            )

            bot.edit_message_text("Введите сумму в рублях или литрах:", chat_id, call.message.message_id,

                                  reply_markup=markup)
        cursor.close()
        conn.close()
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Ошибка 2246: {e}")


def generate_qr_code(data: str) -> BytesIO:
    try:
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        bio = BytesIO()
        bio.name = 'qr.png'
        img.save(bio, 'PNG')
        bio.seek(0)
        return bio
    except Exception as e:
        print(f"Ошибка 2261: {e}")


def delete_last_message(chat_id):
    try:
        message_id = user_sessions.get(chat_id, {}).get('last_message_id')
        if message_id:
            try:
                bot.delete_message(chat_id, message_id)
            except Exception as e:
                print(f"[Удаление] Ошибка удаления сообщения {message_id}: {e}")
    except Exception as e:
        print(f"Ошибка 2273: {e}")


@bot.callback_query_handler(func=lambda call: call.data in ["start_scan", "choose_address"])
def handle_start_choice(call):
    try:
        chat_id = call.message.chat.id
        delete_last_message(chat_id)

        if call.data == "start_scan":
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📷 Сканировать QR",
                                            web_app=WebAppInfo(url="https://doctor-eggman444.github.io/qr-scanner/")))
            msg = bot.send_message(chat_id, "Нажмите кнопку и отсканируйте QR-код на заправке:", reply_markup=markup)

        elif call.data == "choose_address":
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Южное шоссе 129 (около АвтоВАЗа)", callback_data="station_1"))
            markup.add(InlineKeyboardButton("Южное шоссе 12/2 (пересечение с ул.Полякова)", callback_data="station_2"))
            markup.add(InlineKeyboardButton("Лесная 66А (Центральный р-н)", callback_data="station_3"))
            markup.add(InlineKeyboardButton("Борковская 72/1 (Восточное кольцо)", callback_data="station_4"))

        bot.send_message(chat_id, "📍 Выберите адрес:", reply_markup=markup)

        user_sessions[chat_id] = user_sessions.get(chat_id, {})
        user_sessions[chat_id]['last_message_id'] = call.message.message_id
    except Exception as e:
        print(f"Ошибка 2300: {e}")


@bot.message_handler(content_types=["web_app_data"])
def handle_qr(message):
    try:
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

    except Exception as e:
        print(f"Ошибка 2359: {e}")

def safe_remove_buttons(chat_id, message_id):
    try:
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
    except Exception as e:
        if "message is not modified" in str(e):
            pass  # кнопки уже нет — игнорируем
        else:
            print(f"[UI ERROR] {e}")

# Хелпер для безопасного редактирования текста
def safe_edit_message_text(new_text, chat_id, message_id, reply_markup=None):
    try:
        old_text = ""  # по умолчанию, если text недоступен
        try:
            old_text = bot.get_message(chat_id, message_id).text
        except:
            pass
        if old_text != new_text:
            bot.edit_message_text(new_text, chat_id, message_id, reply_markup=reply_markup)
        else:
            # Меняем только кнопки, если текст не изменился
            if reply_markup is not None:
                safe_remove_buttons(chat_id, message_id)
    except Exception as e:
        if "message is not modified" in str(e):
            pass
        else:
            print(f"[UI ERROR] {e}")


@bot.callback_query_handler(func=lambda call: isinstance(call.data, str) and call.data.startswith(
    ("station_", "column_", "accepted_", "amount_", "pay_", "confirm", "cancel")
))
def callback_handler(call):
    try:
        chat_id = call.message.chat.id
        data = call.data

        # Удаляем старые кнопки безопасно
        safe_remove_buttons(chat_id, call.message.message_id)

        # Убедимся, что сессия для пользователя существует
        if chat_id not in user_sessions:
            user_sessions[chat_id] = {}

        # === Выбор станции ===
        if data.startswith("station_"):
            station_code = data
            user_sessions[chat_id]['station'] = station_code

            # Проверка наличия активной смены
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT 1 
                        FROM shifts 
                        WHERE station = ? AND active = 1
                        LIMIT 1
                    """, (station_code,))
                    shift_exists = cursor.fetchone() is not None

                if not shift_exists:
                    bot.answer_callback_query(call.id,
                                              "❌ На этой заправке через ТГ бота отключена. Платите напрямую оператору или попросите его включить ТГ бота.",
                                              show_alert=True)
                    return

            except Exception as e:
                print(f"[DB ERROR] {e}")
                bot.answer_callback_query(call.id, "⚠️ Ошибка при проверке смены.", show_alert=True)
                return

            # Показываем выбор колонки
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("1", callback_data="column_1"),
                InlineKeyboardButton("2", callback_data="column_2")
            )
            safe_edit_message_text("Выберите колонку:", chat_id, call.message.message_id, reply_markup=markup)

        # === Выбор колонки ===
        elif data.startswith("column_"):
            user_sessions[chat_id]['column'] = data.split("_")[1]
            station_code = user_sessions[chat_id].get('station')

            if station_code in ["station_3", "station_4"]:
                user_sessions[chat_id]['fuel'] = 'gaz'  # Газ по умолчанию

                markup = InlineKeyboardMarkup()
                markup.add(
                    InlineKeyboardButton("₽ Рубли", callback_data="amount_rub"),
                    InlineKeyboardButton("Литры", callback_data="amount_litres"),
                    InlineKeyboardButton("Полный бак", callback_data="fulltank")
                )
                safe_edit_message_text("На этой станции доступен только газ.\nВыберите способ ввода:", chat_id,
                                       call.message.message_id, reply_markup=markup)
            else:
                markup = InlineKeyboardMarkup()
                markup.add(
                    InlineKeyboardButton("Бензин", callback_data="fuel_benzin"),
                    InlineKeyboardButton("Газ", callback_data="fuel_gaz")
                )
                safe_edit_message_text("Выберите тип топлива:", chat_id, call.message.message_id, reply_markup=markup)

        # === Выбор способа ввода суммы или литров ===
        elif data in ["amount_rub", "amount_litres"]:
            user_sessions[chat_id]['amount_type'] = 'rub' if data == 'amount_rub' else 'litres'
            bot.send_message(chat_id, "Введите значение:")

        # === Подтверждение или отмена ===
        elif data == "confirm":
            client_chat_id = chat_id
            session = user_sessions.get(client_chat_id, {})
            litres = float(session.get('litres', 0))
            fuel = session.get('fuel')
            price = 0
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT price_per_litre FROM fuel WHERE fuel_type = ? LIMIT 1", (fuel,))
                    row = cur.fetchone()
                    if row:
                        price = row[0]
            except Exception as e:
                print(f"[fuel price] Ошибка: {e}")

            rub = round(litres * price, 2)

            if client_chat_id not in price_change_sessions:
                price_change_sessions[client_chat_id] = {}

            price_change_sessions[client_chat_id]['litres'] = litres
            price_change_sessions[client_chat_id]['status'] = 'litres_entered'

            # Проверяем бонусы пользователя
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT bonus FROM users WHERE telegram_id = ?", (client_chat_id,))
                    row = cur.fetchone()
                    current_bonus = int(row[0]) if row and row[0] else 0
            except Exception as e:
                print(f"[bonus check] Ошибка: {e}")
                current_bonus = 0

            markup_client = InlineKeyboardMarkup()
            markup_client.add(
                InlineKeyboardButton("💵 Наличные", callback_data=f"payment_cash_full_{client_chat_id}"),
                InlineKeyboardButton("💳 Карта", callback_data=f"payment_card_full_{client_chat_id}")
            )

            if current_bonus >= rub:
                markup_client.add(
                    InlineKeyboardButton("🎁 Оплатить баллами", callback_data=f"paying_bonus_full_{client_chat_id}")
                )

            text_client = f"Выберите способ оплаты:\nСумма: {rub} ₽"
            bot.send_message(client_chat_id, text_client, reply_markup=markup_client)

        elif data == "cancel":
            reset_state(chat_id)
            bot.send_message(chat_id, "❌ Операция отменена.")
            choose_address_menu(chat_id)

    except Exception as e:
        print(f"Ошибка 2578: {e}")


def choose_address_menu(chat_id):
    try:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Южное шоссе 129 (около АвтоВАЗа)", callback_data="station_1"))
        markup.add(InlineKeyboardButton("Южное шоссе 12/2 (пересечение с ул.Полякова)", callback_data="station_2"))
        markup.add(InlineKeyboardButton("Лесная 66А (Центральный р-н)", callback_data="station_3"))
        markup.add(InlineKeyboardButton("Борковская 72/1 (Восточное кольцо)", callback_data="station_4"))

        bot.send_message(chat_id, "📍 Выберите адрес:", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка 2591: {e}")


@bot.message_handler(func=lambda m: (
        m.chat.id in user_sessions and
        user_sessions[m.chat.id].get('amount_type') and
        user_sessions[m.chat.id].get('amount') is None and
        user_sessions[m.chat.id].get('amount_type') != 'fulltank'
))
def amount_input_handler(msg):
    try:
        chat_id = msg.chat.id
        try:
            amount = float(msg.text.replace(',', '.'))
        except ValueError:
            safe_send(chat_id, "❌ Введите корректное число")
            return

        with sessions_lock:
            user_sessions.setdefault(chat_id, {})['amount'] = amount

        # удаляем старое сообщение
        last_msg_id = user_sessions[chat_id].get("last_bot_msg_id")
        if last_msg_id:
            try:
                bot.delete_message(chat_id, last_msg_id)
            except Exception as e:
                logger.warning("[!] Не удалось удалить сообщение: %s", e)

        data = user_sessions.get(chat_id, {})
        fuel_name = 'Бензин' if data.get('fuel') == 'benzin' else 'Газ'

        # используем safe helper
        price = get_price_per_litre_safe(data.get('fuel'))
        if not price or price == 0:
            safe_send(chat_id, "❌ Не удалось получить цену топлива. Попробуйте выбрать колонку/станцию снова.")
            return

        if data.get('amount_type') == 'rub':
            litres = round(amount / price, 2)
            rub = amount
        else:
            litres = amount
            rub = round(amount * price, 2)

        with sessions_lock:
            user_sessions[chat_id]['litres'] = litres

        confirm_text = (f"🧾 Проверьте данные:\n"
                        f"Станция: {STATION_NAMES.get(data.get('station'), 'Неизвестно')}\n"
                        f"Колонка: {data.get('column')}\n"
                        f"Топливо: {fuel_name}\n"
                        f"Объём: {litres} л\n"
                        f"Сумма: {rub:.2f} ₽")

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Верно", callback_data="confirm"),
            InlineKeyboardButton("❌ Отмена", callback_data="cancel")
        )
        sent = safe_send(chat_id, confirm_text, reply_markup=markup)
        if sent:
            with sessions_lock:
                user_sessions[chat_id]['last_bot_msg_id'] = sent.message_id
    except Exception:
        logger.exception("Ошибка в amount_input_handler")
        safe_send(msg.chat.id, "❌ Внутренняя ошибка. Администратор уведомлен.")

def finalize_order(chat_id):
    try:
        data = user_sessions.get(chat_id, {}) or {}
        required_fields = ['station', 'column', 'fuel', 'amount_type', 'amount', 'payment_method']
        missing = [field for field in required_fields if data.get(field) is None]
        if missing:
            safe_send(chat_id, f"❌ Не хватает данных: {', '.join(missing)}. Попробуйте заново.")
            reset_state(chat_id)
            return

        if data.get('amount_type') == 'fulltank':
            start_full_tank_procedure(chat_id)
            return

        fuel = data.get('fuel')
        price = get_price_per_litre_safe(fuel, data.get('payment_method'))
        if price == 0:
            safe_send(chat_id, "❌ Не удалось определить цену топлива. Попробуйте позже.")
            return

        if data['amount_type'] == 'rub':
            litres = round(data['amount'] / price, 2)
            rub = data['amount']
        else:
            litres = data['amount']
            rub = round(data['amount'] * price, 2)

        station_code = data.get('station')
        station_name = STATION_NAMES.get(station_code, "Неизвестно")
        operator_id = OPERATORS.get(station_code)

        with sessions_lock:
            user_sessions[chat_id].update({
                'rub': rub,
                'litres': litres,
                'station_name': station_name,
                'fuel_name': ('Бензин' if fuel == 'benzin' else 'Газ'),
            })

        message = (f"🧾 Новый заказ\n"
                   f"Станция: {station_name}\n"
                   f"Колонка: {data.get('column')}\n"
                   f"Топливо: {('Бензин' if fuel == 'benzin' else 'Газ')}\n"
                   f"Объем: {litres} л\n"
                   f"Сумма: {rub:.2f} ₽\n"
                   f"Оплата: {'💵 Наличные' if data.get('payment_method') == 'cash' else '💳 Безнал'}")

        if data.get('payment_method') == 'cash':
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("✅ Принял", callback_data=f"accepted_{chat_id}"))
            if operator_id:
                safe_send(operator_id, message, reply_markup=markup)
            else:
                logger.warning("finalize_order: operator_id is None for station %s", station_code)
                notify_admin(f"[WARN] Не найден оператор для {station_code}, заказ {chat_id} не отправлен оператору.")
            safe_send(chat_id, "✅ Отлично! Подойдите и оплатите свой заказ.")
        else:
            safe_send(chat_id, f"💳 Ссылка на оплату (заглушка): https://pay.tinkoff.ru")
            if operator_id:
                safe_send(operator_id, message)
            save_to_db(chat_id)
    except Exception:
        logger.exception("Ошибка в finalize_order")
        safe_send(chat_id, "❌ Произошла внутренняя ошибка при формировании заказа.")


def start_full_tank_procedure(chat_id):
    try:
        data = user_sessions[chat_id]
        station_code = data.get('station')
        column = data.get('column')
        fuel = data.get('fuel')
        fuel_name = 'Бензин' if fuel == 'benzin' else 'Газ'
        operator_id = OPERATORS.get(station_code)

        text = (f"🚩 Новый заказ: Полный бак\n"
                f"Станция: {STATION_NAMES.get(station_code, 'Неизвестно')}\n"
                f"Колонка: {column}\n"
                f"Топливо: {fuel_name}")

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🚀 Начинаю заправку", callback_data=f"full_tank_start_{chat_id}"))

        if operator_id:
            bot.send_message(operator_id, text, reply_markup=markup)

        bot.send_message(chat_id, "🕐 Оператор скоро начнет заправку. Пожалуйста, подождите.")
    except Exception as e:
        print(f"Ошибка 2728: {e}")


def add_bonus(user_id, litres, fuel, payment_method):
    print(user_id, litres, fuel, payment_method)
    try:
        """Начисляет бонусы пользователю за литры топлива по таблице fuel"""
        if litres <= 0:
            return 0, 0

        bonus_to_add = 0
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()

                # 🔹 Получаем коэффициент бонусов для конкретного топлива и метода оплаты
                cur.execute(
                    "SELECT bonuses FROM fuel WHERE fuel_type = ? AND payment_method = ? LIMIT 1",
                    (fuel, payment_method)
                )
                row = cur.fetchone()
                if not row:
                    print(f"[add_bonus] Нет настроек бонусов для {fuel} ({payment_method})")
                    return 0, 0

                bonus_per_litre = float(row[0])
                bonus_to_add = round(litres * bonus_per_litre, 2)

                # Проверяем, есть ли пользователь
                cur.execute("SELECT bonus FROM users WHERE telegram_id = ?", (user_id,))
                row = cur.fetchone()

                if row is None:
                    # Если пользователя нет — создаём запись
                    cur.execute(
                        "INSERT INTO users (telegram_id, bonus) VALUES (?, ?)",
                        (user_id, bonus_to_add)
                    )
                    conn.commit()
                    return bonus_to_add, bonus_to_add

                current_bonus = float(row[0] or 0)
                new_bonus = round(current_bonus + bonus_to_add, 2)

                cur.execute("UPDATE users SET bonus = ? WHERE telegram_id = ?", (new_bonus, user_id))
                conn.commit()
                return bonus_to_add, new_bonus

        except Exception as e:
            print(f"[add_bonus] Ошибка при работе с БД: {e}")
            return 0, 0
    except Exception as e:
        print(f"Ошибка 2760: {e}")
        return 0, 0

price_change_sessions = {}


@bot.callback_query_handler(func=lambda call: call.data.startswith("full_tank_start_"))
def handle_full_tank_start(call):
    try:
        operator_chat_id = call.from_user.id
        client_chat_id = int(call.data.split("_")[-1])

        # Запоминаем, что оператор начал заправку для клиента
        price_change_sessions[client_chat_id] = {
            'status': 'started',
            'operator_chat_id': operator_chat_id
        }

        try:
            bot.edit_message_text(
                "Заправка начата. Когда закончите, отправьте количество литров:",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )
        except Exception as e:
            print(f"Ошибка при редактировании сообщения: {e}")

        bot.send_message(client_chat_id, "🚀 Оператор начал заправку вашего полного бака. Пожалуйста, дождитесь окончания.")
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Ошибка 2790: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("fulltank"))
def handle_fulltank_callback(call):
    try:
        chat_id = call.from_user.id
        # Удаляем кнопки у сообщения с кнопками выбора
        try:
            bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          reply_markup=None)
        except Exception as e:
            print(f"Ошибка при удалении кнопок: {e}")

        user_sessions[chat_id]['amount_type'] = 'fulltank'
        start_full_tank_procedure(chat_id)
    except Exception as e:
        print(f"Ошибка 2808: {e}")


@bot.message_handler(func=lambda m: any(
    data.get('operator_chat_id') == m.chat.id and data.get('status') == 'started'
    for data in price_change_sessions.values()
))
def handle_full_tank_litres_input(message):
    try:
        operator_chat_id = message.chat.id
        client_chat_id = None
        with sessions_lock:
            for cid, data in price_change_sessions.items():
                if data.get('operator_chat_id') == operator_chat_id and data.get('status') == 'started':
                    client_chat_id = cid
                    break

        if client_chat_id is None:
            safe_send(operator_chat_id, "❌ Не удалось определить клиента для этого заказа.")
            return

        try:
            litres = float(message.text.replace(',', '.'))
        except ValueError:
            safe_send(operator_chat_id, "❌ Введите корректное число литров.")
            return

        with sessions_lock:
            price_change_sessions[client_chat_id]['litres'] = litres
            price_change_sessions[client_chat_id]['status'] = 'litres_entered'

        session = user_sessions.get(client_chat_id, {}) or {}
        fuel = session.get('fuel')
        price = get_price_per_litre_safe(fuel)
        if price == 0:
            safe_send(operator_chat_id, "❌ Не удалось получить цену топлива для расчёта. Проверьте БД.")
            notify_admin(f"[ERROR] price==0 for fuel={fuel} client={client_chat_id}")
            return

        rub = round(litres * price, 2)
        fuel_name = 'Бензин' if fuel == 'benzin' else 'Газ'
        text_client = (
            f"⛽ В ваш бак вошло {litres:.2f} л {fuel_name}.\n"
            f"К оплате: {rub:.2f} ₽\n"
            "Выберите способ оплаты:"
        )

        try:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute("SELECT bonus FROM users WHERE telegram_id = ?", (client_chat_id,))
                row = cur.fetchone()
                current_bonus = int(row[0]) if row and row[0] else 0
        except Exception:
            logger.exception("bonus check failed")
            current_bonus = 0

        markup_client = InlineKeyboardMarkup()
        markup_client.add(
            InlineKeyboardButton("💵 Наличные", callback_data=f"payment_cash_full_{client_chat_id}"),
            InlineKeyboardButton("💳 Карта", callback_data=f"payment_card_full_{client_chat_id}")
        )
        if current_bonus >= rub:
            markup_client.add(InlineKeyboardButton("🎁 Оплатить баллами", callback_data=f"paying_bonus_full_{client_chat_id}"))

        safe_send(client_chat_id, text_client, reply_markup=markup_client)
    except Exception:
        logger.exception("Ошибка в handle_full_tank_litres_input")
        safe_send(operator_chat_id, "❌ Внутренняя ошибка. Администратор уведомлен.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("paying_bonus_full_"))
def handle_pay_bonus_full(call):
    try:
        bot.answer_callback_query(call.id)
        client_chat_id = int(call.data.split("_")[-1])

        try:
            safe_edit_reply_markup(call.message.chat.id, call.message.message_id)
        except Exception:
            pass

        with sessions_lock:
            litres = float(price_change_sessions.get(client_chat_id, {}).get('litres', 0.0))
            price_change_sessions[client_chat_id]['payment_method'] = "bonus"

        session = user_sessions.get(client_chat_id, {}) or {}
        fuel = session.get('fuel')

        price = get_price_per_litre_safe(fuel)
        if price == 0:
            safe_send(client_chat_id, "❌ Не удалось получить цену топлива. Обратитесь в поддержку.")
            notify_admin(f"[ERROR] price==0 in paying_bonus_full for client {client_chat_id}")
            return

        rub = round(litres * price, 2)

        try:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute("SELECT bonus FROM users WHERE telegram_id = ?", (client_chat_id,))
                row = cur.fetchone()
                current_bonus = int(row[0]) if row and row[0] else 0

                if current_bonus >= int(rub):
                    new_bonus = current_bonus - int(rub)
                    cur.execute("UPDATE users SET bonus = ? WHERE telegram_id = ?", (new_bonus, client_chat_id))
                    conn.commit()

                    safe_send(client_chat_id, f"✅ Оплата бонусами прошла успешно!\n💰 Остаток: {new_bonus} баллов.")
                    # запись в историю и уведомление оператору
                    cur.execute('''INSERT INTO history ("Адрес", "Топливо", "Рубли", "Литры", "Оплата", "Telegram_ID")
                                   VALUES (?, ?, ?, ?, ?, ?)''', (
                        STATION_NAMES.get(session.get('station'), 'Неизвестно'),
                        ('Бензин' if fuel == 'benzin' else 'Газ'),
                        rub,
                        litres,
                        "🎁 Баллами",
                        client_chat_id
                    ))
                    conn.commit()

                    station_code = session.get('station')
                    station_address = STATION_CODES_TO_ADDRESSES.get(station_code)
                    operator_id = STATION_OPERATORS.get(station_address)
                    if operator_id:
                        text_operator = (
                            f"✅ Клиент оплатил бонусами.\n"
                            f"Станция: {STATION_NAMES.get(session.get('station'), 'Неизвестно')}\n"
                            f"Колонка: {session.get('column')}\n"
                            f"Топливо: {('Бензин' if fuel == 'benzin' else 'Газ')}\n"
                            f"Литры: {litres:.2f}\n"
                            f"Сумма (в баллах): {rub}"
                        )
                        safe_send(operator_id, text_operator, reply_markup=InlineKeyboardMarkup().add(
                            InlineKeyboardButton("✅ Заправил", callback_data=f"full_tank_accepted_{client_chat_id}")
                        ))
                    else:
                        logger.warning("paying_bonus_full: operator_id is None for station %s", station_code)
                else:
                    safe_send(client_chat_id, "❌ Недостаточно баллов для оплаты.")
        except Exception:
            logger.exception("Ошибка в paying_bonus_full DB flow")
            safe_send(client_chat_id, "❌ Произошла ошибка при оплате баллами. Администратор уведомлен.")
    except Exception:
        logger.exception("Ошибка в handle_pay_bonus_full")
        try:
            safe_send(call.from_user.id, "❌ Внутренняя ошибка. Администратор уведомлен.")
        except Exception:
            pass
# --- Обработка выбора оплаты ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("payment_"))
def handle_payment_choice(call):
    try:
        method = call.data.split("_")[1]  # cash или card
        client_chat_id = int(call.data.split("_")[-1])
        print(client_chat_id, method)
        try:
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None
            )
        except Exception as e:
            print(f"[UI ERROR] Не удалось убрать кнопку: {e}")
        session = user_sessions.get(client_chat_id, {})
        fuel = session.get('fuel')
        litres = price_change_sessions[client_chat_id].get('litres')

        price = 0
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                # Берём первую попавшуюся цену для выбранного топлива
                cur.execute("SELECT price_per_litre FROM fuel WHERE fuel_type = ? AND payment_method = ? LIMIT 1", (fuel, method))
                row = cur.fetchone()
                if row:
                    price = row[0]
        except Exception as e:
            print(f"[fuel price] Ошибка: {e}")
            price = 0


        fuel_name = 'Бензин' if fuel == 'benzin' else 'Газ'
        rub = round(litres * price, 2)

        price_change_sessions[client_chat_id]['payment_method'] = method

        payment_info = "💵 Наличные" if method == "cash" else "💳 Карта"

        station_code = session.get('station')
        station_address = STATION_CODES_TO_ADDRESSES.get(station_code)
        operator_chat_id = STATION_OPERATORS.get(station_address)

        text_operator = (
            f"✅ Клиент выбрал способ оплаты:\n"
            f"Станция: {STATION_NAMES.get(station_code, 'Неизвестно')}\n"
            f"Колонка: {session.get('column')}\n"
            f"Топливо: {fuel_name}\n"
            f"Литры: {litres:.2f}\n"
            f"Сумма: {rub:.2f} ₽\n"
            f"Способ оплаты: {payment_info}"
        )
        markup_operator = InlineKeyboardMarkup()
        markup_operator.add(InlineKeyboardButton("✅ Принял", callback_data=f"full_tank_accepted_{client_chat_id}"))

        if operator_chat_id is None:
            print(f"Не найден оператор для станции {station_code}, сообщение не отправлено.")
        else:
            try:
                bot.send_message(operator_chat_id, text_operator, reply_markup=markup_operator)
            except telebot.apihelper.ApiTelegramException as e:
                print(f"Ошибка отправки сообщения оператору {operator_chat_id}: {e}")

        bot.answer_callback_query(call.id, f"Вы выбрали {payment_info}. Ожидайте заправку.")

    except Exception as e:
        print(f"Ошибка 3015: {e}")

# --- Обработка нажатия "✅ Принял" ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("full_tank_accepted_"))
def handle_full_tank_accepted(call):
    try:
        bot.answer_callback_query(call.id)

        # Убираем кнопку у сообщения оператора
        try:
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None
            )
        except Exception as e:
            print(f"[UI ERROR] Не удалось убрать кнопку: {e}")
        client_chat_id = int(call.data.split("_")[-1])
        session = user_sessions.get(client_chat_id, {}) or {}
        litres = price_change_sessions.get(client_chat_id, {}).get('litres', 0)

        try:
            litres = float(litres)
        except Exception:
            litres = 0.0

        fuel = session.get('fuel')
        price = 0
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                # Берём первую попавшуюся цену для выбранного топлива
                cur.execute("SELECT price_per_litre FROM fuel WHERE fuel_type = ? LIMIT 1", (fuel,))
                row = cur.fetchone()
                if row:
                    price = row[0]
        except Exception as e:
            print(f"[fuel price] Ошибка: {e}")
            price = 0
        rub = round(litres * price, 2)
        fuel_name = 'Бензин' if fuel == 'benzin' else 'Газ'

        payment_method = price_change_sessions.get(client_chat_id, {}).get('payment_method')
        if payment_method == "cash":
            payment_info = "💵 Наличные"
        elif payment_method == "card":
            payment_info = "💳 Карта"
        else:
            payment_info = "🎁 Баллы"

        earned, total = add_bonus(client_chat_id, litres, fuel, payment_method)
        if earned > 0:
            bot.send_message(client_chat_id,
                             f"✅ Операция прошла успешно!\n🎁 Вам начислено {earned} баллов.\n💰 Всего: {total} баллов.")
        else:
            bot.send_message(client_chat_id, f"✅ Операция прошла успешно!\nℹ️ Баллы не начислены (литры: {litres}).")
        station_code = session.get('station')
        station_address = STATION_CODES_TO_ADDRESSES.get(station_code)
        operator_chat_id = STATION_OPERATORS.get(station_address)
        bot.send_message(operator_chat_id, "✅ Отлично, заправка прошла успешно!")
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()

                # 1. Находим телефон клиента по telegram_id
                cur.execute("SELECT phone FROM users WHERE telegram_id = ?", (client_chat_id,))
                user_data = cur.fetchone()
                client_phone = user_data["phone"] if user_data else None
                print(session.get('station'))
                # Вставляем в историю
                if payment_info != "🎁 Баллы":
                    cur.execute('''
                        INSERT INTO history ("Дата", "Адрес", "Топливо", "Рубли", "Литры", "Оплата", "Telegram_ID")
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        datetime.now().strftime("%Y-%m-%d %H:%M"),  # Дата
                        STATION_NAMES.get(session.get('station'), 'Неизвестно'),  # Здесь лучше хранить station_code, а не адрес
                        fuel_name,
                        rub,
                        litres,
                        payment_info,
                        client_chat_id
                    ))

                station_code = session.get('station')  # 'station_1', 'station_2', ...
                if station_code:
                    # 2. Получаем активную смену по station_code
                    cur.execute("""
                            SELECT operator_id 
                            FROM shifts 
                            WHERE station = ? AND active = 1
                        """, (station_code,))
                    shift_data = cur.fetchone()
                    print(shift_data)
                    if shift_data:
                        operator_id = shift_data["operator_id"]

                        print(operator_id)
                        # 3. Получаем телефон и имя оператора
                        cur.execute("SELECT name, phone FROM operators WHERE id = ?", (operator_id,))
                        operator_info = cur.fetchone()

                        if operator_info:
                            operator_name = operator_info["name"]
                            operator_phone = operator_info["phone"]

                            # Функция для нормализации номера
                            def normalize_phone(phone):
                                if not phone:
                                    return None
                                phone = str(phone).strip()
                                # Убираем все символы кроме цифр и плюса
                                phone = ''.join(ch for ch in phone if ch.isdigit() or ch == '+')
                                # Приводим к формату +7
                                if phone.startswith('+7'):
                                    return phone
                                elif phone.startswith('8'):
                                    return '+7' + phone[1:]
                                elif phone.startswith('7'):
                                    return '+7' + phone[1:]
                                elif phone.startswith('9') and len(phone) == 10:
                                    # если номер без кода страны, добавляем +7
                                    return '+7' + phone
                                else:
                                    return phone  # если формат неизвестен, возвращаем как есть

                            operator_phone = normalize_phone(operator_phone)
                            client_phone = normalize_phone(client_phone)

                            print(operator_phone, client_phone)

                            # 4. Сравниваем телефоны
                            if client_phone and operator_phone and client_phone == operator_phone:
                                bot.send_message(
                                    ADMIN_ID2,  # сюда ID админа
                                    f"⚠️ Внимание!\nОператор {operator_name} ({operator_phone}) "
                                    f"заправляется во время своей смены на станции {STATION_CODES_TO_ADDRESSES.get(station_code, station_code)}."
                                )

                # Обновление данных в shifts
                if station_code:
                    if fuel == 'benzin':
                        if payment_info == "🎁 Баллы":
                            cur.execute("""
                                    UPDATE shifts
                                    SET gasoline_liters = COALESCE(gasoline_liters, 0) + ?,
                                        bonus_sum = COALESCE(bonus_sum, 0) + ?
                                    WHERE station = ? AND active = 1
                                """, (litres, rub, station_code))
                        else:
                            cur.execute("""
                                    UPDATE shifts
                                    SET gasoline_liters = COALESCE(gasoline_liters, 0) + ?,
                                        sales_sum = COALESCE(sales_sum, 0) + ?
                                    WHERE station = ? AND active = 1
                                """, (litres, rub, station_code))
                    else:
                        if payment_info == "🎁 Баллы":
                            cur.execute("""
                                    UPDATE shifts
                                    SET gas_liters = COALESCE(gas_liters, 0) + ?,
                                        bonus_sum = COALESCE(bonus_sum, 0) + ?
                                    WHERE station = ? AND active = 1
                                """, (litres, rub, station_code))
                        else:
                            cur.execute("""
                                    UPDATE shifts
                                    SET gas_liters = COALESCE(gas_liters, 0) + ?,
                                        sales_sum = COALESCE(sales_sum, 0) + ?
                                    WHERE station = ? AND active = 1
                                """, (litres, rub, station_code))

                conn.commit()
        except Exception as e:
            print(f"[DB ERROR] {e}")

        user_sessions.pop(client_chat_id, None)
        price_change_sessions.pop(client_chat_id, None)
    except Exception as e:
        print(f"Ошибка 3157: {e}")
@bot.message_handler(commands=['set_bonus'])
def set_bonus_command(message):
    try:
        if message.chat.id != DIRECTOR_ID:
            bot.send_message(message.chat.id, "❌ У вас нет прав для этой команды.")
            return

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("⛽ Бензин", callback_data="bonus_fuel_benzin"),
            InlineKeyboardButton("🔥 Газ", callback_data="bonus_fuel_gaz")
        )
        bot.send_message(DIRECTOR_ID, "Выберите топливо для изменения бонусов:", reply_markup=markup)
    except Exception as e:
        print(f"[ERROR] Ошибка 3871: {e}")


# 2. Выбор топлива
@bot.callback_query_handler(func=lambda call: call.data.startswith("bonus_fuel_"))
def choose_payment_method(call):
    try:
        if call.message.chat.id != DIRECTOR_ID:
            return

        fuel = call.data.replace("bonus_fuel_", "")
        user_sessions[DIRECTOR_ID] = {"fuel": fuel}  # временно сохраняем выбор

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("💵 Наличные", callback_data="bonus_method_cash"),
            InlineKeyboardButton("💳 Карта", callback_data="bonus_method_card")
        )
        bot.edit_message_text(
            f"Топливо: {fuel}\nВыберите способ оплаты:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )
    except Exception as e:
        print(f"[ERROR] Ошибка 3896: {e}")


# 3. Выбор способа оплаты
@bot.callback_query_handler(func=lambda call: call.data.startswith("bonus_method_"))
def ask_new_bonus(call):
    try:
        if call.message.chat.id != DIRECTOR_ID:
            return

        payment_method = call.data.replace("bonus_method_", "")
        user_sessions[DIRECTOR_ID]["payment_method"] = payment_method

        bot.send_message(DIRECTOR_ID, f"Введите новое количество бонусов за 1 литр ({user_sessions[DIRECTOR_ID]['fuel']}, {payment_method}):")
    except Exception as e:
        print(f"[ERROR] Ошибка 3911: {e}")


# 4. Ввод нового бонуса
@bot.message_handler(func=lambda m: m.chat.id == DIRECTOR_ID and "fuel" in user_sessions.get(DIRECTOR_ID, {}))
def update_bonus(message):
    try:
        new_bonus = float(message.text.replace(",", "."))
        session = user_sessions[DIRECTOR_ID]
        fuel = session["fuel"]
        payment_method = session["payment_method"]

        ensure_fuel_rows()  # проверяем и создаём все комбинации

        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            # обновляем бонус только для выбранной комбинации
            cur.execute(
                "UPDATE fuel SET bonuses = ? WHERE fuel_type = ? AND payment_method = ?",
                (new_bonus, fuel, payment_method)
            )
            conn.commit()

        bot.send_message(DIRECTOR_ID, f"✅ Бонусы для {fuel} ({payment_method}) обновлены: {new_bonus} баллов/л")
        user_sessions.pop(DIRECTOR_ID, None)

    except Exception as e:
        bot.send_message(DIRECTOR_ID, f"❌ Ошибка при обновлении бонусов: {e}")
@bot.callback_query_handler(func=lambda call: call.data in ["admin_set_price", "admin_set_bonus", "admin_set_operator"])
def handle_admin_buttons(call):
    try:
        if call.message.chat.id != DIRECTOR_ID:
            return bot.reply_to(call.message, "Нет доступа.")

        if call.data == "admin_set_price":
            # Запускаем ту же функцию, что и /set_price
            set_price_command(call.message)

        elif call.data == "admin_set_bonus":

            # Запускаем ту же функцию, что и /set_bonus
            set_bonus_command(call.message)
        elif call.data == "admin_set_operator":
            try:
                if call.message.chat.id != DIRECTOR_ID:
                    return bot.reply_to(call.message, "Нет доступа.")
                bot.send_message(call.message.chat.id, "Введите имя оператора:")
                bot.register_next_step_handler(call.message, add_operator_step2)
            except Exception as e:
                print(f"Ошибка 3956: {e}")
    except Exception as e:
        print(f"[ERROR] Ошибка 3950: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "admin_set_broadcast")
def start_broadcast(call):
    try:
        if call.message.chat.id != DIRECTOR_ID:
            bot.send_message(call.message.chat.id, "❌ У вас нет прав для этой команды.")
            return

        bot.send_message(DIRECTOR_ID, "Введите текст рассылки:")
        bot.register_next_step_handler(call.message, process_broadcast)

    except Exception as e:
        print(f"[ERROR] Ошибка 3864: {e}")


# 📢 Рассылка
def process_broadcast(message):
    try:
        if message.chat.id != DIRECTOR_ID:   # ✅ тут должен быть message, а не call
            return

        text = message.text
        sent_count, fail_count = 0, 0

        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT telegram_id FROM users WHERE telegram_id IS NOT NULL")
            rows = cur.fetchall()

        for row in rows:
            user_id = row[0]
            try:
                bot.send_message(user_id, text)
                sent_count += 1
            except Exception as e:
                print(f"[BROADCAST ERROR] Не удалось отправить {user_id}: {e}")
                fail_count += 1

        bot.send_message(
            DIRECTOR_ID,
            f"✅ Рассылка завершена!\nОтправлено: {sent_count}\nОшибок: {fail_count}"
        )

    except Exception as e:
        print(f"[ERROR] Ошибка 3892: {e}")

@bot.callback_query_handler(func=lambda call: call.data in ["admin_set_job"])
def admin_manage_jobs(call):
    try:
        if call.message.chat.id != DIRECTOR_ID:
            bot.answer_callback_query(call.id, "❌ Нет доступа")
            return

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs")
        jobs = cursor.fetchall()
        conn.close()

        if not jobs:
            text = "📂 Вакансий пока нет."
        else:
            text = "📂 Список вакансий:\n\n"

        inline_kb = types.InlineKeyboardMarkup()

        for job in jobs:
            text += f"▫️ {job['title']} ({job['profession']})\n"
            inline_kb.add(
                types.InlineKeyboardButton(f"❌ Удалить {job['title']}", callback_data=f"deleting_job_{job['id']}"))

        inline_kb.add(types.InlineKeyboardButton("➕ Добавить вакансию", callback_data="add_job"))

        bot.send_message(call.message.chat.id, text, reply_markup=inline_kb)
    except Exception as e:
        print(f"[ERROR] Ошибка 3981: {e}")


@bot.message_handler(commands=['set_price'])
def set_price_command(message):
    try:
        if message.chat.id != DIRECTOR_ID:
            bot.send_message(message.chat.id, "❌ У вас нет прав для этой команды.")
            return

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("⛽ Бензин", callback_data="price_fuel_benzin"),
            InlineKeyboardButton("🔥 Газ", callback_data="price_fuel_gaz")
        )
        bot.send_message(DIRECTOR_ID, "Выберите топливо для изменения цены:", reply_markup=markup)
    except Exception as e:
        print(f"[ERROR] Ошибка 3998: {e}")


# 2. Выбор топлива
@bot.callback_query_handler(func=lambda call: call.data.startswith("price_fuel_"))
def ask_new_price(call):
    try:
        if call.message.chat.id != DIRECTOR_ID:
            return

        fuel = call.data.replace("price_fuel_", "")
        user_sessions[DIRECTOR_ID] = {"fuel_price": fuel}

        bot.send_message(DIRECTOR_ID, f"Введите новую цену за литр ({fuel}):")

    except Exception as e:
        print(f"[ERROR] Ошибка 4014: {e}")

# 3. Ввод новой цены
def ensure_fuel_rows():
    """Создаёт все комбинации топлива и способа оплаты, если их нет."""
    fuels = ['benzin', 'gaz']
    payments = ['cash', 'card']
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            for fuel in fuels:
                for pay in payments:
                    cur.execute(
                        "SELECT 1 FROM fuel WHERE fuel_type = ? AND payment_method = ?",
                        (fuel, pay)
                    )
                    if cur.fetchone() is None:
                        # вставляем строку с ценой 0 и бонусами 0 по умолчанию
                        cur.execute(
                            "INSERT INTO fuel (fuel_type, payment_method, price_per_litre, bonuses) VALUES (?, ?, ?, ?)",
                            (fuel, pay, 0.0, 0)
                        )
            conn.commit()
    except Exception as e:
        print(f"[DB ERROR] ensure_fuel_rows: {e}")


# ====== Обновление цены ======
@bot.message_handler(func=lambda m: m.chat.id == DIRECTOR_ID and "fuel_price" in user_sessions.get(DIRECTOR_ID, {}))
def update_price(message):
    try:
        new_price = float(message.text.replace(",", "."))
        session = user_sessions[DIRECTOR_ID]
        fuel = session["fuel_price"]

        ensure_fuel_rows()  # проверяем и создаём все комбинации

        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            # обновляем цену для всех способов оплаты этого топлива
            cur.execute("UPDATE fuel SET price_per_litre = ? WHERE fuel_type = ?", (new_price, fuel))
            conn.commit()

            # лог таблицы
            cur.execute("SELECT fuel_type, payment_method, price_per_litre, bonuses FROM fuel")
            print("[FUEL TABLE]")
            for r in cur.fetchall():
                print(r)

        bot.send_message(DIRECTOR_ID, f"✅ Цена для {fuel} обновлена: {new_price:.2f} ₽/л (для всех способов оплаты)")
        user_sessions.pop(DIRECTOR_ID, None)

    except Exception as e:
        bot.send_message(DIRECTOR_ID, f"❌ Ошибка при обновлении цены: {e}")



@bot.message_handler(commands=['history'])
def show_history(msg):
    try:
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
    except Exception as e:
        print(f"Ошибка 3242: {e}")


def save_to_db(chat_id):
    try:
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
    except Exception as e:
        print(f"Ошибка 3268: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "rext")
def show_repair_info(call):
    try:
        text = (
            "🚗 <b>Элит Рихтовка — Тольятти</b>\n"
            "💡 Чтобы рассчитать стоимость ремонта — "
            "опишите проблему и прикрепите фото повреждения 👇"
        )

        bot.send_message(call.from_user.id, text, parse_mode="HTML")

        # Запоминаем, что ждём текст от клиента
        session[call.from_user.id] = {"stage": "waiting_for_repair_text"}
    except Exception as e:
        print(f"Ошибка 3285: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "taxi")
def handle_taxi(call):
    try:
        bot.answer_callback_query(call.id)

        app_link = "https://play.google.com/store/apps/details?id=com.taxsee.taxsee&pcampaignid=web_share"  # вставь свою ссылку
        app_link = "https://play.google.com/store/apps/details?id=com.taxsee.elite&pcampaignid=web_share"
        markup = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton("Скачать приложение", url=app_link)
        markup.add(button)

        bot.send_message(
            call.message.chat.id,
            "🚕 Чтобы заказать такси, позвоните по номеру: +78482999999\n"
            "Или скачайте наше приложение для быстрого заказа:",
            reply_markup=markup
        )
    except Exception as e:
        print(f"Ошибка 3306: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "about")
def handle_about(call):
    try:
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
    except Exception as e:
        print(f"Ошибка 3338: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "jobs")
def handle_jobs(call):
    try:
        bot.answer_callback_query(call.id)

        kb = types.InlineKeyboardMarkup()

        # # фиксированные кнопки
        # kb.add(
        #     types.InlineKeyboardButton("🚕 Водитель такси", callback_data="job_taxi")
        # )
        # kb.add(
        #     types.InlineKeyboardButton("🚚 Водитель Газели", callback_data="job_gazel")
        # )

        # динамические вакансии из БД
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, profession, title FROM jobs")
        jobs = cursor.fetchall()
        conn.close()

        for job in jobs:
            # profession – английское название (для callback_data),
            # title – человеко-понятное название (для текста кнопки)
            kb.add(
                types.InlineKeyboardButton(f"💼 {job['title']}", callback_data=f"job_{job['profession']}")
            )

        bot.send_message(call.message.chat.id, "💼 Выберите вакансию:", reply_markup=kb)

    except Exception as e:
        print(f"Ошибка 3356: {e}")


from telebot import TeleBot, types
from telebot.handler_backends import State, StatesGroup
import pytesseract


@bot.callback_query_handler(func=lambda call: call.data == "jobs_taxi")
def handle_jobs(call):
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      reply_markup=None)
        description = (
            "🚖 <b>Вакансия: Водитель такси</b>\n\n"
            "✅ <i>Преимущества:</i>\n"
            "• Без диспетчерских комиссий\n"
            "• Свободный график — работаешь когда хочешь\n"
            "• Свой автопарк и мастерская: чинись и мойся бесплатно в любое время\n"
            "• Сломалась машина? — Сразу выдадим другую\n"
            "• Бесплатно 20 литров газа каждый день\n"
            "• Соцпакет для водителей\n"
            "• Деньги получаешь прямо от клиентов — без бухгалтерии\n"
            "• <b>Нужен ИП</b>\n"
            "• 💰 Заработок зависит только от тебя\n"
        )

        # Отправляем описание вакансии
        bot.send_message(call.message.chat.id, description, parse_mode="HTML")

        # Отдельным сообщением — кнопку отклика
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✅ Продолжить", callback_data="target_taxi"))

        bot.send_message(call.message.chat.id, "Если вас заинтересовало предложение:", reply_markup=kb)

    except Exception as e:
        print(f"Ошибка 3395: {e}")


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


# class JobStates(StatesGroup):
#   waiting_for_license = State()

@bot.callback_query_handler(func=lambda call: call.data.startswith("job_"))
def handle_job_description(call):
    try:
        user_id = call.from_user.id
        bot.answer_callback_query(call.id)
        profession_key = call.data[4:]  # убираем "job_"

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT title, description FROM jobs WHERE profession = ?", (profession_key,))
        job = cursor.fetchone()
        conn.close()

        if job:
            text = f"💼 {job['title']}\n\n{job['description']}"
            bot.send_message(call.message.chat.id, text)
        else:
            bot.send_message(call.message.chat.id, "❌ Описание вакансии не найдено.")
        user_data[user_id] = {"selected_job": profession_key}



        # Вызов календаря без car_id
        show_user_calendar(call.message, None, user_id)
    except Exception as e:
        print(f"Ошибка 3748: {e}")


class JobStates(StatesGroup):
    waiting_for_license = State()


@bot.callback_query_handler(func=lambda call: call.data.startswith("meeting_next_") or call.data == "return_location")
def yes_or_no(call):
    try:
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

            with sqlite3.connect(DB_PATH) as conn:
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
    except Exception as e:
        print(f"Ошибка 3864: {e}")


def show_user_rental_calendar(message, car_id):
    try:
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
    except Exception as e:
        print(f"Ошибка 3891: {e}")


@bot.message_handler(
    func=lambda message: (get_state(message.from_user.id) or '').startswith('waiting_for_rental_time_'))
def process_rental_time(message):
    try:
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

    except Exception as e:
        print(f"Ошибка 3914: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "jobs_gazel")
def handle_job_selection(call):
    try:
        user_id = call.from_user.id
        car_id = "gazel_001"
        bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      reply_markup=None)
        user_data[user_id] = {
            "selected_job": "газель",
            "car_id": car_id
        }

        description = (
            "🚚 *Вакансия: Водитель Газели*\n\n"
            "✅ _Преимущества:_\n"
            "• График работы обсуждается индивидуально\n"
            "• Постоянные маршруты / стабильная загрузка\n"
            "• Работа по городу и области\n"
            "• ЗП от 80 000 ₽\n"
            "• Оформление по ИП или самозанятый\n"
        )

        bot.send_message(call.message.chat.id, description, parse_mode="Markdown")

        session = get_session(user_id)
        session["state"] = "waiting_for_photo"
        session["car_id"] = car_id
        session["selected_service"] = "gazel"

        bot.send_message(user_id, "📸 Пожалуйста, отправьте фотографию водительского удостоверения.")
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Ошибка 3949: {e}")


def send_date_buttons(chat_id):
    try:
        from datetime import datetime, timedelta
        from telebot import types

        today = datetime.today()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for i in range(7):
            day = today + timedelta(days=i)
            day_num = day.day
            month_name = MONTH_NAMES_RU_GEN[day.month - 1]
            date_str = f"{day_num} {month_name}"  # Например: "25 июля"
            markup.add(types.KeyboardButton(date_str))
        bot.send_message(chat_id, "📅 Выберите дату встречи:", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка 3967: {e}")


def check_photo_in_db(user_id, photo_column):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT {photo_column} FROM users WHERE telegram_id = ?", (user_id,))
            row = cursor.fetchone()
            return bool(row and row[0])
    except Exception as e:
        print(f"Ошибка 3978: {e}")


orders = {}
pending_photo_reply = {}  # {master_message_id: client_user_id}


# {master_photo_msg_id: {"client_id": int, "photo": file_id}}

@bot.message_handler(func=lambda m: session.get(m.from_user.id, {}).get("stage") == "waiting_for_repair_text",
                     content_types=["text"])
def handle_repair_description(message):
    try:
        session[message.from_user.id]["description"] = message.text
        session[message.from_user.id]["stage"] = "waiting_for_repair_photo"

        bot.send_message(message.chat.id, "Спасибо! Теперь пришлите фото повреждения 📷")
    except Exception as e:
        print(f"Ошибка 3996: {e}")


@bot.message_handler(func=lambda m: session.get(m.from_user.id, {}).get("stage") == "waiting_for_repair_photo",
                     content_types=["photo"])
def handle_repair_photo(message):
    try:
        user_id = message.from_user.id
        file_id = message.photo[-1].file_id
        desc = session[user_id].get("description", "Без описания")

        # Достаем из базы имя и телефон
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT name, phone FROM users WHERE telegram_id = ?", (user_id,))
            user_info = cur.fetchone()
            if user_info:
                name = user_info["name"]
                phone = user_info["phone"]
            else:
                name = "Неизвестно"
                phone = "Неизвестно"
        finally:
            conn.close()

        # Сообщаем клиенту
        bot.send_message(user_id, "Отлично 👍 Ваши данные отправлены мастеру, скоро свяжемся!")

        # Отправляем мастеру с подсказкой и данными клиента
        sent_msg = bot.send_photo(
            MASTER_CHAT_ID,
            file_id,
            caption=(
                f"🆕 Заявка от клиента {user_id}:\n"
                f"Имя: {name}\n"
                f"Телефон: {phone}\n"
                f"Описание: {desc}\n\n"
                "💡 Чтобы ответить клиенту — нажмите «Ответить» на это сообщение."
            )
        )

        # Запоминаем заказ
        orders[sent_msg.message_id] = {"client_id": user_id, "photo": file_id}

        # Очищаем сессию клиента
        session.pop(user_id, None)
    except Exception as e:
        print(f"Ошибка 4045: {e}")


@bot.message_handler(func=lambda m: m.reply_to_message and m.reply_to_message.message_id in orders,
                     content_types=["text"])
def handle_master_reply(message):
    try:
        order_info = orders[message.reply_to_message.message_id]
        client_id = order_info["client_id"]
        client_photo = order_info["photo"]

        # Отправляем клиенту фото с ответом мастера
        bot.send_photo(client_id, client_photo, caption=f"💬 Ответ мастера:\n{message.text}")

        # Сообщаем мастеру, что отправлено
        bot.send_message(message.chat.id, "✅ Ответ отправлен клиенту.")
    except Exception as e:
        print(f"Ошибка 4062: {e}")


@bot.message_handler(
    func=lambda m: get_session(m.from_user.id).get("state") in [
        "waiting_for_photo",
        "waiting_for_passport_front",
        "waiting_for_passport_back",
        "admin_add_car_photo",
        "waiting_for_contract_photo",
        "waiting_for_issue_photo",
    ],
    content_types=['photo']
)
def handle_photo_upload(message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        photo_id = message.photo[-1].file_id
        session = get_session(user_id)
        state = session.get("state")

        # ---------- функция пропуска шага ----------
        def skip_step(photo_field, next_state, prompt_text):
            if check_photo_in_db(user_id, photo_field):
                set_state(user_id, next_state)
                bot.send_message(chat_id, prompt_text)
                return True
            return False

        # ---------- логика состояний ----------
        if state == "waiting_for_photo":
            if not skip_step("driver_license_photo", "waiting_for_passport_front",
                             "📄 Теперь пришлите лицевую сторону паспорта."):
                session["driver_license_photo"] = photo_id
                set_state(user_id, "waiting_for_passport_front")
                bot.send_message(chat_id, "📄 Теперь пришлите лицевую сторону паспорта.")

        elif state == "waiting_for_passport_front":
            if not skip_step("passport_front_photo", "waiting_for_passport_back",
                             "📄 И теперь — обратную сторону паспорта."):
                session["passport_front_photo"] = photo_id
                set_state(user_id, "waiting_for_passport_back")
                bot.send_message(chat_id, "📄 И теперь — обратную сторону паспорта.")

        elif state == "waiting_for_passport_back":
            if not check_photo_in_db(user_id, "passport_back_photo"):
                session["passport_back_photo"] = photo_id

            set_state(user_id, None)
            bot.send_message(chat_id, "✅ Все документы получены.")

            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET
                        driver_license_photo = COALESCE(?, driver_license_photo),
                        passport_front_photo = COALESCE(?, passport_front_photo),
                        passport_back_photo = COALESCE(?, passport_back_photo)
                    WHERE telegram_id = ?
                ''', (
                    session.get("driver_license_photo"),
                    session.get("passport_front_photo"),
                    session.get("passport_back_photo"),
                    user_id
                ))
                conn.commit()

            post_photo_processing(user_id, chat_id, session)

        elif state == "admin_add_car_photo":
            session["photo"] = photo_id
            with db_lock, sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO cars (number, brand_model, year, transmission, photo_url, service, station)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session.get("number"),
                    session.get("model"),
                    session.get("year"),
                    session.get("transmission"),
                    photo_id,
                    session.get("service"),
                    session.get("station")
                ))
                conn.commit()

            bot.send_message(user_id, f"✅ Машина добавлена:\n\n"
                                      f"<b>Номер:</b> {session.get('number')}\n"
                                      f"<b>Модель:</b> {session.get('model')}\n"
                                      f"<b>Год:</b> {session.get('year')}\n"
                                      f"<b>Коробка:</b> {session.get('transmission')}\n"
                                      f"<b>Тип услуги:</b> {session.get('service')}\n"
                                      f"<b>Станция:</b> {session.get('station')}",
                             parse_mode="HTML")
            bot.send_photo(user_id, photo_id)
            user_sessions.pop(user_id, None)
            clear_state(user_id)

        elif state == "waiting_for_contract_photo":
            file_id = photo_id
            booking_id = inspection_states.get(user_id, {}).get("booking_id", "❓")

            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute("SELECT name, phone, passport_front_photo FROM users WHERE telegram_id = ?", (user_id,))
                row = cur.fetchone()

            name, phone, passport_photo_id = row if row else ("❓", "❓", None)

            caption = (
                f"📅 <b>Подписанный договор</b> от <b>{name}</b> (📞 {phone})\n"
                f"Заявка: #{booking_id}\n\n"
                f"Проверьте документы:"
            )

            bot.send_photo(ADMIN_ID2, file_id, caption=caption, parse_mode="HTML")

            if passport_photo_id:
                bot.send_photo(ADMIN_ID2, passport_photo_id, caption="🆔 Паспорт (лицевая сторона)")

            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("✅ Всё правильно", callback_data=f"vverify_docs_ok_{user_id}"),
                InlineKeyboardButton("❌ Неверно", callback_data=f"vverify_docs_wrong_{user_id}")
            )

            bot.send_message(ADMIN_ID2, "Проверьте документы и подтвердите:", reply_markup=markup)

            session["state"] = None
            user_contract_data[user_id]["awaiting_document"] = False

        elif state == "waiting_for_issue_photo":
            session["inspection_issue_photo"] = photo_id
            session["state"] = None
            issue_text = session.get("inspection_issue_text", "— описание отсутствует —")

            with db_lock, sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT bookings.car_id, cars.brand_model, cars.number,
                           users.name, users.phone
                    FROM bookings
                    JOIN cars ON bookings.car_id = cars.car_id
                    JOIN users ON bookings.user_id = users.telegram_id
                    WHERE bookings.user_id = ? AND bookings.status = 'confirmed'
                    ORDER BY bookings.id DESC LIMIT 1
                """, (user_id,))
                row = cursor.fetchone()

            if row:
                car_id, brand_model, number, user_name, user_phone = row
                car_info = f"🚗 Машина: {brand_model} ({number})"
                user_info = f"👤 Пользователь: {user_name or '—'}\n📞 Телефон: {user_phone or '—'}"
            else:
                car_info = "🚗 Машина: Неизвестная"
                user_info = "👤 Пользователь: Неизвестен"

            bot.send_message(ADMIN_ID2,
                             f"🚨 Проблема при осмотре от пользователя {user_id}:\n\n"
                             f"{user_info}\n"
                             f"{car_info}\n\n"
                             f"📝 Описание проблемы:\n{issue_text}")
            bot.send_photo(ADMIN_ID2, photo_id)
            bot.send_message(user_id, "✅ Спасибо! Проблема зафиксирована и передана администрации.")

        else:
            # fallback если state неизвестен
            session["state"] = "waiting_for_photo"
            bot.send_message(chat_id, "📸 Пожалуйста, пришлите фото водительского удостоверения.")

    except Exception as e:
        print(f"Ошибка 4257: {e}")
pending_fullnames = {}  # telegram_id: (car_id, service, user_id)



def post_photo_processing(user_id, chat_id, session):
    try:
        service = session.get("selected_service")
        car_id = session.get("car_id")
        print(car_id)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, full_name, phone FROM users WHERE telegram_id = ?", (user_id,))
            user_row = cursor.fetchone()

        if not user_row:
            bot.send_message(chat_id, "❌ Ошибка: пользователь не найден в базе.")
            return

        if service == "gazel":
            set_state(user_id, f"waiting_for_time_selection|gazel|{car_id}")
            send_date_buttons(chat_id)
            return


        elif service in ["rent", "rental"]:

            with sqlite3.connect(DB_PATH) as conn:

                cursor = conn.cursor()

                car = None
                print(car_id)
                if car_id:
                    cursor.execute("SELECT brand_model, year, station, price FROM cars WHERE car_id = ?", (car_id,))

                    car = cursor.fetchone()
                    if service == 'rent':
                        cursor.execute("UPDATE cars SET is_available = 0 WHERE car_id = ?", (car_id,))

                        conn.commit()

                now = datetime.now()

                date_str = now.strftime("%Y-%m-%d")

                time_str = now.strftime("%H:%M")

                rent_start, rent_end = None, None

                if service == "rental":

                    cursor.execute("""

                                SELECT rent_start, rent_end FROM rental_history

                                WHERE user_id = ? AND car_id = ?

                                ORDER BY id DESC LIMIT 1

                            """, (user_id, car_id))

                    rental_row = cursor.fetchone()

                    if rental_row:
                        rent_start, rent_end = rental_row

                        # date_str = rent_start or date_str

                cursor.execute("""

                            INSERT INTO bookings (user_id, car_id, service, status, date, time)

                            VALUES (?, ?, ?, ?, ?, ?)

                        """, (user_id, car_id, service, 'pending', date_str, time_str))
                print(user_id, car_id, service, 'pending', date_str, time_str)
                conn.commit()

            markup = types.InlineKeyboardMarkup()

            markup.add(

                types.InlineKeyboardButton("✅ Принять",
                                           callback_data=f"carapprove_{service}_{car_id or 0}_{user_row[0]}_{user_id}"),

                types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{car_id or 0}_{user_id}")

            )

            markup.add(

                types.InlineKeyboardButton("📄 Показать документы", callback_data=f"show_documents_{user_id}")

            )

            service_display = {

                "rent": "аренда",

                "rental": "прокат"

            }.get(service, service)

            message_text = (

                f"📥 Новая заявка:\n\n"

                f"👤 Имя: {user_row[1] or '—'}\n"

                f"📞 Телефон: {user_row[2] or '—'}\n"

                f"🛠 Услуга: {service_display}"

            )
            if car:

                message_text += f"\n🚗 Машина: {car[0]} ({car[1]})"

                base_price = car[3]

                if rent_start and rent_end and base_price:

                    # Расчёт количества дней

                    days = (datetime.strptime(rent_end, "%Y-%m-%d") - datetime.strptime(rent_start, "%Y-%m-%d")).days + 1
                    days = int(days) - 1
                    total_price = calculate_price(base_price, days)

                    message_text += f"\n💰 Итоговая цена: {total_price} ₽ за {days} дн."

                elif base_price:

                    message_text += f"\n💰 Базовая цена: {base_price} ₽"

                if car[2]:
                    message_text += f"\n📍 Станция: {car[2]}"

            if rent_start and rent_end:
                message_text += f"\n🗓 Срок аренды: с {format_date_russian(rent_start)} до {format_date_russian(rent_end)}"

            bot.send_message(ADMIN_ID2, message_text, reply_markup=markup)

            bot.send_message(user_id, "✅ Отлично! Мы уже отправили заявку админу. Ожидайте подтверждение.")

            user_sessions.pop(user_id, None)


        else:

            show_user_calendar(None, car_id, user_id)

    except Exception as e:
        print(f"Ошибка 4411: {e}")

admin_waiting_for_contract = {}  # {admin_id: {"user_id": ..., "callback_data": ..., "full_name": ...}}


def format_date_russian(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")
    except Exception as e:
        print(f"Ошибка 4420: {e}")

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

# --------------------- 1. ОБРАБОТКА CALLBACK "Одобрить" ---------------------
def get_session(uid: int) -> dict:
    try:
        if uid not in session:
            session[uid] = {}
        return session[uid]
    except Exception as e:
        print(f"Ошибка 4472: {e}")


def set_session(uid: int, **kwargs):
    try:
        session = get_session(uid)
        session.update(kwargs)
        return session
    except Exception as e:
        print(f"Ошибка 4481: {e}")


# ===== Callback обработчик кнопки approve =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("carapprove_"))
def process_carapprove(call):
    try:
        admin_id = call.from_user.id
        parts = call.data[len("carapprove_"):].split("_")
        if len(parts) != 4:
            bot.answer_callback_query(call.id, "❌ Ошибка данных")
            return

        service, car_id_raw, client_telegram_str, client_user_str = parts
        car_id = int(car_id_raw) if car_id_raw != "None" else 0
        client_telegram_id = int(client_telegram_str)
        client_user_id = int(client_user_str)

        # Удаляем кнопки у клиента
        try:
            bot.edit_message_reply_markup(chat_id=client_telegram_id,
                                          message_id=call.message.message_id,
                                          reply_markup=None)
        except Exception as e:
            print(f"⚠️ Ошибка при удалении кнопок у клиента: {e}")

        # Сохраняем сессию по админу
        set_session(admin_id,
                    state="waiting_fullname",
                    client_telegram_id=client_telegram_id,
                    client_user_id=client_user_id,
                    car_id=car_id,
                    service=service)

        # Проверяем, есть ли ФИО в БД
        with db_lock, sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT full_name FROM users WHERE id=?", (client_telegram_id,))
            full_name_row = cur.fetchone()

        if full_name_row and full_name_row[0] and full_name_row[0].strip():
            full_name = full_name_row[0]
            set_session(admin_id, state="waiting_contract", full_name=full_name)
            bot.send_message(admin_id, f"📄 Пришлите файл договора аренды на имя: <b>{full_name}</b>", parse_mode="HTML")
        else:
            bot.send_message(admin_id, "📝 Пожалуйста, введите ФИО клиента:")

    except Exception as e:
        print(f"❌ Ошибка в process_carapprove: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка при обработке заявки")


# ===== Обработка ввода ФИО =====
@bot.message_handler(func=lambda m: get_session(m.from_user.id).get("state") == "waiting_fullname")
def handle_admin_fullname_input(message):
    admin_id = message.from_user.id
    try:
        session = get_session(admin_id)
        client_telegram_id = session.get("client_telegram_id")

        if not client_telegram_id:
            bot.send_message(admin_id, "⚠️ Ошибка: данные клиента не найдены. Начните процесс заново.")
            return

        full_name = message.text.strip()
        if not full_name:
            bot.send_message(admin_id, "⚠️ ФИО не может быть пустым. Попробуйте ещё раз.")
            return

        print(f"🔍 Обновляем ФИО: {full_name} для telegram_id={client_telegram_id!r}")

        with db_lock, sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            # Проверим, есть ли такой пользователь
            cur.execute("SELECT 1 FROM users WHERE id=?", (client_telegram_id,))
            if not cur.fetchone():
                print("ℹ️ Пользователь не найден — создаём новую запись.")
                cur.execute("INSERT INTO users (id, full_name) VALUES (?, ?)", (client_telegram_id, full_name))
            else:
                cur.execute("UPDATE users SET full_name=? WHERE id=?", (full_name, client_telegram_id))
            conn.commit()

        bot.send_message(admin_id, f"✅ ФИО клиента обновлено: {full_name}")
        set_session(admin_id, state="waiting_contract", full_name=full_name)
        bot.send_message(admin_id, f"📄 Пришлите файл договора аренды на имя: <b>{full_name}</b>", parse_mode="HTML")

    except Exception as e:
        print(f"❌ Ошибка в handle_admin_fullname_input: {e}")
        bot.send_message(admin_id, f"❌ Произошла ошибка: {e}")


@bot.message_handler(content_types=['document'])
def handle_contract_file(message):
    try:
        admin_id = message.from_user.id
        session = get_session(admin_id)

        client_user_id = session.get("client_user_id")
        car_id = session.get("car_id")
        service = session.get("service")

        if not client_user_id or not car_id:
            bot.send_message(admin_id, "⚠️ Не найдена информация о пользователе или машине в сессии. Повторите действие.")
            return

        file_id = message.document.file_id

        try:
            with db_lock, sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute("""
                        SELECT id FROM bookings
                        WHERE user_id = ? AND car_id = ?
                        ORDER BY id DESC
                        LIMIT 1
                    """, (client_user_id, car_id))
                row = cur.fetchone()

                if not row:
                    bot.send_message(admin_id, "⚠️ Не найдено брони для этого клиента и машины.")
                    return

                booking_id = row[0]
                cur.execute("UPDATE bookings SET contract_file_id = ? WHERE id = ?", (file_id, booking_id))
                conn.commit()

            bot.send_message(admin_id, f"✅ Договор сохранён в базе bookings.")

            # Продолжаем процесс утверждения
            continue_carapprove_flow(service, car_id, client_user_id, admin_id)

            # Очищаем сессию
            clear_session(admin_id)

        except Exception as e:
            bot.send_message(admin_id, f"❌ Ошибка при сохранении договора: {e}")
    except Exception as e:
        print(f"Ошибка 4618: {e}")


def continue_carapprove_flow(service, car_id, telegram_id, admin_id):
    try:
        print(telegram_id)
        with db_lock, sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("""
                UPDATE rental_history
                SET status = 'confirmed'
                WHERE user_id = ? AND car_id = ?
            """, (telegram_id, car_id))

            cur.execute("UPDATE bookings SET status = 'confirmed' WHERE user_id = ? AND car_id = ? AND service = ?",
                        (telegram_id, car_id, service))
            cur.execute("UPDATE users SET status = 'waiting_car' WHERE telegram_id = ?", (telegram_id,))

            cur.execute("SELECT brand_model, year, station FROM cars WHERE car_id = ?", (car_id,))
            car = cur.fetchone()
            conn.commit()

        service_display = {"rent": "аренду", "rental": "прокат"}.get(service, service)
        if car:
            car_info = f"🚗 Машина: {car['brand_model']} ({car['year']})"
            station_info = f"📍 Станция: {car['station']}" if car['station'] else "📍 Станция: уточняется"
        else:
            car_info = "🚗 Машина: неизвестна"
            station_info = "📍 Станция: неизвестна"

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("/start")  # кнопка, которая отправляет команду /start
        bot.send_message(telegram_id, "Нажмите кнопку, чтобы вернуться в меню:", reply_markup=markup)

        bot.send_message(
            telegram_id,
            f"✅ Ваша заявка на {service_display} одобрена!\n\n"
            f"{car_info}\n"
            f"{station_info}\n\n"
            f"💰 Для закрепления автомобиля необходимо внести залог \n*10 000 ₽*.\n"
            f"⏳ У вас есть *1 час*, чтобы\n"
            f"внести залог *онлайн*.\n"
            f"⚠️ *Если в течение часа залог не будет внесён — бронь аннулируется*,\n"
            f"и автомобиль станет доступен другим клиентам.\n\n"
            f"🔐 После внесения залога мы оформим страховку на автомобиль,\n"
            f"и вы сможете забрать машину *завтра с 12:00*.\n\n"
            f"💸 *Залог будет возвращён сразу после сдачи автомобиля*,\n"
            f"как только механик завершит проверку состояния машины.\n\n"
            f"🪪 Не забудьте взять с собой *паспорт (оригинал)*.",
            parse_mode="Markdown"
        )
        # bot.send_message(
        #     telegram_id,
        #     f"✅ Ваша заявка на {service_display} одобрена!\n\n"
        #     f"{car_info}\n"
        #     f"{station_info}\n\n"
        #     f"💰 Для закрепления автомобиля необходимо внести залог *10 000 ₽*.\n"
        #     f"⏳ У вас есть *1 час*, чтобы:\n"
        #     f"— внести залог *онлайн*, или\n"
        #     f"— приехать на станцию и оплатить на месте *перед получением машины*.\n\n"
        #     f"⚠️ *Если в течение часа залог не будет внесён — бронь аннулируется*,\n"
        #     f"и автомобиль станет доступен другим клиентам.\n\n"
        #     f"🔐 После внесения залога машина будет *закреплена за вами*, и вы сможете забрать её *в любое удобное время*.\n\n"
        #     f"💸 *Залог будет возвращён сразу после сдачи автомобиля*,\n"
        #     f"как только механик завершит проверку состояния машины.\n\n"
        #     f"🪪 Не забудьте взять с собой *паспорт (оригинал)*.",
        #     parse_mode="Markdown"
        # )

        bot.send_message(admin_id, "✅ Заявка полностью одобрена и клиенту отправлено уведомление.")

    except Exception as e:
        bot.send_message(admin_id, f"❌ Ошибка при завершении одобрения: {e}")


# --------------------- 5. ОТПРАВКА ДОГОВОРА ОПЕРАТОРУ ---------------------
def send_contract_to_operator(operator_id, telegram_id):
    try:
        with db_lock, sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT contract_file_id
                FROM rental_history
                WHERE user_id = ?
                ORDER BY id DESC LIMIT 1
            """, (telegram_id,))
            row = cur.fetchone()

        if row and row[0]:
            bot.send_document(operator_id, row[0])
        else:
            bot.send_message(operator_id, "❌ Договор для этого клиента не найден.")
    except Exception as e:
        print(f"Ошибка 4713: {e}")


from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove


@bot.message_handler(func=lambda m: m.text in ["💳 Оплатить онлайн", "ℹ️ Информация об аренде", "📍 Я на месте"])
def handle_waiting_car_actions(message):
    print(2)
    try:
        print(1)
        user_id = message.from_user.id
        text = message.text

        # Проверка статуса пользователя
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT status FROM users WHERE telegram_id = ?", (user_id,))
        user = cur.fetchone()
        conn.close()

        if user and user["status"] == "new":
            # Удалить reply-кнопки (reply-клавиатуру)
            bot.send_message(
                message.chat.id,
                "Привет! Выберите действие:",
                reply_markup=types.ReplyKeyboardRemove()
            )

            # Показать Inline-кнопки
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton(
                    "🏠 Бронировать квартиры Тольятти",
                    url="https://homereserve.ru/RRNTTTVoul?tag=%D1%82%D0%B5%D0%BB%D0%B5%D0%B3%D1%80%D0%B0%D0%BC"
                )
            )
            markup.add(InlineKeyboardButton("🚕 Заказать такси", callback_data="taxi"))
            markup.add(InlineKeyboardButton("🏎 Аренда авто", callback_data="rent"))
            markup.add(InlineKeyboardButton("⛽ Заправки", callback_data="gas"))
            markup.add(InlineKeyboardButton("🔧 Ремонт авто", callback_data="rext"))
            markup.add(InlineKeyboardButton("💼 Вакансии", callback_data="jobs"))
            markup.add(types.InlineKeyboardButton("📩 Написать директору", url="https://t.me/Dagman42"))

            bot.send_message(user_id, f"📋 Всё что вам нужно здесь    ", reply_markup=markup)
            return  # Прекращаем обработку, ничего дальше не делаем
        if user and user["status"] == "waiting_rental":
            bot.send_message(
                message.chat.id,
                "Привет! Выберите действие:",
                reply_markup=types.ReplyKeyboardRemove()
            )
            rental_menu_kb = InlineKeyboardMarkup()
            rental_menu_kb.add(
                InlineKeyboardButton("🚕 Заказать такси", callback_data="taxi"),
                InlineKeyboardButton("🏎 Аренда", callback_data="rent"),
            )
            rental_menu_kb.add(
                InlineKeyboardButton("⛽ Заправки", callback_data="gas"),
                InlineKeyboardButton("🔧 Ремонт авто", callback_data="rext")
            )
            rental_menu_kb.add(
                InlineKeyboardButton("💼 Вакансии", callback_data="jobs"),
                types.InlineKeyboardButton("📩 Написать директору", url="https://t.me/Dagman42")
            )
            rental_menu_kb.add(
                InlineKeyboardButton("🧾 Моя аренда", callback_data="my_rental")
            )

            bot.send_message(
                message.chat.id,
                f"🚗 Привет! Добро пожаловать в меню аренды.",
                reply_markup=rental_menu_kb
            )
            return  # Прекращаем обработку, ничего дальше не делаем
        if user and user["status"] == "using_car":
            bot.send_message(
                message.chat.id,
                "Привет! Выберите действие:",
                reply_markup=types.ReplyKeyboardRemove()
            )
            show_main_menu(message.chat.id)
            return  # Прекращаем обработку, ничего дальше не делаем
        # Если статус НЕ "new", продолжаем как раньше
        if text == "💳 Оплатить онлайн":
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("✅ Я оплатил", callback_data=f"depositpaid_{user_id}"))

            bot.send_message(
                user_id,
                "💳 *Реквизиты для залога (10 000 ₽):*\n\n"
                "Получатель: Нугуманов Даниэль Радикович  \n"
                "СБП / Телефон: +7 9297107180  \n"
                "Карта МИР: 2200 7019 0981 4094  \n"
                "Комментарий: залог за авто\n\n"
                "❗ После перевода нажмите кнопку ниже.",
                parse_mode="Markdown",
                reply_markup=markup
            )

        elif text == "ℹ️ Информация об аренде":

            from datetime import datetime, timedelta

            with db_lock:

                conn = get_db_connection()

                conn.row_factory = sqlite3.Row

                cur = conn.cursor()

                # Получаем последнюю подтверждённую бронь

                cur.execute("""

                            SELECT bookings.id AS booking_id, bookings.car_id,

                                   cars.brand_model, cars.year, cars.station, cars.price,

                                   bookings.date, bookings.time, bookings.deposit_status, bookings.service

                            FROM bookings

                            JOIN cars ON bookings.car_id = cars.car_id

                            WHERE bookings.user_id = ? AND bookings.status = 'confirmed'

                            ORDER BY bookings.id DESC LIMIT 1

                        """, (user_id,))

                booking = cur.fetchone()

                info = ""

                if booking:

                    car_id = booking['car_id']

                    booking_id = booking['booking_id']

                    service = booking['service'].lower()

                    base_price = booking['price']

                    info += (

                        f"🚗 <b>Машина:</b> {booking['brand_model']} ({booking['year']})\n"

                        f"📍 <b>Станция:</b> {booking['station']}\n"

                        f"🗓 <b>Дата бронирования:</b> {booking['date']} в {booking['time']}\n"

                    )

                    # Получаем сроки аренды
                    print(car_id)
                    cur.execute("""

                                SELECT rent_start, rent_end

                                FROM rental_history

                                WHERE user_id = ? AND car_id = ?

                                ORDER BY id DESC LIMIT 1

                            """, (user_id, car_id))

                    rental = cur.fetchone()

                    if service == "rental":
                        if rental and rental['rent_start'] and rental['rent_end']:
                            rent_start = rental['rent_start']
                            rent_end = rental['rent_end']
                            info += f"🕒 <b>Срок аренды:</b> с {rent_start} до {rent_end}\n"

                            try:
                                start_date = datetime.strptime(rent_start, "%Y-%m-%d")
                                end_date = datetime.strptime(rent_end, "%Y-%m-%d")
                                total_days = (end_date - start_date).days
                                if total_days < 1:
                                    total_days = 1

                                total_price = calculate_price(base_price, total_days)
                                per_day_price = int(total_price) / int(total_days)
                                info += (
                                    f"💰 <b>Цена за день:</b> {per_day_price}₽\n"
                                    f"💵 <b>Итого за {total_days} дн.:</b> {total_price}₽\n"
                                )
                            except Exception as e:
                                info += f"\n⚠️ Ошибка при расчёте цены: {e}"
                        else:
                            info += "❌ Ошибка: не найдены даты аренды.\n"
                    else:  # rent
                        info += f"💰 <b>Цена за день:</b> {base_price}₽\n"

                    # Проверяем время действия брони

                    try:

                        booking_time = datetime.strptime(f"{booking['date']} {booking['time']}", "%Y-%m-%d %H:%M")

                        expire_time = booking_time + timedelta(minutes=60)

                        now = datetime.now()

                        deposit_status = booking['deposit_status'] or 'unpaid'

                        if now < expire_time:

                            if deposit_status != 'paid':

                                minutes_left = int((expire_time - now).total_seconds() // 60)

                                info += f"\n🔐 Ваша бронь действует ещё <b>{minutes_left} мин.</b>\n"

                            else:

                                info += "\n🚗 Подъезжайте на станцию и забирайте машину.\n"

                        else:

                            if deposit_status != 'paid':

                                # Время вышло и залог не внесён — сбрасываем бронь

                                cur.execute("UPDATE users SET status = 'new' WHERE telegram_id = ?", (user_id,))

                                conn.commit()

                                info += (

                                    "\n⛔ Время брони истекло, залог не был внесён.\n"

                                    "🚫 Машина снова доступна для других пользователей."

                                )

                            else:

                                info += "\n✅ Время брони истекло, но залог внесён. Машина закреплена за вами.\n"

                        # Показываем статус залога

                        status_display = "внесён" if deposit_status == 'paid' else "не внесён"

                        info += f"\n💳 <b>Залог:</b> {status_display}"


                    except Exception as e:

                        info += f"\n❌ Ошибка при расчёте времени: {e}"

                conn.close()

            if booking:

                bot.send_message(user_id, info, parse_mode="HTML")

            else:

                bot.send_message(user_id, "ℹ️ Не удалось найти информацию о бронированной машине.")








        elif text == "📍 Я на месте":

            from datetime import datetime, timedelta

            with db_lock:

                conn = get_db_connection()

                conn.row_factory = sqlite3.Row

                cur = conn.cursor()

                # Получаем последнюю подтвержденную бронь

                cur.execute("""

                        SELECT 

                            bookings.id AS booking_id,

                            bookings.car_id,

                            bookings.deposit_status,

                            bookings.status,

                            bookings.service,

                            cars.brand_model,

                            cars.year,

                            cars.station,

                            cars.number,

                            rh.sum_status,

                            rh.price,

                            rh.rent_start,

                            rh.rent_end,

                            users.full_name,

                            bookings.contract_file_id

                        FROM bookings

                        LEFT JOIN rental_history rh 

                            ON bookings.user_id = rh.user_id AND bookings.car_id = rh.car_id

                        JOIN cars ON bookings.car_id = cars.car_id
                        JOIN users ON bookings.user_id = users.telegram_id

                        WHERE bookings.user_id = ? AND bookings.status = 'confirmed'

                        ORDER BY bookings.id DESC

                        LIMIT 1

                    """, (user_id,))

                booking = cur.fetchone()

                if not booking:
                    bot.send_message(user_id, "❌ У вас нет активной брони.")

                    return

                operator_id = STATION_OPERATORS.get(booking["station"])

                # Отправляем договор оператору, если есть

                contract_file_id = booking["contract_file_id"]

                if operator_id and contract_file_id:
                    bot.send_message(operator_id,
                                     f"📄 Договор по машине {booking['brand_model']} для клиента {booking['full_name']}:")

                    bot.send_document(operator_id, contract_file_id)

                    # Достаём информацию

                    booking_id = booking["booking_id"]

                    car_id = booking["car_id"]

                    car_model = booking["brand_model"]

                    car_year = booking["year"]

                    car_station = booking["station"]

                    car_number = booking["number"]

                    deposit_status = booking["deposit_status"] or "unpaid"

                    sum_status = booking["sum_status"] or "unpaid"

                    service = booking["service"].lower()

                    contract_file_id = booking["contract_file_id"]
                    operator_id = STATION_OPERATORS.get(car_station)
                    print(operator_id)
                    price = booking["price"]

                    markup = InlineKeyboardMarkup()

                    if service in ("rental", "rent"):

                        needs_deposit = deposit_status != "paid"

                        needs_rent = (service == "rental" and sum_status != "paid")

                        if not needs_deposit and not needs_rent:

                            bot.send_message(

                                user_id,

                                f"✅ Отлично! Подойдите к стойке оператора на станции {car_station} для оформления документов.",

                                reply_markup=types.ReplyKeyboardRemove()

                            )

                            if operator_id:
                                with get_db_connection() as conn:
                                    cur = conn.cursor()

                                    cur.execute("UPDATE bookings SET docs_given = 1 WHERE id = ?", (booking_id,))

                                    conn.commit()

                                    cur.execute("SELECT full_name FROM users WHERE telegram_id = ?", (user_id,))

                                    row = cur.fetchone()

                                    full_name = row[0] if row else "клиента"

                                markup = InlineKeyboardMarkup()

                                markup.add(InlineKeyboardButton("➡️ Осмотр авто",

                                                                callback_data=f"continue_inspection_{booking_id}_{user_id}"))

                                bot.send_message(

                                    operator_id,

                                    f"📄 Заявка на машину:\n"

                                    f"ФИО: {full_name}\n"

                                    f"Марка: {car_model} ({car_year})\n"

                                    f"Госномер: {car_number}\n\n"

                                    f"🚗 Пожалуйста, откройте машину клиенту, чтобы он мог ознакомиться с договором.\n\n"

                                    f"❗ Важно: передача ключей происходит *только после* принятия копии договора.\n"

                                    f"Проверьте, указаны ли *даты и подписи* во всех необходимых местах.",

                                    parse_mode="Markdown",

                                )

                                bot.send_message(

                                    user_id,

                                    f"📄 Оператор открыл машину.\n\n"

                                    f"🚶 Сейчас подойдите к машине *{car_model}* *{car_number}*, чтобы ознакомиться с договором и осмотреть авто перед началом аренды.\n\n"

                                    f"🔓 От оператора вы получили две копии следующих документов:\n"

                                    f"• договор аренды\n"

                                    f"• соглашение о внесении залога\n"

                                    f"• приложение и обязательства арендатора\n\n"

                                    f"✍️ Поставьте дату и подпись на *обеих копиях* там, где это необходимо.\n\n"

                                    f"🧾 Один экземпляр оставьте в бардачке — он нужен для возможных проверок и подтверждения аренды.\n"

                                    f"📩 Второй экземпляр сдайте оператору, чтобы получить ключи от автомобиля.",

                                    parse_mode="Markdown",

                                    reply_markup=markup

                                )

                        else:

                            # Пользователю

                            payment_text = []

                            if needs_deposit:
                                payment_text.append("залог *10 000 ₽*")

                            if needs_rent:
                                payment_text.append(f"стоимость аренды *{int(price)} ₽*")

                            bot.send_message(

                                user_id,

                                f"💬 Подойдите к стойке оператора на станции {car_station} и оплатите: " + " и ".join(
                                    payment_text) + "."

                            )

                            # Оператору

                            if operator_id:

                                with get_db_connection() as conn:

                                    cur = conn.cursor()

                                    cur.execute("SELECT full_name FROM users WHERE telegram_id = ?", (user_id,))

                                    row = cur.fetchone()

                                    full_name = row[0] if row else "клиента"

                                operator_msg = (

                                    f"🚨 Заявка на машину:\n"

                                    f"Марка: {car_model} ({car_year})\n"

                                    f"Госномер: {car_number}\n"

                                    f"ФИО: {full_name}\n"

                                )

                                if service == "rent":

                                    if needs_deposit:

                                        markup.add(InlineKeyboardButton("🔐 Залог 10.000 ₽ принят",

                                                                        callback_data=f"deposit_paid_{booking_id}_{user_id}"))

                                        operator_msg += "Статус: ❗ Залог не оплачен.\n"

                                    else:

                                        operator_msg += "Статус: ✅ Залог оплачен.\n"


                                elif service == "rental":

                                    if needs_deposit:

                                        markup.add(InlineKeyboardButton("🔐 Залог 10.000 ₽ принят",

                                                                        callback_data=f"deposit_paid_{booking_id}_{user_id}"))

                                        operator_msg += "Статус: ❗ Залог не оплачен.\n"

                                    elif needs_rent:

                                        markup.add(InlineKeyboardButton(f"💸 Аренда {int(price)} ₽ оплачена",

                                                                        callback_data=f"rent_paid_{booking_id}_{user_id}"))

                                        operator_msg += "Статус: ✅ Залог оплачен.\n"

                                        operator_msg += f"💰 Аренда не оплачена — сумма {int(price)} ₽.\n"

                                    else:

                                        # Всё оплачено: оформление договора

                                        with get_db_connection() as conn:

                                            cur = conn.cursor()

                                            cur.execute("UPDATE bookings SET docs_given = 1 WHERE id = ?", (booking_id,))

                                            conn.commit()

                                        markup = InlineKeyboardMarkup()

                                        markup.add(InlineKeyboardButton("➡️ Осмотр авто",

                                                                        callback_data=f"continue_inspection_{booking_id}_{user_id}"))

                                        bot.send_message(

                                            user_id,

                                            f"📄 Оператор открыл машину.\n\n"

                                            f"🚶 Сейчас подойдите к машине *{car_model}* *{car_number}*, чтобы ознакомиться с договором и осмотреть авто перед началом аренды.\n\n"

                                            f"🔓 От оператора вы получили две копии следующих документов:\n"

                                            f"• договор аренды\n"

                                            f"• соглашение о внесении залога\n"

                                            f"• приложение и обязательства арендатора\n\n"

                                            f"✍️ Поставьте дату и подпись на *обеих копиях* там, где это необходимо.\n\n"

                                            f"🧾 Один экземпляр оставьте в бардачке — он нужен для возможных проверок и подтверждения аренды.\n"

                                            f"📩 Второй экземпляр сдайте оператору, чтобы получить ключи от автомобиля.",

                                            parse_mode="Markdown",

                                            reply_markup=markup

                                        )

                                        operator_msg += (

                                            f"\n📄 Все оплаты подтверждены.\n"

                                            f"Выдайте клиенту договор на имя {full_name}\n"

                                            f"🚗 Пожалуйста, откройте машину клиенту, чтобы он мог ознакомиться с договором.\n\n"

                                            f"❗ Важно: передача ключей происходит *только после* принятия копии договора.\n"

                                            f"Проверьте, указаны ли *даты и подписи* во всех необходимых местах."

                                        )

                                bot.send_message(operator_id, operator_msg, reply_markup=markup, parse_mode="Markdown")

    except Exception as e:
        print(f"Ошибка 5329: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("depositpaid_"))
def handle_deposit_paid(call):
    try:
        user_id = int(call.data.split("_")[-1])
        bot.answer_callback_query(call.id, "Спасибо! Ожидайте подтверждения.")

        full_name = "Неизвестно"
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT full_name, phone FROM users WHERE telegram_id = ?", (user_id,))
                row = cur.fetchone()
                if row:
                    full_name = row["full_name"]
                    phone = row["phone"]
        except Exception as e:
            print(f"[handle_deposit_paid] Ошибка: {e}")
        print(user_id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Залог пришел", callback_data=f"depositconfirm_{user_id}"))

        operator_id = DAN_TELEGRAM_ID
        bot.send_message(
            operator_id,
            f"💰 Пользователь *{full_name}*  {phone} сообщил об оплате залога.\n"
            "Проверьте поступление средств.\n\n"
            "Нажмите кнопку, когда подтвердите получение.",
            parse_mode="Markdown",
            reply_markup=markup
        )
    except Exception as e:
        print(f"Ошибка 5363: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("depositconfirm_"))
def handle_confirm_deposit(call):
    try:
        try:
            bot.answer_callback_query(call.id, "Подтверждение получено.")
        except ApiTelegramException as e:
            print(f"[handle_confirm_deposit] answer_callback_query failed: {e}")

        user_id = int(call.data.split("_")[-1])
        print(user_id)

        # Отправляем клиенту подтверждение
        try:
            bot.send_message(user_id, "✅ Ваш залог подтвержден. Спасибо!")
        except ApiTelegramException as e:
            print(f"[handle_confirm_deposit] send_message to {user_id} failed: {e}")

        # Обновляем статус в базе
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE bookings SET deposit_status = 'paid' WHERE user_id = ? AND status = 'confirmed'",
                (user_id,)
            )
            cur.execute(
                "UPDATE users SET status = 'waiting_rental' WHERE telegram_id = ?",
                (user_id,)
            )
            conn.commit()
        # Редактируем сообщение у оператора
        try:
            bot.edit_message_text(
                "✅ Залог подтверждён.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None
            )
        except ApiTelegramException as e:
            print(f"[handle_confirm_deposit] edit_message_text failed: {e}")
    except Exception as e:
        print(f"Ошибка 5406: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("deposit_paid_"))
def handle_deposit_paid(call):
    try:
        bot.answer_callback_query(call.id, "✅ Залог отмечен как оплаченный.")

        _, _, booking_id, user_id = call.data.split("_")
        booking_id = int(booking_id)
        user_id = int(user_id)

        with get_db_connection() as conn:
            cur = conn.cursor()

            # Обновляем статус залога
            cur.execute("UPDATE bookings SET deposit_status = 'paid' WHERE id = ?", (booking_id,))
            conn.commit()

            # Получаем тип услуги + ФИО клиента
            cur.execute("SELECT service FROM bookings WHERE id = ?", (booking_id,))
            result = cur.fetchone()
            if not result:
                bot.send_message(user_id, "❌ Ошибка: бронь не найдена.")
                return

            service = result[0].lower()

            cur.execute("SELECT full_name FROM users WHERE telegram_id = ?", (user_id,))
            user_row = cur.fetchone()
            full_name = user_row[0] if user_row else "клиента"

            # Получаем данные об автомобиле
            cur.execute("""
                SELECT cars.brand_model, cars.number, cars.price
                FROM bookings
                JOIN cars ON bookings.car_id = cars.car_id
                WHERE bookings.id = ?
            """, (booking_id,))
            car_row = cur.fetchone()
            if not car_row:
                bot.send_message(user_id, "❌ Ошибка: автомобиль не найден.")
                return

            car_model, car_number, car_price = car_row
            # Получаем даты аренды

        if service == "rent":
            bot.send_message(user_id, "✅ Оператор подтвердил получение залога.",
                             reply_markup=types.ReplyKeyboardRemove())
        bot.send_message(user_id, "✅ Оператор подтвердил получение залога.")
        markup = InlineKeyboardMarkup()
        operator_msg = ""

        if service == "rental":
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                            SELECT price
                            FROM rental_history
                            WHERE user_id = ? AND status = 'confirmed'
                        """, (user_id,))
                rent_row = cur.fetchone()
                if not rent_row or rent_row[0] is None:
                    bot.send_message(user_id, "❌ Ошибка: не найдена цена.")
                    return

            price = rent_row[0]
            # Следующий шаг — оплата аренды
            markup.add(InlineKeyboardButton(
                f"💸 Аренда {price} ₽ оплачена",
                callback_data=f"rent_paid_{booking_id}_{user_id}"
            ))

            operator_msg = (
                f"💰 Залог получен.\n"
                f"Пожалуйста, примите оплату за аренду у клиента."
            )
            try:
                bot.edit_message_reply_markup(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=None
                )
            except Exception as e:
                print(f"Ошибка при удалении кнопки: {e}")
            bot.send_message(call.message.chat.id, operator_msg, reply_markup=markup)

        else:  # краткосрочная аренда
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("➡️ Осмотр авто", callback_data=f"continue_inspection_{booking_id}_{user_id}"))

            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE bookings SET docs_given = 1 WHERE id = ?", (booking_id,))
                conn.commit()

            bot.send_message(
                user_id,
                f"📄 Оператор открыл машину.\n\n"
                f"🚶 Сейчас подойдите к машине *{car_model}* *{car_number}*, чтобы ознакомиться с договором и осмотреть авто перед началом аренды.\n\n"
                f"🔓 От оператора вы получили две копии следующих документов:\n"
                f"• договор аренды\n"
                f"• соглашение о внесении залога\n"
                f"• приложение и обязательства арендатора\n\n"
                f"✍️ Впишите паспортные данные, поставьте дату и подпись на *обеих копиях* там, где это необходимо.\n\n"
                f"🧾 Один экземпляр оставьте в бардачке — он нужен для возможных проверок и подтверждения аренды.\n"
                f"📩 Второй экземпляр сдайте оператору, чтобы получить ключи от автомобиля.",
                parse_mode="Markdown",
                reply_markup=markup
            )

            operator_msg = (
                f"📄 Залог получен от клиента\n Выдайте клиенту договор на имя *{full_name}*.\n\n"
                f"🚗 Пожалуйста, откройте машину клиенту, чтобы он мог ознакомиться с договором.\n\n"
                f"❗ Важно: передача ключей происходит *только после* принятия копии договора.\n"
                f"Проверьте, указаны ли *даты и подписи* во всех необходимых местах."
            )

            bot.send_message(call.message.chat.id, operator_msg, parse_mode="Markdown")

    except Exception as e:
        print(f"❌ Ошибка в handle_deposit_paid: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("rent_paid_"))
def handle_rent_paid(call):
    try:
        bot.answer_callback_query(call.id, "✅ Аренда отмечена как оплаченная.")

        parts = call.data.split("_")
        booking_id = int(parts[2])
        user_id = int(parts[3])

        with get_db_connection() as conn:
            cur = conn.cursor()

            cur.execute("UPDATE bookings SET docs_given = 1 WHERE id = ?", (booking_id,))
            conn.commit()
            # Находим rental_history запись по user_id и статусу confirmed
            cur.execute(
                "SELECT id FROM rental_history WHERE user_id = ? AND status = 'confirmed'",
                (user_id,)
            )
            row = cur.fetchone()
            if not row:
                bot.send_message(user_id, "❌ Ошибка: запись аренды не найдена.")
                return
            rental_history_id = row[0]

            # Обновляем sum_status в rental_history
            cur.execute(
                "UPDATE rental_history SET sum_status = 'paid' WHERE id = ?",
                (rental_history_id,)
            )
            conn.commit()

            # Получаем данные для оператора
            cur.execute("""
                SELECT 
                    b.car_id,
                    c.brand_model,
                    c.year,
                    c.station,
                    c.number,
                    u.full_name
                FROM bookings b
                JOIN cars c ON b.car_id = c.car_id
                JOIN users u ON b.user_id = u.telegram_id
                WHERE b.id = ?
            """, (booking_id,))
            booking_info = cur.fetchone()

        if not booking_info:
            bot.send_message(user_id, "❌ Ошибка: информация о бронировании не найдена.")
            return

        car_model = booking_info[1]
        car_year = booking_info[2]
        car_station = booking_info[3]
        car_number = booking_info[4]
        full_name = booking_info[5]

        operator_id = STATION_OPERATORS.get(car_station)

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("➡️ Осмотр авто", callback_data=f"continue_inspection_{booking_id}_{user_id}"))

        bot.send_message(
            user_id,
            f"📄 Оператор открыл машину.\n\n"
            f"🚶 Сейчас подойдите к машине *{car_model}* *{car_number}*, чтобы ознакомиться с договором и осмотреть авто перед началом аренды.\n\n"
            f"🔓 От оператора вы получили две копии следующих документов:\n"
            f"• договор аренды\n"
            f"• соглашение о внесении залога\n"
            f"• приложение и обязательства арендатора\n\n"
            f"✍️ Впишите паспортные данные, поставьте дату и подпись на *обеих копиях* там, где это необходимо.\n\n"
            f"🧾 Один экземпляр оставьте в бардачке — он нужен для возможных проверок и подтверждения аренды.\n"
            f"📩 Второй экземпляр сдайте оператору, чтобы получить ключи от автомобиля.",
            parse_mode="Markdown",
            reply_markup=markup
        )

        # 2. Сообщение оператору — с кнопкой
        if operator_id:

            operator_msg = (
                f"📄 Все оплаты подтверждены.\n"

                f"Марка: {car_model} ({car_year})\n"
                f"Госномер: {car_number}\n\n"
                f"Выдайте клиенту договор на имя {full_name}\n"
                f"🚗 Пожалуйста, откройте машину клиенту, чтобы он мог ознакомиться с договором.\n\n"
                f"❗ Важно: передача ключей происходит *только после* принятия копии договора.\n"
                f"Проверьте, указаны ли *даты и подписи* во всех необходимых местах."
            )

            bot.send_message(operator_id, operator_msg, parse_mode="Markdown")
        else:
            bot.send_message(call.message.chat.id, "⚠️ Оператор не найден.")

    except Exception as e:
        print(f"Ошибка в handle_rent_paid: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("docs_given_"))
def handle_keys_given(call):
    try:
        _, _, booking_id, user_id = call.data.split("_")
        booking_id = int(booking_id)
        user_id = int(user_id)

        # Получаем данные о машине, пользователе и фото паспорта
        with get_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("""
                SELECT 
                    b.car_id,
                    c.brand_model,
                    c.number,
                    c.station,
                    u.full_name,
                    u.passport_front_photo,
                    u.passport_back_photo
                FROM bookings b
                JOIN cars c ON b.car_id = c.car_id
                JOIN users u ON b.user_id = u.telegram_id
                WHERE b.id = ?
            """, (booking_id,))
            row = cur.fetchone()

        if not row:
            bot.send_message(call.from_user.id, "❌ Бронирование не найдено.")
            return

        car_model = row["brand_model"]
        car_number = row["number"]
        station = row["station"]
        full_name = row["full_name"]
        passport_front = row["passport_front_photo"]
        passport_back = row["passport_back_photo"]

        operator_id = STATION_OPERATORS.get(station)
        if not operator_id:
            bot.send_message(call.from_user.id, "❌ Не удалось определить оператора для этой станции.")
            return

        # Сообщение оператору
        operator_msg = (
            f"📄 Клиент *{full_name}* передаёт вам договор на аренду автомобиля:\n"
            f"🚗 *{car_model}* — *{car_number}*\n\n"
            f"🔍 Проверьте, чтобы:\n"
            f"• все даты и подписи были заполнены\n")
        # operator_msg = (
        #     f"📄 Клиент *{full_name}* передаёт вам договор на аренду автомобиля:\n"
        #     f"🚗 *{car_model}* — *{car_number}*\n\n"
        #     f"🔍 Проверьте, чтобы:\n"
        #     f"• все даты аренды были заполнены\n"
        #     f"• подписи клиента стояли в нужных местах (4 подписи)\n"
        #     f"• паспортные данные были заполнены в 2 местах\n"
        #     f"• данные в договоре совпадали с паспортом\n\n"
        #     f"📌 Фото паспорта отправлены ниже для сверки."
        # )

        operator_markup = InlineKeyboardMarkup()
        operator_markup.add(
            InlineKeyboardButton("📄 Договор принят", callback_data=f"keys_given_{booking_id}_{user_id}")
        )

        bot.send_message(
            operator_id,
            operator_msg,
            parse_mode="Markdown",
            reply_markup=operator_markup  # ← прикрепляем клавиатуру
        )
        # # 2️⃣ Отправляем фото
        # if passport_front:
        #     bot.send_photo(operator_id, passport_front, caption="📄 Паспорт (лицевая сторона)")
        #
        # if passport_back:
        #     # Кнопка под последним фото
        #     bot.send_photo(operator_id, passport_back, caption="📄 Паспорт (обратная сторона)",
        #                    reply_markup=operator_markup)
        # else:
        #     # Если задней стороны нет — кнопку ставим после переднего фото
        #     if passport_front:
        #         bot.send_message(operator_id, "📄 Подтвердите приём договора:", reply_markup=operator_markup)
    except Exception as e:
        print(f"[handle_keys_given] ❌ Ошибка: {e}")


sent_messages = {}


@bot.callback_query_handler(func=lambda call: call.data.startswith("keys_given_"))
def handle_keys_transfer(call):
    try:
        parts = call.data.split("_")
        booking_id = int(parts[-2])
        user_id = int(parts[-1])

        # Получаем данные о машине и клиенте
        with get_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("""
                SELECT c.brand_model, c.number, c.station, u.full_name
                FROM bookings b
                JOIN cars c ON b.car_id = c.car_id
                JOIN users u ON b.user_id = u.telegram_id
                WHERE b.id = ?
            """, (booking_id,))
            row = cur.fetchone()

        if not row:
            bot.send_message(call.from_user.id, "❌ Ошибка: данные бронирования не найдены.")
            return

        car_model = row["brand_model"]
        car_number = row["number"]
        full_name = row["full_name"]

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🔑 Ключи переданы", callback_data=f"finished_confirmation_{booking_id}_{user_id}"))

        msg_op = bot.send_message(
            call.from_user.id,
            f"✅ Отлично! Теперь передайте клиенту ключи от автомобиля *{car_model}* *{car_number}*.",
            parse_mode="Markdown",
            reply_markup=markup
        )
        sent_messages.setdefault(call.from_user.id, []).append(msg_op.message_id)
    except Exception as e:
        print(f"[handle_keys_transfer] ❌ Ошибка: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("continue_inspection_"))
def handle_inspection_start(call):
    try:
        parts = call.data.split("_")
        booking_id = int(parts[-2])
        user_id = int(parts[-1])

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Я осмотрел автомобиль", callback_data=f"inspection_done_{booking_id}_{user_id}"))

        instructions = (
            "🛠 <b>Инструкция по осмотру:</b>\n"
            "- Проверьте кузов на наличие вмятин, царапин, сколов\n"
            "- Осмотрите стёкла и зеркала\n"
            "- Проверьте салон\n"
            "- Зафиксируйте уровень газа и пробег\n\n"
            "Если что-то заметите — сообщите дальше."
        )
        bot.send_message(user_id, instructions, parse_mode="HTML", reply_markup=markup)
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Ошибка 5788: {e}")


inspection_states = {}
user_contract_data = {}


@bot.callback_query_handler(func=lambda call: call.data.startswith("inspection_done_"))
def handle_contract_display(call):
    try:
        parts = call.data.split("_")
        booking_id = int(parts[-2])
        user_id = int(parts[-1])

        # Сохраняем начальное состояние
        inspection_states[user_id] = {
            "booking_id": booking_id,
            "confirmations": {
                "gas": False,
                "mileage": False,
                "scratches": False,
                "cleanliness": False
            },
            "reported_issue": False
        }

        message = (
            f"🚗 <b>Проверьте автомобиль</b>"
            f"Пожалуйста, подтвердите следующее перед продолжением:")

        bot.send_message(user_id, message, parse_mode="HTML", reply_markup=generate_inspection_buttons(user_id))
        bot.answer_callback_query(call.id)

    except Exception as e:
        print(f"Ошибка 5822: {e}")

def generate_inspection_buttons(user_id):
    try:
        state = inspection_states.get(user_id, {})
        confirmations = state.get("confirmations", {})
        print(f"[generate_inspection_buttons] user_id={user_id}, state={state}")

        def mark(param):
            return "☑" if confirmations.get(param) else "☐"

        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton(f"{mark('gas')} Уровень газа соответствует", callback_data=f"inspect_confirm_gas"),
            InlineKeyboardButton(f"{mark('mileage')} Километраж соответствует", callback_data=f"inspect_confirm_mileage"),
            InlineKeyboardButton(f"{mark('scratches')} Царапин нет", callback_data=f"inspect_confirm_scratches"),
            InlineKeyboardButton(f"{mark('cleanliness')} Машина чистая", callback_data=f"inspect_confirm_cleanliness"),
            InlineKeyboardButton("❗ Сообщить о проблеме", callback_data="inspect_report_problem")
        )

        if all(confirmations.values()) or state.get("reported_issue"):
            cb_data = f"sign_contract_{state['booking_id']}_{user_id}"
            print(f"[generate_inspection_buttons] ➕ Добавлена кнопка с callback_data: {cb_data}")
            markup.add(InlineKeyboardButton("✅ Продолжить к договору", callback_data=cb_data))
        return markup
    except Exception as e:
        print(f"Ошибка 5848: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("inspect_confirm_"))
def handle_inspection_confirm(call):
    try:
        user_id = call.from_user.id
        param = call.data.split("_")[-1]  # gas / mileage / scratches / cleanliness

        state = inspection_states.setdefault(user_id, {"confirmations": {}, "reported_issue": False})
        current = state["confirmations"].get(param, False)
        state["confirmations"][param] = not current

        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                      reply_markup=generate_inspection_buttons(user_id))
    except Exception as e:
        print(f"Ошибка 5865: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "inspect_report_problem")
def handle_inspection_problem(call):
    try:
        user_id = call.from_user.id
        inspection_states.setdefault(user_id, {"confirmations": {}, "reported_issue": False})
        session = get_session(user_id)

        session["state"] = "waiting_for_issue_description"

        bot.answer_callback_query(call.id, "Опишите проблему и прикрепите фото")

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="inspect_back_to_check"))

        bot.send_message(user_id, "📝 Пожалуйста, опишите проблему (текстом). После этого пришлите фото.",
                         reply_markup=markup)

        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                          reply_markup=generate_inspection_buttons(user_id))
        except telebot.apihelper.ApiTelegramException as e:
            if "message is not modified" in str(e):
                pass
            else:
                raise
    except Exception as e:
        print(f"Ошибка 5894: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "inspect_back_to_check")
def handle_back_to_inspection(call):
    try:
        user_id = call.from_user.id

        # Удаляем временное состояние описания проблемы
        session = get_session(user_id)
        session["state"] = None

        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🚗 <b>Проверьте автомобиль</b>\nПожалуйста, подтвердите следующее перед продолжением:",
            parse_mode="HTML",
            reply_markup=generate_inspection_buttons(user_id)
        )
    except Exception as e:
        print(f"Ошибка 5915: {e}")


# 📋 Хендлер для описания проблемы при осмотре автомобиля
@bot.message_handler(func=lambda m: get_session(m.from_user.id).get("state") == "waiting_for_issue_description",
                     content_types=["text"])
def handle_issue_description(message):
    try:
        user_id = message.from_user.id
        session = get_session(user_id)

        session["inspection_issue_text"] = message.text
        session["state"] = "waiting_for_issue_photo"
        bot.send_message(user_id, "📸 Теперь пришлите фото, связанное с проблемой.")
    except Exception as e:
        print(f"Ошибка 5930: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("sign_contract_"))
def handle_contract_signed(call):
    try:
        parts = call.data.split("_")
        booking_id = int(parts[-2])
        user_id = int(parts[-1])
        bot.answer_callback_query(call.id)

        # Получаем данные о клиенте и машине из базы
        with get_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("""
                SELECT 
                    u.full_name,
                    c.brand_model,
                    c.number
                FROM bookings b
                JOIN cars c ON b.car_id = c.car_id
                JOIN users u ON b.user_id = u.telegram_id
                WHERE b.id = ?
            """, (booking_id,))
            row = cur.fetchone()

        if not row:
            bot.send_message(user_id, "❌ Не удалось найти данные по бронированию.")
            return

        full_name = row["full_name"]
        car_model = row["brand_model"]
        car_number = row["number"]

        # Инициализация хранилища пользователя
        if user_id not in user_contract_data:
            user_contract_data[user_id] = {}
        user_contract_data[user_id]["awaiting_document"] = True

        # Инструкция по заполнению договора
        bot.send_message(
            user_id,
            f"📄 *{full_name}*, перед тем как передать договор на аренду автомобиля оператору, "
            f"пожалуйста, убедитесь, что *все поля заполнены*.\n\n"
            f"📌 Поставьте подписи и даты, где это необходимо\n",
            parse_mode="Markdown"
        )
        # bot.send_message(
        #     user_id,
        #     f"📄 *{full_name}*, перед тем как передать договор на аренду автомобиля оператору, "
        #     f"пожалуйста, убедитесь, что *все поля заполнены*.\n\n"
        #     f"🚗 Автомобиль: *{car_model}* — *{car_number}*\n\n"
        #     f"✅ Что нужно сделать:\n"
        #     f"1️⃣ Поставить даты аренды (все даты в договоре).\n"
        #     f"2️⃣ Проставить свою подпись в *4 местах*, отмеченных для 'Арендатора'.\n"
        #     f"3️⃣ Заполнить паспортные данные в *2 местах* "
        #     f"(серия, номер, кем и когда выдан, код подразделения).\n"
        #     f"4️⃣ Заполнить ФИО, дату рождения, место рождения, адрес регистрации и проживания, телефон.\n\n"
        #     f"📌 *Пример заполнения:*\n"
        #     f"Иванов Иван Иванович,\n"
        #     f"дата рождения: 15.04.1990,\n"
        #     f"место рождения: г. Москва\n"
        #     f"адрес регистрации: г. Москва, ул. Ленина, д. 15, кв. 45\n"
        #     f"адрес фактического проживания: г. Москва, ул. Мира, д. 7, кв. 12\n"
        #     f"паспорт РФ 45 12 345678\n"
        #     f"Код подразделения: 770-001,\n"
        #     f"Телефон: +7 (916) 123-45-67\n"
        #     f"__________________________/Иванов И.И./\n"
        #     f"(подпись арендатора, дата)\n",
        #     parse_mode="Markdown"
        # )
        # Кнопка подтверждения
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Я подписал договор", callback_data=f"docs_given_{booking_id}_{user_id}")
        )

        msg = bot.send_message(user_id, "Когда вы подпишете договор, нажмите на кнопку ниже 👇", reply_markup=markup)
        sent_messages.setdefault(user_id, []).append(msg.message_id)
    except Exception as e:
        print(f"[handle_contract_signed] ❌ Ошибка: {e}")
        error_log = getattr(bot, 'error_log', {})
        error_log[user_id] = str(e)
        bot.error_log = error_log


@bot.callback_query_handler(func=lambda call: call.data.startswith("finished_confirmation"))
def handle_doc_verification(call):
    try:
        parts = call.data.split("_")
        booking_id = int(parts[-2])
        user_id = int(parts[-1])

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Обновляем статус пользователя
        cur.execute("UPDATE users SET status = ? WHERE telegram_id = ?", ("using_car", user_id))

        # Обновляем статус бронирования
        cur.execute("UPDATE bookings SET status = 'process' WHERE user_id = ?", (user_id,))

        # Получаем rental_history для user_id, если нужно
        cur.execute("""
            SELECT rent_end, price
            FROM rental_history
            WHERE user_id = ? AND status = 'confirmed'
            ORDER BY id DESC LIMIT 1
        """, (user_id,))
        rental = cur.fetchone()

        if rental:
            rent_end_date = rental["rent_end"]
            price = rental["price"]
            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            now_time = datetime.now().strftime("%H:%M:%S")
            end_time = f"{rent_end_date} {now_time}"

            cur.execute("""
                UPDATE rental_history
                SET start_time = ?, end_time = ?
                WHERE user_id = ? AND status = 'confirmed'
            """, (start_time, end_time, user_id))
        else:
            price = 0
        # Найти название станции по оператору call.from_user.id
        operator_id = call.from_user.id
        station_address = None

        for addr, op_id in STATION_OPERATORS.items():
            if op_id == operator_id:
                station_address = addr
                print(f"Адрес станции по оператору: {station_address}")
                break

        if station_address:
            station_code = STATION_ADDRESSES_TO_CODES.get(station_address)
            print(f"Код станции: {station_code}")

            cur.execute("""
                UPDATE shifts
                SET cars_sold = COALESCE(cars_sold, 0) + 1,
                    sold_sum = COALESCE(sold_sum, 0) + ?
                WHERE station = ? AND active = 1
            """, (price, station_code))
        # Получаем имя и телефон пользователя
        cur.execute("SELECT name, phone, purpose FROM users WHERE telegram_id = ?", (user_id,))
        user_info = cur.fetchone()
        name, phone, purpose = user_info
        conn.commit()
        conn.close()
        print(name, phone, purpose)
        # Уведомление пользователя
        bot.answer_callback_query(call.id, "Документы подтверждены.")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("/start")  # кнопка, которая отправляет команду /start
        bot.send_message(user_id,
                         "🎉 Отлично! Теперь вы — официальный клиент нашей компании.\n\nНажмите на кнопку снизу, чтобы начать аренду.",
                         reply_markup=markup)

        # Если пользователь шёл в такси — отправим уведомление
        if purpose == "taxi" and user_info:
            bot.send_message(
                TAXI_SETUP_MANAGER_ID,
                f"🚖 Пользователь готов к устройству в такси:\n"
                f"👤 Имя: {name}\n"
                f"📞 Телефон: {phone}\n"
                f"🆔 Telegram ID: {user_id}"
            )

    except Exception as e:
        print(f"[handle_doc_verification] Ошибка: {e}")


@bot.message_handler(commands=['set_deposit'])
def set_deposit_status(message):
    if message.from_user.id != ADMIN_ID2:
        bot.reply_to(message, "❌ У тебя нет прав на выполнение этой команды.")
        return

    try:
        _, booking_id, status = message.text.strip().split()
        status = status.lower()

        if status not in ['paid', 'unpaid']:
            bot.reply_to(message, "❗ Статус должен быть 'paid' или 'unpaid'.")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("UPDATE bookings SET deposit_status = ? WHERE id = ?", (status, booking_id))
        conn.commit()
        conn.close()

        bot.reply_to(message, f"✅ Статус залога для заявки #{booking_id} обновлён на: {status}")

    except ValueError:
        bot.reply_to(message, "⚠️ Неверный формат команды. Пример: /set_deposit 12 paid")
    except Exception as e:
        bot.reply_to(message, f"🚫 Ошибка: {e}")


@bot.message_handler(
    func=lambda message: (get_state(message.from_user.id) or "").startswith("waiting_for_time_selection|"))
def handle_date_selection(message):
    try:
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
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
                SELECT time FROM bookings
                WHERE date = ? AND status = 'confirmed'
            """, (date_str,))
        booked_times = set(t[0] for t in c.fetchall())

        # Формируем inline-клавиатуру
        markup = types.InlineKeyboardMarkup(row_width=3)
        has_available = False

        for hour in range(10, 19):  # Время с 10:00 до 19:59
            for minute in range(0, 60, 30):  # каждые 10 минут
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

    except Exception as e:
        print(f"Ошибка 6194: {e}")
from datetime import datetime

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
        try:
            _, service, car_id_str, date_str, time_str = call.data.split("|")
            car_id = int(car_id_str) if car_id_str.isdigit() else 0
        except Exception:
            bot.answer_callback_query(call.id, text="Ошибка данных.")
            return

        telegram_id = call.from_user.id
        chat_id = call.message.chat.id
        bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      reply_markup=None)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Получаем пользователя по telegram_id
            cursor.execute("SELECT id, telegram_id, name, phone FROM users WHERE telegram_id = ?", (telegram_id,))
            user_row = cursor.fetchone()
            if not user_row:
                bot.send_message(chat_id, "⚠️ Вы не зарегистрированы. Нажмите /start.")
                return

            user_id = user_row['id']
            user_telegram_id = user_row['telegram_id']
            phone = user_row['phone']
            session = get_session(user_telegram_id)
            session["selected_service"] = service

            full_name = user_row['name']

            # Сохраняем бронирование
            cursor.execute("""
                    INSERT INTO bookings (service, car_id, user_id, date, time, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (service, car_id, user_telegram_id, date_str, time_str, 'pending'))
            conn.commit()

            # if car_id != 0 and car_id is not None:
            # cursor.execute("UPDATE cars SET is_available = 0 WHERE car_id = ?", (car_id,))
            # conn.commit()

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
            "rental": "прокат"
        }.get(service, None)

        # Если service не один из стандартных — ищем в таблице jobs
        if service_display is None:
            profession_key = service  # service содержит profession_key
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT title FROM jobs WHERE profession = ?", (profession_key,))
            job = cursor.fetchone()
            conn.close()
            if job:
                service_display = job['title']
            else:
                service_display = service  # fallback, если не нашли

        # Формируем клавиатуру (без кнопки "Ответить")
        car_id_str = car_id_str if car_id_str.isdigit() else "0"
        markup = types.InlineKeyboardMarkup()

        if service != "return":
            markup.add(
                types.InlineKeyboardButton(
                    "✅ Принять",
                    callback_data=f"approve_{service}_{car_id_str}_{user_id}_{user_telegram_id}_{date_str}_{time_str}"
                )
            )
        else:
            markup.add(
                types.InlineKeyboardButton(
                    "✅ Принять",
                    callback_data=f"chooseplace_{service}_{car_id_str}_{user_id}_{user_telegram_id}_{date_str}_{time_str}"
                )
            )

        markup.add(
            types.InlineKeyboardButton(
                "🕒 Предложить другое время",
                callback_data=f"suggest_{car_id_str}_{user_telegram_id}"
            )
        )

        if service != "return":
            markup.add(
                types.InlineKeyboardButton(
                    "❌ Отклонить",
                    callback_data=f"reject_{car_id_str}_{user_telegram_id}"
                )
            )
        else:
            markup.add(
                types.InlineKeyboardButton(
                    "❌ Отговорил",
                    callback_data=f"remind_{car_id_str}_{user_telegram_id}"
                )
            )

        # Добавляем кнопку "Водительское удостоверение", только если сервис не painter
        if service in ["rent", "rental", "gazel"]:
            markup.add(types.InlineKeyboardButton(
                "📄 Водительское удостоверение",
                callback_data=f"show_documents_{user_telegram_id}"
            ))

        # Формируем сообщение админу
        message_text = (
            f"📥 Новая заявка:\n\n"
            f"👤 Имя: {full_name}\n"
            f" Телефон: {phone}\n"
            f"🛠 Услуга: {service_display}\n"
            f"📅 Дата: {date_str}\n"
            f"⏰ Время: {time_str}"
        )

        if car:
            brand_model, year = car['brand_model'], car['year']
            message_text += f"\n🚗 Машина: {brand_model} ({year})"

        message_text += delivery_info

        if service == "return":
            bot.send_message(ADMIN_ID2, message_text, reply_markup=markup)
        else:
            bot.send_message(DIRECTOR_ID, message_text, reply_markup=markup)
        bot.send_message(user_telegram_id, f"✅Отлично!\nМы Уже отправили заявку админу. Это может занять некоторое время")

    except Exception as e:
        print(f"Ошибка 6365: {e}")
addresses = {
        "addr1": "Южное шоссе 129",
        "addr2": "Южное шоссе 12/2",
        "addr3": "Лесная 66А",
        "addr4": "Борковская 59",
        "addr5": "Борковская 72/1"
}



# В chooseplace_ callback handler
@bot.callback_query_handler(func=lambda call: call.data.startswith('chooseplace_'))
def chooseplace_callback_handler(call):
    try:
        user_data = call.data[len('chooseplace_'):]  # все параметры
        # Сохраняем где-то, например в словаре
        session[call.from_user.id] = user_data  # sessions — глобальный словарь

        markup = types.InlineKeyboardMarkup(row_width=1)
        for key, name in addresses.items():
            markup.add(types.InlineKeyboardButton(name, callback_data=f"address_{key}"))
        bot.send_message(call.message.chat.id, "Выберите адрес:", reply_markup=markup)
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Ошибка 6390: {e}")
    # Сохраняем параметры после префикса 'chooseplace_' в словарь, используя chat_id как ключ



@bot.callback_query_handler(func=lambda call: call.data.startswith('address_'))
def address_callback_handler(call):
    try:
        addr_key = call.data[len('address_'):]
        address = addresses.get(addr_key, "Неизвестный адрес")

        # Получаем сохранённые данные для пользователя
        user_data = session.get(call.from_user.id)
        if not user_data:
            bot.answer_callback_query(call.id, "Ошибка: данные не найдены.")
            return

        # Разбираем user_data, например: service_carid_userid_usertelegramid_date_time
        parts = user_data.split('_')
        service = parts[0]
        car_id = parts[1]
        user_id = int(parts[2])
        user_telegram_id = int(parts[3])
        date_str = parts[4]
        time_str = parts[5]
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        update_query = '''
                                UPDATE bookings
                                SET status = 'confirmed'
                                WHERE service = ? AND car_id = ? AND user_id = ? AND date = ? AND time = ?
                            '''
        params = (service, car_id, user_telegram_id, date_str, time_str)

        print(service, car_id, user_telegram_id, date_str, time_str)
        cursor.execute(update_query, params)
        conn.commit()

        # Далее запрос к базе и отправка сообщений как раньше
        cursor.execute(
            "SELECT date, time FROM bookings WHERE user_id=? AND car_id=? AND status='process' ORDER BY created_at DESC LIMIT 1",
            (user_id, car_id))
        booking = cursor.fetchone()
        if booking:
            date_str = booking[0]
            time_str = booking[1]

        client_msg = f"Ваша заявка на сдачу авто принята.\nВстреча назначена на {date_str} в {time_str}.\nАдрес встречи: {address}."
        bot.send_message(user_telegram_id, client_msg)
        bot.send_message(call.message.chat.id, f"Клиенту отправлено сообщение с адресом: {address}")

        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Ошибка 6444: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("remind_"))
def handle_remind(call):
    try:
        # Данные: remind_{car_id}_{user_telegram_id}
        _, car_id_str, user_telegram_id_str = call.data.split("_")
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        # Можно выполнить действия с базой или логикой:
        # Например, отметить заявку как "отговорена" или удалить её
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Пример: удалим заявку у админа (если есть связь в БД)

        # Удалим сообщение с кнопками у админа (или просто отредактируем)
        bot.delete_message(chat_id, message_id)

        # Ответим админу, что заявка отговорена
        bot.answer_callback_query(call.id, text="Заявка отговорена и удалена.")

        # Можно оповестить пользователя
        bot.send_message(int(user_telegram_id_str),
                         "Рад, что вы остались с нами. Надеюсь дальше всё будет хорошо😉 ")
    except Exception as e:
        bot.answer_callback_query(call.id, text=f"Ошибка: {e}")


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
                    WHERE service = ? AND user_id = ? AND date = ? AND time = ?
                '''
                params = (service, telegram_id, date_str, time_str)
                print(params)
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
            OFFICE_ADDRESS = "г. Тольятти, ул. Южное шоссе, 35А"
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


@bot.callback_query_handler(func=lambda call: call.data.startswith("show_documents_"))
def show_documents(call):
    try:
        telegram_id = int(call.data.split("_")[-1])

        with db_lock:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT driver_license_photo, passport_front_photo, passport_back_photo 
                FROM users WHERE telegram_id = ?
            """, (telegram_id,))
            row = cur.fetchone()
            conn.close()

        if not row:
            bot.answer_callback_query(call.id, "Документы не найдены.")
            return

        doc1, doc2, doc3 = row

        if not any([doc1, doc2, doc3]):
            bot.answer_callback_query(call.id, "Пользователь не загрузил документы.")
            return

        chat_id = call.message.chat.id
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("❌ Скрыть", callback_data="hide_documents"))

        # Отправляем доступные документы
        if doc1:
            bot.send_photo(chat_id, doc1, caption="📘 Водительское удостоверение", reply_markup=markup)

        if doc2:
            bot.send_photo(chat_id, doc2, caption="📕 Паспорт (лицевая сторона)", reply_markup=markup)

        if doc3:
            bot.send_photo(chat_id, doc3, caption="📙 Паспорт (обратная сторона)", reply_markup=markup)

        bot.answer_callback_query(call.id)

    except Exception as e:
        bot.answer_callback_query(call.id, f"Ошибка: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "hide_documents")
def hide_documents(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Ошибка удаления документа: {e}")


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
    try:
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
    except Exception as e:
        print(f"Ошибка 6708: {e}")


@bot.message_handler(func=lambda message: message.text and message.chat.id in selected_suggest)
def handle_suggest_date_choice(message):
    try:
        chat_id = message.chat.id
        if chat_id not in selected_suggest:
            bot.send_message(chat_id,
                             "⚠️ Невозможно обработать дату: отсутствуют данные по выбору авто. Пожалуйста, начните заново.")
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

        bot.send_message(chat_id, f"📅 Дата выбрана: {text}. Теперь выберите время:",
                         reply_markup=types.ReplyKeyboardRemove())
        show_time_selection(message, car_id, user_id, date_str)
    except Exception as e:
        print(f"Ошибка 6748: {e}")


def show_time_selection(message, car_id, user_id, date_str):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT time FROM bookings WHERE car_id=? AND date=? AND status='confirmed'", (car_id, date_str))
        booked_times = [row[0] for row in c.fetchall()]
        conn.close()

        keyboard = types.InlineKeyboardMarkup(row_width=3)
        for hour in range(10, 19):
            for minute in range(0, 60, 30):  # каждые 10 минут
                time_str = f"{hour:02}:{minute:02}"
                if time_str in booked_times:
                    btn = types.InlineKeyboardButton(f"⛔ {time_str}", callback_data="busy")
                else:
                    btn = types.InlineKeyboardButton(time_str,
                                                     callback_data=f"suggest_time_{car_id}_{user_id}_{date_str}_{time_str}")
                keyboard.add(btn)

        bot.send_message(message.chat.id, f"Выберите время для {date_str}:", reply_markup=keyboard)
    except Exception as e:
        print(f"Ошибка 6772: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("suggest_time_"))
def process_admin_time_selection(call):


    try:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

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

        conn = sqlite3.connect(DB_PATH)
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
        c.execute("SELECT id FROM users WHERE telegram_id = ?", (user_id,))
        result = c.fetchone()
        if not result:
            bot.send_message(call.message.chat.id, "❌ Не найден telegram_id для пользователя.")
            conn.close()
            return

        telegram_id = result[0]

        # Записываем предложенное время
        session = get_session(user_id)
        service = session.get("selected_service")
        if not service:
            bot.send_message(call.message.chat.id, "❌ Ошибка: не удалось определить тип услуги.")
            return  # Можно сделать динамическим при необходимости
        c.execute('''
            INSERT INTO bookings (user_id, car_id, service, date, time, status)
            VALUES (?, ?, ?, ?, ?, 'suggested')
        ''', (user_id, car_id, service, date_str, time_str))
        conn.commit()
        conn.close()

        # Кнопка OK для клиента
        if service != "return":
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("OK",
                                                  callback_data=f"ok_{service}_{car_id}_{user_id}_{date_str}_{time_str}"))

            bot.send_message(telegram_id,
                             f"📩 Администратор предлагает: {date_str} в {time_str}\nЕсли согласны, нажмите кнопку ниже.",
                             reply_markup=markup)
            bot.send_message(call.message.chat.id, "✅ Предложение отправлено клиенту.")
        else:
            # Вызываем функцию chooseplace, например передав call
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("продолжить",
                                                  callback_data=f"chooseplace_{service}_{car_id}_{telegram_id}_{user_id}_{date_str}_{time_str}"))
            bot.send_message(ADMIN_ID2,
                             f"выберите место",
                             reply_markup=markup)
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
        print(car_id_raw)
        car_id = int(car_id_raw) if car_id_raw != "None" else 0
        user_id = int(parts[2])  # Добавлено, чтобы отправлять сообщение в Telegram

        date_str = parts[3]
        time_str = parts[4]

        with db_lock:
            conn = get_db_connection()
            cur = conn.cursor()

            # Обновляем статус машины

            # Получаем telegram_id по user_id
            cur.execute("SELECT telegram_id FROM users WHERE telegram_id = ?", (user_id,))
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
                        WHERE service = ? AND user_id = ? AND date = ? AND time = ?
                    '''
                params = (service, telegram_id, date_str, time_str)
                print(params)
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
        print(f"❌ Ошибка в process_ok: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("paid_delivery_"))
def handle_paid_delivery(call):
    try:
        user_id = int(call.data.split("_")[-1])

        bot.send_message(call.message.chat.id, "✅ Спасибо! Я проверю оплату и напишу вам.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception as e:
        print(f"Ошибка 6973: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_") and call.data.count("_") == 2)
def start_reject_decision(call):
    try:
        parts = call.data.split("_")
        _, car_id_str, telegram_id_str = parts

        car_id = int(car_id_str)
        telegram_id = int(telegram_id_str)
        admin_id = call.from_user.id

        # Убираем кнопки с исходного сообщения
        try:
            bot.edit_message_reply_markup(chat_id=telegram_id, message_id=call.message.message_id, reply_markup=None)
        except Exception as e:
            print(f"Ошибка при удалении кнопок: {e}")

        # Сохраняем данные
        global reject_buffer
        if "reject_buffer" not in globals():
            reject_buffer = {}

        reject_buffer[admin_id] = {
            "car_id": car_id,
            "telegram_id": telegram_id,
            "message_chat_id": call.message.chat.id,
            "message_id": call.message.message_id
        }

        # Вопрос админу
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Да, документы в порядке", callback_data=f"reject_docs_ok_{admin_id}"),
            types.InlineKeyboardButton("❌ Нет, документы не подходят", callback_data=f"reject_docs_bad_{admin_id}")
        )

        bot.send_message(admin_id, "📄 Документы клиента в порядке?", reply_markup=markup)
        bot.answer_callback_query(call.id)

    except Exception as e:
        bot.answer_callback_query(call.id, "Ошибка при начале отказа.")
        print(f"[ERROR in start_reject_decision]: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_docs_ok_"))
def ask_reject_reason(call):
    try:
        admin_id = int(call.data.split("_")[-1])

        if admin_id not in reject_buffer:
            bot.send_message(admin_id, "⚠️ Нет активного отказа.")
            return

        bot.send_message(admin_id, "✏️ Напишите причину отказа:")
        bot.answer_callback_query(call.id)
        try:
            bot.delete_message(chat_id=admin_id, message_id=call.message.message_id)
        except Exception as e:
            print(f"Ошибка при удалении исходного сообщения клиента: {e}")
    except Exception as e:
        print(f"Ошибка 7035: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_docs_bad_"))
def reject_due_to_documents(call):
    try:
        admin_id = int(call.data.split("_")[-1])
        data = reject_buffer.get(admin_id)
        if not data:
            bot.send_message(admin_id, "⚠️ Данные не найдены.")
            return

        telegram_id = data["telegram_id"]

        conn = get_db_connection()
        cursor = conn.cursor()

        # Удаляем фото
        cursor.execute("""
            UPDATE users
            SET driver_license_photo = NULL,
                passport_front_photo = NULL,
                passport_back_photo = NULL
            WHERE telegram_id = ?
        """, (telegram_id,))

        conn.commit()
        conn.close()

        bot.send_message(admin_id, "📁 Документы клиента удалены.")
        bot.send_message(admin_id, "✏️ Теперь напишите причину отказа:")

        bot.answer_callback_query(call.id)
        try:
            bot.delete_message(chat_id=admin_id, message_id=call.message.message_id)
        except Exception as e:
            print(f"Ошибка при удалении исходного сообщения клиента: {e}")
    except Exception as e:
        bot.send_message(call.from_user.id, "❌ Ошибка при удалении документов.")
        print(f"[ERROR in reject_due_to_documents]: {e}")


@bot.message_handler(func=lambda message: message.from_user.id in globals().get("reject_buffer", {}))
def handle_reject_reason(message):
    try:
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
        print(car_id, telegram_id, chat_id, msg_id)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 1. Сделать машину снова доступной (если car_id > 0)
            if car_id and car_id > 0:
                cursor.execute("UPDATE cars SET is_available = 1 WHERE car_id = ?", (car_id,))

            # 2. Удалить заявку по telegram_id и car_id
            cursor.execute("""
                    DELETE FROM bookings
                    WHERE user_id = ? AND (car_id = ? OR ? = 0)
                """, (telegram_id, car_id, car_id))

            if car_id is not None:
                cursor.execute("""
                        DELETE FROM rental_history
                        WHERE user_id = ? AND car_id = ? AND status = 'confirmed'
                    """, (telegram_id, car_id))
                print(
                    f"[cancel_expired_bookings] 📄 rental_history удалена для user_id={telegram_id}, car_id={car_id}, status='confirmed'")

            conn.commit()
            conn.close()

            # 3. Уведомляем клиента
            bot.send_message(telegram_id, f"❌ Ваша заявка отклонена.\nПричина: {reason}")

            # 4. Удаляем inline-кнопки
            try:
                bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None)
            except telebot.apihelper.ApiTelegramException as e:
                if "message is not modified" in str(e):
                    pass  # кнопки уже удалены — ничего не делаем
                else:
                    raise e  # пробрасываем остальные ошибки

            # 5. Подтверждаем админу
            bot.send_message(admin_id, "✅ Причина отправлена и заявка удалена.")

            # 6. Очистить состояние (если используешь FSM)
            clear_state(admin_id)

        except Exception as e:
            bot.send_message(admin_id, "❌ Ошибка при обработке отказа.")
            print(f"[ERROR in handle_reject_reason]: {e}")
    except Exception as e:
        print(f"Ошибка 7140: {e}")


@bot.message_handler(commands=['list_users'])
def list_all_users(message):
    try:
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
    except Exception as e:
        print(f"Ошибка 7169: {e}")



def translate_status(status):
    try:
        return {
            'confirmed': '✅ Подтверждена',
            'pending': '⏳ В ожидании',
            'reject': '❌ Отклонена'
        }.get(status, '❔ Неизвестно')


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
    except Exception as e:
        print(f"Ошибка 7204: {e}")


@bot.message_handler(commands=['delete_user'])
def delete_user_handler(message):
    try:
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
    except Exception as e:
        print(f"Ошибка 7224: {e}")


def delete_user_from_db(phone_number):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE phone = ?", (phone_number,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка 7235: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "admin_avtopark")
def admin_view_all_cars(call):
    try:
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        if user_id not in ADMIN_IDS:
            bot.send_message(chat_id, "❌ У вас нет доступа к этой команде.")
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
                SELECT car_id, brand_model, year, number, is_available, price, station, service, is_broken, fix_date
                FROM cars
            """)
        cars = cursor.fetchall()
        conn.close()

        if not cars:
            bot.send_message(chat_id, "🚫 В базе данных нет машин.")
            return

        for car_id, brand_model, year, number, is_available, price, station, service, is_broken, fix_date in cars:
            status = "🟢 Свободна" if is_available else "🔴 Занята"
            service_label = {
                "rent": "Аренда",
                "rental": "Прокат",
                "gazel": "Газель"
            }.get(service, service)

            broken_text = "❌ Сломана" if is_broken else "✅ Исправна"
            fix_date_str = f"\n🛠 Починка: {fix_date}" if fix_date else ""

            # Перевод станции
            station_name = STATION_NAMES.get(station, station)

            text = (
                f"<b>№{car_id}</b>\n"
                f"<b>{brand_model}</b> ({year})\n"
                f"Номер: {number}\n"
                f"Статус: {status}\n"
                f"{broken_text}{fix_date_str}\n"
                f"Цена: {price}₽\n"
                f"Станция: {station_name}\n"
                f"Услуга: {service_label}"
            )

            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("🗑 Удалить", callback_data=f"deletecar_{car_id}"),
                types.InlineKeyboardButton(
                    "🔓 Сделать доступной" if not is_available else "🔒 Сделать недоступной",
                    callback_data=f"togglecar_{car_id}_{int(not is_available)}"
                ),
                types.InlineKeyboardButton("💸 Сменить цену", callback_data=f"changeprice_{brand_model}_{year}_{service}")
            )
            markup.add(
                types.InlineKeyboardButton("🛠 Изменить станцию", callback_data=f"editstation_{car_id}"),
                types.InlineKeyboardButton(
                    "🔧 Статус: Сломана" if is_broken else "✅ Статус: Исправна",
                    callback_data=f"togglebroken_{car_id}_{int(not is_broken)}"
                )
            )

            bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

        # Кнопка обновления
        refresh_markup = types.InlineKeyboardMarkup()
        refresh_markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="refresh_admin_cars"))
        bot.send_message(chat_id, "📋 Нажмите, чтобы обновить список машин", reply_markup=refresh_markup)
    except Exception as e:
        print(f"Ошибка 7310: {e}")



@bot.callback_query_handler(func=lambda call: call.data.startswith("deletecar_"))
def delete_car_handler(call):
    try:
        car_id = int(call.data.split("_")[1])

        # Удаляем машину из БД
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cars WHERE car_id = ?", (car_id,))
        conn.commit()
        conn.close()

        # Уведомляем пользователя
        bot.answer_callback_query(call.id, "🚗 Машина удалена")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="✅ Машина успешно удалена."
        )

    except Exception as e:
        print(f"❌ Ошибка при удалении машины: {e}")
        bot.answer_callback_query(call.id, "⚠ Ошибка при удалении")


@bot.callback_query_handler(func=lambda call: call.data.startswith("togglebroken_"))
def toggle_car_broken_status(call):
    try:
        _, car_id, new_status = call.data.split("_")
        car_id = int(car_id)
        new_status = int(new_status)

        if new_status == 1:
            # Сломана — запрашиваем дату ремонта
            msg = bot.send_message(call.message.chat.id,
                                   "📆 Укажите дату починки авто в формате <b>ДД.ММ.ГГГГ</b>:",
                                   parse_mode="HTML")
            bot.register_next_step_handler(msg, save_broken_status_with_date, car_id)
        else:
            # Исправна — просто сбрасываем
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE cars SET is_broken = 0 AND is_available = 0, fix_date = NULL WHERE car_id = ?",
                               (car_id,))
                conn.commit()
            bot.answer_callback_query(call.id, "✅ Машина теперь отмечена как исправная.")
            # admin_view_all_cars(call.message, user_id=call.from_user.id)

    except Exception as e:
        print(f"Ошибка 7363: {e}")

def save_broken_status_with_date(message, car_id):
    try:
        date_text = message.text.strip().lower()

        # ✅ Возможность выйти из шага
        if date_text in ["отмена", "выход", "стоп"]:
            bot.send_message(message.chat.id, "❌ Действие отменено. Вы вышли из режима ввода даты.")
            return

        try:
            parsed_date = datetime.strptime(date_text, "%d.%m.%Y").date()
        except ValueError:
            msg = bot.send_message(
                message.chat.id,
                "❌ Неверный формат. Введите дату как <b>ДД.ММ.ГГГГ</b> или напишите <b>отмена</b> для выхода:",
                parse_mode="HTML"
            )
            bot.register_next_step_handler(msg, save_broken_status_with_date, car_id)
            return

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE cars SET is_broken = 1, fix_date = ? WHERE car_id = ?
            """, (parsed_date.strftime("%Y-%m-%d"), car_id))
            conn.commit()

        bot.send_message(
            message.chat.id,
            f"✅ Машина отмечена как сломанная до {parsed_date.strftime('%d.%m.%Y')}"
        )

    except Exception as e:
        print(f"Ошибка 7386: {e}")


# ✅ Обработка запроса на ввод даты ремонта
@bot.callback_query_handler(func=lambda call: call.data.startswith("editfixdate_"))
def ask_fix_date(call):
    try:
        car_id = int(call.data.split("_")[1])
        msg = bot.send_message(call.message.chat.id,
                               "📅 Введите дату ремонта в формате <b>ДД.ММ.ГГГГ</b>:",
                               parse_mode="HTML")
        bot.register_next_step_handler(msg, save_fix_date, car_id)
    except Exception as e:
        print(f"Ошибка 7399: {e}")


# ✅ Сохранение fix_date
def save_fix_date(message, car_id):
    try:
        date_text = message.text.strip()
        try:
            parsed_date = datetime.strptime(date_text, "%d.%m.%Y").date()
        except ValueError:
            msg = bot.send_message(message.chat.id, "❌ Неверный формат даты. Попробуйте снова (ДД.ММ.ГГГГ):")
            bot.register_next_step_handler(msg, save_fix_date, car_id)
            return

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE cars SET fix_date = ? AND is_available = 0 WHERE car_id = ?",
                           (parsed_date.strftime("%Y-%m-%d"), car_id))
            conn.commit()

        bot.send_message(message.chat.id, f"✅ Дата ремонта сохранена: {parsed_date.strftime('%d.%m.%Y')}")
    except Exception as e:
        print(f"Ошибка 7421: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("editstation_"))
def handle_edit_station(call):
    try:
        car_id = call.data.split("_")[1]
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Южное шоссе 129", callback_data=f"stationset_{car_id}_Южное шоссе 129"),
            types.InlineKeyboardButton("Южное шоссе 12/2", callback_data=f"stationset_{car_id}_Южное шоссе 12/2"),
            types.InlineKeyboardButton("Лесная 66А", callback_data=f"stationset_{car_id}_Лесная 66А"),
            types.InlineKeyboardButton("Борковская 72/1", callback_data=f"stationset_{car_id}_Борковская 72/1"),
        )
        bot.edit_message_text(
            "🏁 Выберите новую станцию:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )
    except Exception as e:
        print(f"Ошибка 7442: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("stationset_"))
def handle_station_set(call):
    try:
        _, car_id, new_station = call.data.split("_", 2)

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE cars SET station = ? WHERE car_id = ?", (new_station, car_id))
            conn.commit()

        bot.edit_message_text(
            f"✅ Станция успешно обновлена на: <b>{new_station}</b>",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка 7462: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "refresh_admin_cars")
def refresh_admin_cars(call):
    try:
        admin_view_all_cars(call)
        bot.answer_callback_query(call.id, "🔄 Список обновлён")
    except Exception as e:
        print(f"Ошибка 7471: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("deletecar_"))
def delete_car(call):
    car_id = call.data.split("_")[1]

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Удаляем связанные записи в зависимых таблицах
        cursor.execute("DELETE FROM bookings WHERE car_id = ?", (car_id,))
        cursor.execute("DELETE FROM rental_history WHERE car_id = ?", (car_id,))

        # Теперь можно удалить саму машину
        cursor.execute("DELETE FROM cars WHERE car_id = ?", (car_id,))
        conn.commit()

        bot.edit_message_text("🗑 Машина удалена.", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Машина успешно удалена.")
    except sqlite3.IntegrityError as e:
        bot.answer_callback_query(call.id, f"Ошибка при удалении: {e}")
    finally:
        conn.close()


@bot.callback_query_handler(func=lambda call: call.data.startswith("togglecar_"))
def toggle_car_availability(call):
    try:
        parts = call.data.split("_")
        car_id = parts[1]
        new_status = int(parts[2])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE cars SET is_available = ? WHERE car_id = ?", (new_status, car_id))
        conn.commit()
        conn.close()

        status_msg = "Теперь машина доступна ✅" if new_status else "Теперь машина недоступна ❌"
        bot.edit_message_text(status_msg, call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Ошибка 7515: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("changeprice_"))
def change_price_prompt(call):
    try:
        _, brand_model, year, service = call.data.split("_")
        user_id = call.from_user.id

        session = get_session(user_id)
        session["change_price_target"] = (brand_model, year, service)

        # Словарь перевода сервиса
        service_display = {
            "rent": "аренда",
            "rental": "прокат",
            "gazel": "газель"
        }.get(service, service)

        bot.send_message(
            call.message.chat.id,
            f"Введите новую цену для всех <b>{brand_model}</b> ({year}), услуга: <b>{service_display}</b>",
            parse_mode="HTML"
        )
        set_state(user_id, "awaiting_new_price")
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Ошибка 7542: {e}")


@bot.message_handler(func=lambda m: get_state(m.chat.id) == "awaiting_new_price")
def apply_new_price(message):
    try:
        if message.text.startswith("/"):
            return

        session = get_session(message.chat.id)

        try:
            new_price = int(message.text.strip())
        except ValueError:
            bot.send_message(message.chat.id, "Введите корректное число.")
            return

        brand_model, year, service = session.get("change_price_target", (None, None, None))
        if not brand_model or not year or not service:
            bot.send_message(message.chat.id, "⚠️ Ошибка. Данные не найдены.")
            # сбрасываем состояние, чтобы не застрять
            session["state"] = None
            return

        # Словарь для отображения сервиса на русском
        service_display = {
            "rent": "аренда",
            "rental": "прокат",
            "gazel": "газель"
        }.get(service, service)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE cars SET price = ?
            WHERE brand_model = ? AND year = ? AND service = ?
        """, (new_price, brand_model, year, service))
        conn.commit()
        conn.close()

        bot.send_message(
            message.chat.id,
            f"✅ Цена обновлена: <b>{new_price}₽</b>\n"
            f"Модель: <b>{brand_model}</b>, Год: <b>{year}</b>, Услуга: <b>{service_display}</b>",
            parse_mode="HTML"
        )

        # аккуратно очищаем только state и таргет
        session["state"] = None
        session.pop("change_price_target", None)
    except Exception as e:
        print(f"Ошибка 7593: {e}")
    # если юзер прислал команду — отдадим её другим хендлерам


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


# @bot.callback_query_handler(func=lambda call: call.data == "rent")
# def handle_rent(call):
#     bot.answer_callback_query(call.id)
#     markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
#     markup.add("🚗 Смотреть машины", "❓ Вопросы")
#     bot.send_message(call.message.chat.id,
#                              f"Хорошо а теперь выберите то что вас интересует",
#                              reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "rent")
def handle_show_cars(call):
    try:
        choose_service_type(call.message)
    except Exception as e:
        print(f"Ошибка 7632: {e}")


@bot.message_handler(func=lambda message: message.text == "❓ Вопросы")
def handle_show_questions(message):
    # Вызов команды вопросов
    try:

        handle_ask_command(message)
    except Exception as e:
        print(f"Ошибка 7642: {e}")

@bot.message_handler(commands=['add_user'])
def admin_add_user(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "⛔ У тебя нет прав для этого!")
        return
    try:

        bot.send_message(message.chat.id, "Введите номер телефона нового пользователя:")
        set_state(message.chat.id, "waiting_for_new_user")
    except Exception as e:
        print(f"Ошибка 7654: {e}")

@bot.message_handler(func=lambda m: get_state(m.chat.id) == "waiting_for_new_user")
def handle_new_user(message):
    try:

        add_user_to_db(message.text.strip())
        bot.send_message(message.chat.id, "✅ Пользователь добавлен.")
        set_state(message.chat.id, None)
    except Exception as e:
        print(f"Ошибка 7664: {e}")

@bot.message_handler(commands=['add_car'])
def admin_add_car(message):
    if message.from_user.id not in ADMIN_ID:
        bot.reply_to(message, "⛔ У тебя нет прав для этого!")
        return
    try:

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Фольцваген Поло", "Шкода Рапид", "Рено Логан", "Шкода Октавия", "Джили Эмгранд")
        bot.send_message(message.chat.id, "Выберите модель автомобиля:", reply_markup=markup)
        set_state(message.chat.id, "admin_add_car_model")
    except Exception as e:
        print(f"Ошибка 7678: {e}")

@bot.message_handler(func=lambda m: get_state(m.chat.id) == "admin_add_car_model")
def admin_add_car_model(message):
    try:
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
    except Exception as e:
        print(f"Ошибка 7707: {e}")


@bot.message_handler(func=lambda m: get_state(m.chat.id) == "admin_add_car_year")
def admin_add_car_year(message):
    try:
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

    except Exception as e:
        print(f"Ошибка 7740: {e}")

@bot.message_handler(func=lambda m: get_state(m.chat.id) == "admin_add_car_transmission")
def admin_add_car_transmission(message):
    try:
        session = get_session(message.chat.id)
        session["transmission"] = message.text.strip()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("аренда", "прокат")
        bot.send_message(message.chat.id, "Выберите тип обслуживания:", reply_markup=markup)
        set_state(message.chat.id, "admin_add_car_service")
    except Exception as e:
        print(f"Ошибка 7753: {e}")


@bot.message_handler(func=lambda m: get_state(m.chat.id) == "admin_add_car_service")
def admin_add_car_service(message):
    try:
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
    except Exception as e:
        print(f"Ошибка 7778: {e}")


@bot.message_handler(func=lambda m: get_state(m.chat.id) == "admin_add_car_id")
def admin_add_car_id(message):
    try:
        session = get_session(message.chat.id)
        car_id = message.text.strip().upper()

        if not car_id or len(car_id) < 5:
            bot.send_message(message.chat.id, "❌ Введите корректный номер автомобиля.")
            return

        # Сохраняем car_id в сессию
        session["number"] = car_id

        bot.send_message(message.chat.id, "Выберите станцию для автомобиля:", reply_markup=generate_station_keyboard())
        set_state(message.chat.id, "admin_add_car_station")
    except Exception as e:
        print(f"Ошибка 7797: {e}")


@bot.message_handler(func=lambda m: get_state(m.chat.id) == "admin_add_car_station")
def admin_add_car_station(message):
    try:
        session = get_session(message.chat.id)
        station = message.text.strip()

        valid_stations = [
            "Южное шоссе 129",
            "Южное шоссе 12/2",
            "Лесная 66А",
            "Борковская 72/1"
        ]

        if station not in valid_stations:
            bot.send_message(message.chat.id, "❌ Пожалуйста, выберите станцию из предложенных кнопок.")
            return

        session["station"] = station
        bot.send_message(message.chat.id, "Отправьте фото машины:")
        set_state(message.chat.id, "admin_add_car_photo")
    except Exception as e:
        print(f"Ошибка 7821: {e}")


@bot.message_handler(func=lambda m: get_state(m.chat.id) == "admin_add_car_photo", content_types=['photo'])
def admin_add_car_photo(message):
    try:
        session = get_session(message.chat.id)
        photo_id = message.photo[-1].file_id
        session["photo"] = photo_id
        # Сохраняем в БД
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
                INSERT INTO cars (number, brand_model, year, transmission, photo_url, service, station)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
            session.get("number"),
            session.get("model"),
            session.get("year"),
            session.get("transmission"),
            photo_id,
            session.get("service"),
            session.get("station")
        ))
        conn.commit()
        conn.close()

        # Подтверждение
        text = (
            f"<b>Номер:</b> {session.get('number')}\n"
            f"<b>Модель:</b> {session.get('model')}\n"
            f"<b>Год:</b> {session.get('year')}\n"
            f"<b>Коробка:</b> {session.get('transmission')}\n"
            f"<b>Тип услуги:</b> {session.get('service')}\n"
            f"<b>Станция:</b> {session.get('station')}"
        )
        bot.send_message(message.chat.id, f"✅ Машина добавлена:\n\n{text}", parse_mode="HTML")
        bot.send_photo(message.chat.id, photo_id)

        # Очистка
        user_sessions.pop(message.chat.id, None)
    except Exception as e:
        print(f"Ошибка 7863: {e}")


def generate_station_keyboard():
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        stations = [
            "Южное шоссе 129",
            "Южное шоссе 12/2",
            "Лесная 66А",
            "Борковская 72/1"
        ]
        for s in stations:
            markup.add(s)
        return markup

    except Exception as e:
        print(f"Ошибка 7880: {e}")

@bot.message_handler(commands=['available_cars'])
def choose_service_type(message):
    try:
        user_id = message.from_user.id
        session = get_session(user_id)
        # Сброс выбранных ранее данных
        session.pop("selected_service", None)
        session.pop("car_purpose", None)

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("👤 Для личного пользования", callback_data="target_personal"),
            types.InlineKeyboardButton("🚖 Для работы в такси", callback_data="target_taxi")
        )
        bot.send_message(message.chat.id, "Для чего вам автомобиль?", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка 7898: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("target_"))
def handle_purpose_selection(call):
    try:
        user_id = call.from_user.id
        session = get_session(user_id)

        purpose_key = call.data.split("_")[1]  # personal или taxi
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
                UPDATE users
                SET purpose = ?
                WHERE telegram_id = ?
            ''', (purpose_key, user_id))
        conn.commit()

        # Ответ пользователю
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "Выберите тип услуги:",
            reply_markup=get_service_type_markup()
        )
    except Exception as e:
        print(f"Ошибка 7926: {e}")


def get_service_type_markup():
    try:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🚗 Долгосрочная аренда", callback_data="service_rent"))

        markup.add(
            types.InlineKeyboardButton("🏁 Посуточная аренда", callback_data="service_rental")
        )
        return markup
    except Exception as e:
        print(f"Ошибка 7940: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("service_"))
def show_available_cars(call):
    try:
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
                SELECT MIN(car_id), brand_model, year
                FROM cars
                WHERE is_available = 1 AND LOWER(service) = ?
                GROUP BY brand_model, year
                ORDER BY MIN(price) ASC
            """, (service_key,))
        cars = cursor.fetchall()
        conn.close()

        if not cars:
            bot.send_message(chat_id, "🚫 Нет доступных машин для выбранной услуги.")
            bot.answer_callback_query(call.id)
            return

        # Показ фильтра если машин больше 5
        service_titles = {
            "rent": "долгосрочной аренды",
            "rental": "посуточной аренды"
        }

        service_name = service_titles.get(service_key, service_key.upper())  # на случай, если ключ не в словаре

        # if len(cars) > 5:
        #     filter_markup = types.InlineKeyboardMarkup()
        #     filter_markup.add(types.InlineKeyboardButton("🔎 Фильтр", callback_data="start_filter"))
        #     bot.send_message(chat_id, f"📋 Машины для: {service_name}", reply_markup=filter_markup)
        # else:
        bot.send_message(chat_id, f"📋 Машины для: {service_name}")

        session["car_message_ids"] = []

        for car_id, brand_model, year in cars:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT photo_url, price, transmission FROM cars WHERE car_id = ?", (car_id,))
            photo_url, price, transmission = cursor.fetchone()
            conn.close()

            caption = f"<b>{brand_model}</b> ({year})\n Коробка: {transmission}\n💰 {price}₽/день"

            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🚗 Выбрать", callback_data=f"choose_{car_id}"))

            if service_key == "rental":
                markup.add(types.InlineKeyboardButton("📅 Рассчитать цену", callback_data=f"price_{car_id}"))

            sent_msg = bot.send_photo(chat_id, photo=photo_url, caption=caption, parse_mode="HTML", reply_markup=markup)
            session["car_message_ids"].append(sent_msg.message_id)

        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Ошибка 8014: {e}")




@bot.callback_query_handler(func=lambda call: call.data.startswith(("details_", "choose_", "hide_", "price_")))
def handle_inline(call):
    try:
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
            cursor.execute("""
                    SELECT brand_model, year, service, price 
                    FROM cars 
                    WHERE car_id = ?
                """, (car_id,))
            car = cursor.fetchone()
            conn.close()

            if not car:
                bot.send_message(chat_id, "🚫 Машина не найдена.")
                return

            brand_model, year, service, price = car

            if service == "rent":
                if price:
                    bot.send_message(chat_id, f"💰 Цена за сутки аренды {brand_model} ({year}): <b>{price}₽</b>",
                                     parse_mode="HTML")
                else:
                    bot.send_message(chat_id, f"❌ Цена аренды для {brand_model} ({year}) не указана.")

            elif service == "rental":
                session["awaiting_days_for_car"] = car_id
                bot.send_message(chat_id, f"📅 На сколько дней хотите взять {brand_model}?")

            else:
                bot.send_message(chat_id, "❌ Тип услуги не распознан.")
            return

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

            telegram_id = call.from_user.id

            user_id = telegram_id

            chat_id = call.message.chat.id
            try:
                bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)
            except Exception as e:
                print(f"Ошибка при удалении кнопок: {e}")
            # Проверка: есть ли уже аренда и документы

            with sqlite3.connect("cars.db") as conn:

                cursor = conn.cursor()

                cursor.execute(

                    "SELECT status, driver_license_photo, passport_front_photo, passport_back_photo FROM users WHERE telegram_id = ?",

                    (telegram_id,)

                )

                row = cursor.fetchone()

            if not row:
                bot.send_message(chat_id, "❌ Пользователь не найден.")

                return

            status, dl_photo, pass_front, pass_back = row

            if status != "new":
                bot.send_message(chat_id, "🚫 У вас уже есть арендованная машина. Сначала завершите текущую аренду.")

                return

            session["car_id"] = car_id

            # Разветвление по типу услуги

            service = session.get("selected_service")

            print(service)

            # Удаляем старые карточки машин

            current_msg_id = call.message.message_id

            for msg_id in session.get("car_message_ids", []):

                if msg_id != current_msg_id:

                    try:

                        bot.delete_message(chat_id, msg_id)

                    except Exception as e:

                        print(f"Ошибка удаления карточки: {e}")

            session.pop("car_message_ids", None)
            if service == "rental":
                session["selected_car_id"] = car_id
                session["state"] = "waiting_for_rental_start"

                bot.send_message(
                    chat_id,
                    "Теперь выберите дату для бронирования:",
                    reply_markup=create_calendar_markup(car_id)  # ← передаём car_id
                )
                return
            # Получаем марку и год, затем станции

            with sqlite3.connect(DB_PATH) as conn:

                cursor = conn.cursor()

                cursor.execute("SELECT brand_model, year FROM cars WHERE car_id = ?", (car_id,))

                car = cursor.fetchone()

                if not car:
                    bot.send_message(chat_id, "❌ Машина не найдена.")

                    return

                brand_model, year = car

                cursor.execute("""

                        SELECT DISTINCT station FROM cars

                        WHERE brand_model = ? AND year = ? AND is_available = 1

                    """, (brand_model, year))

                stations = [row[0] for row in cursor.fetchall() if row[0]]

            markup = types.InlineKeyboardMarkup()

            for station in stations:
                markup.add(types.InlineKeyboardButton(text=station, callback_data=f"carstation_{station}"))

            bot.send_message(chat_id, "📍 Выберите станцию, с которой хотите забрать машину:", reply_markup=markup)


        else:

            bot.send_message(chat_id, "⚠️ У этой машины не указана станция.")

    except Exception as e:
        print(f"Ошибка 8210: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("carstation_"))
def handle_station_choice(call):
    try:
        user_id = call.from_user.id
        print(user_id)
        chat_id = call.message.chat.id
        session = get_session(user_id)
        service = session.get("selected_service")
        station = call.data.replace("carstation_", "")
        if service == 'rental':
            price = session.get("price")
            rent_start = session.get("rent_start")
            rent_end = session.get("rent_end")
            db_user_id = session.get("db_user_id")
            print(rent_start, rent_end)
            if not all([price, rent_start, rent_end, db_user_id]):
                missing = []
                if not price: missing.append("price")
                if not rent_start: missing.append("rent_start")
                if not rent_end: missing.append("rent_end")
                if not db_user_id: missing.append("db_user_id")
                bot.send_message(chat_id, f"❌ Ошибка: отсутствуют данные: {', '.join(missing)}")
                return
            free_car_ids = session.get("free_car_ids", {})
            if station not in free_car_ids:
                bot.send_message(chat_id, "❌ Ошибка: станция не найдена или машина уже недоступна.")
                return

            selected_car_id = free_car_ids[station]
            print(selected_car_id)
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                print(selected_car_id)
                start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('''
                            INSERT INTO rental_history (user_id, car_id, rent_start, rent_end, price, end_time, start_time, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (user_id, selected_car_id, rent_start, rent_end, price, rent_end, start_time, 'confirmed'))
                conn.commit()
                print("✅ Данные вставлены в rental_history!")
        else:
            selected_car_id = session.get("car_id")
        session["car_id"] = selected_car_id
        session["selected_station"] = station
        for key in ["price", "rent_start_str", "rent_end_str", "db_user_id"]:
            session.pop(key, None)
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        except:
            pass

        bot.send_message(chat_id, f"✅ Вы выбрали станцию: {station}")

        # Тут проверка документов
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                    SELECT driver_license_photo, passport_front_photo, passport_back_photo
                    FROM users WHERE telegram_id = ?
                """, (user_id,))
            row = cursor.fetchone()

        if row and all(row):
            bot.send_message(chat_id, "✅ Документы уже есть. Переходим к оформлению.")
            post_photo_processing(user_id, chat_id, session)
        else:
            session["state"] = "waiting_for_photo"
            bot.send_message(chat_id, "📸 Пожалуйста, отправьте фотографию водительского удостоверения.")
    except Exception as e:
        print(f"Ошибка 8282: {e}")


@bot.message_handler(func=lambda message: get_session(message.from_user.id).get("awaiting_days_for_car"))
def handle_rental_days(message):
    try:
        user_id = message.from_user.id
        session = get_session(user_id)

        try:
            days = int(message.text)
            car_id = int(session["awaiting_days_for_car"])
            if days <= 0:
                raise ValueError
        except (ValueError, KeyError):
            bot.send_message(message.chat.id, "Введите корректное число дней, например: 3")
            return

        # Получаем модель авто и базовую цену
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT brand_model, price FROM cars WHERE car_id = ?", (car_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            bot.send_message(message.chat.id, "🚫 Машина не найдена.")
            return

        brand_model, base_price = row

        if not base_price:
            bot.send_message(message.chat.id, f"❌ Не указана цена для модели {brand_model}.")
            return

        # Применение скидки в зависимости от количества дней
        if 1 <= days <= 6:
            daily_price = base_price
        elif 7 <= days <= 13:
            daily_price = base_price - 100
        elif 14 <= days <= 20:
            daily_price = base_price - 200
        elif 21 <= days <= 27:
            daily_price = base_price - 300
        else:  # от 28 и выше
            daily_price = base_price - 400

        if daily_price < 0:
            daily_price = 0  # защита от отрицательных цен

        total = daily_price * days

        bot.send_message(
            message.chat.id,
            f"💰 Цена аренды <b>{brand_model}</b> на {days} дней:\n"
            f"{daily_price}₽/сутки × {days} = <b>{total}₽</b>",
            parse_mode="HTML"
        )

        # Очистка временных данных
        session.pop("awaiting_days_for_car", None)

    except Exception as e:
        print(f"Ошибка 8345: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("hide_"))
def hide_message(call):
    try:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        print(f"Ошибка удаления сообщения: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("rental_") or call.data.startswith("rent_"))
def handle_rental_and_rent(call):
    try:
        print(f"[DEBUG] callback received: {call.data}")
        action, car_id = call.data.split("_", 1)
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

    except Exception as e:
        print(f"Ошибка 8378: {e}")

def show_user_calendar(message, car_id, user_id):
    try:
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
    except Exception as e:
        print(f"Ошибка 8412: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("rental_days_"))
def rental_days_selected(call):
    try:
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

    except Exception as e:
        print(f"Ошибка 8460: {e}")

# ➤ Обработка ответа на вопрос "Нужна ли доставка?"
@bot.message_handler(func=lambda message: get_state(message.chat.id) == "waiting_for_delivery_choice")
def handle_final_confirmation(message):
    try:
        user_id = message.chat.id
        session = get_session(user_id)
        choice = message.text.strip().lower()

        # --- Убираем reply-клавиатуру ---
        bot.send_message(user_id, "Выбор завершён", reply_markup=types.ReplyKeyboardRemove())

        # --- Убираем inline-кнопки предыдущего сообщения ---
        last_inline_msg_id = session.get("last_inline_msg_id")
        if last_inline_msg_id:
            try:
                bot.edit_message_reply_markup(
                    chat_id=user_id,
                    message_id=last_inline_msg_id,
                    reply_markup=None
                )
            except telebot.apihelper.ApiTelegramException as e:
                print(f"Не удалось удалить inline-кнопки: {e}")
            session.pop("last_inline_msg_id", None)

        car_id = session.get("car_id") or session.get("selected_car_id")
        price = session.get("price")
        rent_start = session.get("rent_start")
        rent_end = session.get("rent_end")
        db_user_id = session.get("db_user_id")

        if choice == "да":
            if not all([car_id, price, rent_start, rent_end, db_user_id]):
                missing = [key for key in ["car_id", "price", "rent_start", "rent_end", "db_user_id"] if not session.get(key)]
                bot.send_message(user_id, f"❌ Ошибка: отсутствуют данные: {', '.join(missing)}")
                return

            # --- Проверяем, есть ли запись в rental_history ---
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM rental_history 
                WHERE user_id = ? AND car_id = ? AND status = 'confirmed'
                ORDER BY id DESC LIMIT 1
            """, (db_user_id, car_id))
            rh_row = cursor.fetchone()

            if rh_row:
                # --- Обновляем данные аренды ---
                cursor.execute("""
                    UPDATE rental_history
                    SET rent_start = ?, rent_end = ?, price = ?
                    WHERE id = ?
                """, (rent_start, rent_end, price, rh_row[0]))
                conn.commit()
                bot.send_message(user_id, f"✅ Срок аренды и цена успешно изменены.\n📅 {rent_start} — {rent_end}\n💰 {price} руб.")
                return
            conn.close()

            # --- Показываем кнопку "📍 Где забрать машину" ---
            markup = types.InlineKeyboardMarkup()
            pickup_btn = types.InlineKeyboardButton("📍 Где забрать авто", callback_data=f"pickup_station|{car_id}")
            markup.add(pickup_btn)

            session["selected_car_id"] = car_id
            session["service"] = "rental"
            set_state(user_id, "waiting_for_choose_station_pick")

            sent_msg = bot.send_message(user_id, "✅ Отлично! Остался последний шаг:", reply_markup=markup)
            session["last_inline_msg_id"] = sent_msg.message_id

        elif choice == "нет":
            set_state(user_id, "waiting_for_rental_start")
            bot.send_message(user_id, "Хорошо, давайте выберем дату начала заново.")
            bot.send_message(user_id, "📅 Укажите новую дату начала проката:", reply_markup=create_calendar_markup(car_id))
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add("Да", "Нет")
            bot.send_message(user_id, "Пожалуйста, выберите 'Да' или 'Нет'.", reply_markup=markup)

    except Exception as e:
        print(f"Ошибка handle_final_confirmation: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pickup_station|"))
def handle_pickup_station(call):
    try:
        import sqlite3

        car_id = int(call.data.split("|")[1])
        print(car_id)
        user_id = call.from_user.id
        print(user_id)
        chat_id = call.message.chat.id
        session = get_session(user_id)
        try:
            bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)
        except Exception as e:
            print(f"Ошибка при удалении кнопок: {e}")
        car_id = session.get("car_id")
        print(car_id)
        price = session.get("price")
        rent_start = session.get("rent_start")
        rent_end = session.get("rent_end")
        db_user_id = session.get("db_user_id")
        print(rent_start, rent_end)
        if not all([car_id, price, rent_start, rent_end, db_user_id]):
            missing = []
            if not car_id: missing.append("car_id")
            if not price: missing.append("price")
            if not rent_start: missing.append("rent_start")
            if not rent_end: missing.append("rent_end")
            if not db_user_id: missing.append("db_user_id")
            bot.send_message(chat_id, f"❌ Ошибка: отсутствуют данные: {', '.join(missing)}")
            return

        print(rent_start, rent_end)
        if not rent_start or not rent_end:
            bot.send_message(chat_id, "❌ Не выбраны даты аренды.")
            return

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Получаем brand_model и year для исходного car_id
            cursor.execute("SELECT brand_model, year FROM cars WHERE car_id = ?", (car_id,))
            car = cursor.fetchone()
            if not car:
                bot.send_message(chat_id, "❌ Машина не найдена.")
                return

            brand_model, year = car["brand_model"], car["year"]

            # Ищем все car_id с этим же brand_model и year, которые свободны на даты
            cursor.execute("""
                    SELECT car_id, station FROM cars
                    WHERE brand_model = ? AND year = ?
                """, (brand_model, year))
            all_cars = cursor.fetchall()

            free_cars = []
            for row in all_cars:
                cid = row["car_id"]
                cursor.execute("""
                        SELECT 1 FROM rental_history
                        WHERE car_id = ?
                        AND status = 'confirmed'
                        AND (
                            (? BETWEEN rent_start AND rent_end)
                            OR (? BETWEEN rent_start AND rent_end)
                            OR (rent_start BETWEEN ? AND ?)
                            OR (rent_end BETWEEN ? AND ?)
                        )
                    """, (
                    cid,
                    rent_start, rent_end,
                    rent_start, rent_end,
                    rent_start, rent_end
                ))
                if not cursor.fetchone():
                    free_cars.append((cid, row["station"]))

        if not free_cars:
            bot.send_message(chat_id, "🚫 Нет свободных машин этой модели и года на эти даты.")
            return

        # Сохраняем список свободных car_id в сессию
        session["free_car_ids"] = {station: cid for cid, station in free_cars}

        # Формируем кнопки станций
        markup = types.InlineKeyboardMarkup()
        for station in sorted(set(st for _, st in free_cars if st)):
            markup.add(types.InlineKeyboardButton(station, callback_data=f"carstation_{station}"))

        bot.send_message(chat_id, "📍 Выберите станцию:", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка 8621: {e}")


def create_time_markup_calendar(date_str, car_id):
    from telebot import types
    import sqlite3
    try:
        markup = types.InlineKeyboardMarkup(row_width=3)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT time FROM bookings WHERE date = ? AND car_id = ?", (date_str, car_id))
        booked = set(row[0][:5] for row in cursor.fetchall() if row[0])
        print(f"[DEBUG] Занятые слоты: {booked}")

        conn.close()

        for hour in range(10, 19):  # с 10:00 до 19:59
            for minute in range(0, 60, 30):
                time_str = f"{hour:02}:{minute:02}"
                if time_str not in booked:
                    callback_data = f"select_time|rental|{car_id}|{date_str}|{time_str}"
                    markup.add(types.InlineKeyboardButton(time_str, callback_data=callback_data))

        return markup
    except Exception as e:
        print(f"Ошибка 8647: {e}")



@bot.message_handler(func=lambda message: message.text == "Написать адрес")
def ask_for_address(message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        session = get_session(user_id)

        car_id = session.get("selected_car_id")
        if not car_id:
            bot.send_message(chat_id, "❌ Ошибка: не выбрана машина.")
            return

        bot.send_message(chat_id, "Пожалуйста, напишите адрес вашего местоположения.")
        bot.register_next_step_handler(message, lambda m: receive_location(m, car_id))
    except Exception as e:
        print(f"Ошибка 8666: {e}")


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
    try:
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

    except Exception as e:
        print(f"Ошибка 8727: {e}")

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
    try:
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
    except Exception as e:
        print(f"Ошибка 8799: {e}")


# --- Админ-панель для удаления машин ---
@bot.message_handler(commands=['delete_car'])
def admin_panel(message):
    try:
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
    except Exception as e:
        print(f"Ошибка 8822: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def delete_car(call):
    try:
        if call.from_user.id not in ADMIN_ID:
            bot.answer_callback_query(call.id, " Нет прав!")
            return

        car_id = int(call.data.split('_')[1])
        cursor.execute('DELETE FROM cars WHERE id = ?', (car_id,))
        conn.commit()
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="\u2705 Машина удалена.")
        bot.answer_callback_query(call.id, "Удалено!")
    except Exception as e:
        print(f"Ошибка 8839: {e}")


# --- Фильтрация по диапазону годов ---
@bot.callback_query_handler(func=lambda call: call.data == 'По году')
def year_range_filter(call):
    try:

        bot.send_message(call.message.chat.id, "Введите диапазон годов в формате: `2015-2020`", parse_mode="Markdown")
        bot.register_next_step_handler(call.message, process_year_range)
    except Exception as e:
        print(f"Ошибка 8850: {e}")

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
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cars")
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Таблица машин успешно очищена.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при очистке: {e}")


@bot.message_handler(commands=['list_cars'])
def list_all_cars(message):
    try:
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

    except Exception as e:
        print(f"Ошибка 8912: {e}")

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
    try:
        user_id = message.from_user.id
        session = get_session(user_id)

        session.clear()  # очищаем предыдущую сессию, если была
        set_state(user_id, "calculate_model")

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Рено Логан", "Фольцваген Поло", "Шкода Рапид", "Шкода Октавия")
        bot.send_message(message.chat.id, "Выберите модель автомобиля:", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка 8943: {e}")


@bot.message_handler(func=lambda message: get_state(message.from_user.id) == "calculate_model")
def calculate_model(message):
    try:
        user_id = message.from_user.id
        session = get_session(user_id)

        session['model'] = message.text.strip()
        set_state(user_id, "calculate_service")

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Аренда", "Прокат", "Выкуп")
        bot.send_message(message.chat.id, "Выберите услугу:", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка 8959: {e}")


@bot.message_handler(func=lambda message: get_state(message.from_user.id) == "calculate_service")
def calculate_service(message):
    try:
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
    except Exception as e:
        print(f"Ошибка 8988: {e}")


@bot.message_handler(func=lambda message: get_state(message.from_user.id) == "calculate_year")
def calculate_year(message):
    try:
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

    except Exception as e:
        print(f"Ошибка 9027: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("rental_days_"))
def rental_days_selected(call):
    try:
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
    except Exception as e:
        print(f"Ошибка 9058: {e}")




@bot.callback_query_handler(func=lambda call: call.data == "start_filter")
def start_filtering(call):
    try:
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
    except Exception as e:
        print(f"Ошибка 9079: {e}")


@bot.message_handler(func=lambda m: get_state(m.from_user.id) == "filter_select")
def filter_select(message):
    try:
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

    except Exception as e:
        print(f"Ошибка 9109: {e}")

@bot.message_handler(func=lambda m: get_state(m.from_user.id) == "filter_value")
def filter_value(message):
    try:
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

    except Exception as e:
        print(f"Ошибка 9176: {e}")

@bot.message_handler(commands=['profile'])
def profile_command(message):
    try:
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
    except Exception as e:
        print(f"Ошибка 9204: {e}")


@bot.message_handler(commands=['edit_car'])
def edit_car(message):
    try:
        if message.from_user.id != ADMIN_ID:
            return bot.send_message(message.chat.id, "Нет доступа.")

        user_id = message.from_user.id
        session = get_session(user_id)

        session.clear()
        set_state(user_id, "edit_car_id")

        bot.send_message(message.chat.id, "Введите ID машины для редактирования:")
    except Exception as e:
        print(f"Ошибка 9221: {e}")


@bot.message_handler(func=lambda m: get_state(m.from_user.id) == "edit_car_id")
def edit_car_id(message):
    try:
        user_id = message.from_user.id
        session = get_session(user_id)

        session["edit_id"] = message.text.strip()
        set_state(user_id, "edit_car_field")

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Марка и модель", "Год", "Двигатель", "Коробка", "Расход", "Привод")

        bot.send_message(message.chat.id, "Что изменить?", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка 9238: {e}")


@bot.message_handler(func=lambda m: get_state(m.from_user.id) == "edit_car_field")
def edit_car_field(message):
    try:
        user_id = message.from_user.id
        session = get_session(user_id)

        session["edit_field"] = message.text.strip()
        set_state(user_id, "edit_car_value")

        bot.send_message(message.chat.id, "Введите новое значение:")
    except Exception as e:
        print(f"Ошибка 9252: {e}")


@bot.message_handler(func=lambda m: get_state(m.from_user.id) == "edit_car_value")
def edit_car_value(message):
    try:
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
    except Exception as e:
        print(f"Ошибка 9254: {e}")

    # --- ЗАПУСК ---


# --- Обработчик команды /view_questions ---
@bot.message_handler(commands=['view_questions'])
def view_questions(message):
    try:
        if message.from_user.id not in ADMIN_ID:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")
            return

        conn = sqlite3.connect(DB_PATH)
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
    except Exception as e:
        print(f"Ошибка 9325: {e}")


@bot.message_handler(commands=['delete_question'])
def delete_question(message):
    try:
        if message.from_user.id not in ADMIN_ID:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")
            return

        conn = sqlite3.connect(DB_PATH)
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
    except Exception as e:
        print(f"Ошибка 9352: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("delq_"))
def handle_delete_question(call):
    try:
        if call.from_user.id not in ADMIN_ID:
            bot.answer_callback_query(call.id, "Нет доступа.")
            return

        question_id = int(call.data.split("_")[1])
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        conn.commit()
        conn.close()

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text="✅ Вопрос удалён.")
    except Exception as e:
        print(f"Ошибка 9373: {e}")


@bot.message_handler(commands=['delete_all_question'])
def delete_questions(message):
    try:
        if message.from_user.id not in ADMIN_ID:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")
            return

        conn = sqlite3.connect(DB_PATH)
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
    except Exception as e:
        print(f"Ошибка 9406: {e}")


@bot.message_handler(commands=['reset_bookings'])
def handle_reset_bookings(message):
    try:
        if message.from_user.id == ADMIN_ID2:  # Проверка на админа
            reset_bookings_table()
            bot.reply_to(message, "✅ Таблица `bookings` сброшена.")
        else:
            bot.reply_to(message, "🚫 У вас нет доступа к этой команде.")
    except Exception as e:
        print(f"Ошибка 9418: {e}")


def reset_bookings_table():
    try:
        conn = sqlite3.connect(DB_PATH)
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
    try:
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
    except Exception as e:
        print(f"Ошибка 9471: {e}")


@bot.message_handler(commands=['list_users'])
def list_users_handler(message):
    try:
        if message.chat.id not in ADMIN_ID:
            bot.reply_to(message, "❌ У вас нет доступа к этой команде.")
            return

        conn = sqlite3.connect(DB_PATH)
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
    except Exception as e:
        print(f"Ошибка 9505: {e}")


@bot.message_handler(commands=['view_bookings'])
def view_bookings(message):
    try:
        user_id = message.from_user.id

        if user_id != ADMIN_ID2:
            bot.send_message(user_id, "⛔ У вас нет доступа к этой команде.")
            return

        conn = sqlite3.connect(DB_PATH)
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
            bot.send_message(user_id, text[i:i + MAX_LEN], parse_mode="HTML")

    except Exception as e:
        print(f"Ошибка 9608: {e}")

from threading import Lock

notify_lock = Lock()




def send_late_pickup_notifications():
    try:
        today = date.today()
        today_str = today.strftime("%Y-%m-%d")
        print("[send_pickup_notifications] Запуск1")

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # === 1. Уведомления для rental ===
            cursor.execute("""
                    SELECT rh.user_id, rh.car_id, rh.rent_start, b.deposit_status, 
                           u.telegram_id, b.service, b.date, u.status
                    FROM rental_history rh
                    JOIN bookings b ON rh.user_id = b.user_id AND rh.car_id = b.car_id
                    JOIN users u ON rh.user_id = u.telegram_id
                    WHERE rh.status = 'confirmed'
                      AND b.deposit_status = 'paid'
                      AND rh.rent_start = ?
                      AND u.status = 'waiting_rental'
                      AND b.service = 'rental'
                """, (today_str,))
            rental_rows = cursor.fetchall()

            for row in rental_rows:
                telegram_id = row["telegram_id"]
                message = (
                    "🚗 Добрый день! Сегодня начинается ваша аренда автомобиля.\n\n"
                    "Вы можете приехать и забрать машину в любое удобное время до 20:00.\n"
                    "⚠️ В 20:00 аренда начнётся автоматически.\n"
                    "Если возникнут вопросы, пожалуйста, свяжитесь с нами.\n\n"
                    "Желаем отличного путешествия!\n"
                    "Нажмите на /go"
                )
                bot.send_message(telegram_id, message)
                cursor.execute("UPDATE users SET status = ? WHERE telegram_id = ?", ('waiting_car', telegram_id))

            # === 2. Уведомления для rent ===
            cursor.execute("""
                    SELECT b.user_id, b.car_id, b.date, u.telegram_id, u.status
                    FROM bookings b
                    JOIN users u ON b.user_id = u.telegram_id
                    WHERE b.status = 'confirmed'
                      AND b.deposit_status = 'paid'
                      AND b.service = 'rent'
                      AND u.status = 'waiting_rental'
                """)
            rent_rows = cursor.fetchall()
            print(1)
            for row in rent_rows:
                booking_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
                if booking_date + timedelta(days=1) == today:
                    telegram_id = row["telegram_id"]
                    message = (
                        "🚗 Доброе утро! Сегодня вы можете забрать автомобиль.\n\n"
                        "С завтрашнего дня аренда начнется автоматически.\n"
                        "Если возникнут вопросы, пожалуйста, свяжитесь с нами.\n\n"
                        "Желаем отличного путешествия!\n"
                        "Нажмите на /go"
                    )
                    bot.send_message(telegram_id, message)
                    cursor.execute("UPDATE users SET status = ? WHERE telegram_id = ?", ('waiting_car', telegram_id))

            conn.commit()
    except Exception as e:
        print(f"Ошибка 9683: {e}")


def send_pickup_notifications():
    try:
        today_str = date.today().strftime("%Y-%m-%d")
        today = date.today()
        yesterday = today - timedelta(days=1)
        print("[send_pickup_notifications] Запуск")

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # === УВЕДОМЛЕНИЯ О НАЧАЛЕ АРЕНДЫ ===
            cursor.execute("""
                    SELECT rh.user_id, rh.car_id, rh.rent_start, b.deposit_status, 
                           u.telegram_id, b.created_at, u.status
                    FROM rental_history rh
                    JOIN bookings b ON rh.user_id = b.user_id AND rh.car_id = b.car_id
                    JOIN users u ON rh.user_id = u.telegram_id
                    WHERE rh.status = 'confirmed'
                      AND b.deposit_status = 'paid'
                      AND rh.rent_start = ?
                      AND u.status = 'waiting_rental'
                """, (today_str,))
            start_rows = cursor.fetchall()

            for row in start_rows:
                telegram_id = row["telegram_id"]
                created_at = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S").date()

                # --- Проверка даты подачи заявки ---
                if created_at == yesterday:
                    print(f"[START] Пропускаем {telegram_id} — заявка подана вчера ({created_at})")
                    continue
                elif created_at == today:
                    print(f"[START] Пропускаем {telegram_id} — заявка подана сегодня ({created_at})")
                    continue

                try:
                    message = (
                        f"🚗 Доброе утро! Сегодня начинается ваша аренда автомобиля.\n\n"
                        f"Вы можете приехать и забрать машину в любое удобное время до 20:00.\n"
                        f"⚠️ В 20:00 аренда начнётся автоматически.\n"
                        f"Если возникнут вопросы, пожалуйста, свяжитесь с нами.\n\n"
                        f"Желаем отличного путешествия!\n"
                        f"Нажмите на /go"
                    )
                    bot.send_message(telegram_id, message)

                    # Меняем статус
                    cursor.execute("UPDATE users SET status = ? WHERE telegram_id = ?", ('waiting_car', telegram_id))
                    conn.commit()
                except Exception as e:
                    print(f"[send_pickup_notifications][START] Ошибка отправки {telegram_id}: {e}")

            # === УВЕДОМЛЕНИЯ О КОНЦЕ АРЕНДЫ ===
            cursor.execute("""
                    SELECT b.user_id, b.car_id, b.created_at, u.telegram_id,
                           c.brand_model, c.year, rh.rent_end
                    FROM bookings b
                    JOIN rental_history rh ON b.user_id = rh.user_id AND b.car_id = rh.car_id
                    JOIN users u ON b.user_id = u.telegram_id
                    JOIN cars c ON b.car_id = c.car_id
                    WHERE b.service = 'rental'
                      AND b.status = 'process'
                      AND rh.rent_end = ?
                """, (today_str,))
            end_rows = cursor.fetchall()

            for row in end_rows:
                try:
                    telegram_id = row["telegram_id"]
                    brand_model = row["brand_model"]
                    year = row["year"]
                    rent_end = row["rent_end"]
                    created_at = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")

                    # Время сдачи = дата окончания аренды + время из created_at
                    return_dt = datetime.strptime(rent_end, "%Y-%m-%d").replace(
                        hour=created_at.hour,
                        minute=created_at.minute,
                        second=0
                    )
                    return_time_str = return_dt.strftime("%H:%M")

                    kb = types.InlineKeyboardMarkup(row_width=2)
                    kb.add(
                        types.InlineKeyboardButton("✅ Продлить", callback_data="extend_rental"),
                        types.InlineKeyboardButton("🕒 Сдам вовремя", callback_data="return_on_time")
                    )

                    msg = (
                        f"📅 Сегодня заканчивается ваша аренда автомобиля <b>{brand_model} ({year})</b>.\n"
                        f"⏰ Время возврата: <b>{return_time_str}</b>\n\n"
                        f"Выберите действие:"
                    )

                    bot.send_message(telegram_id, msg, parse_mode="HTML", reply_markup=kb)

                except Exception as e:
                    print(f"[send_pickup_notifications][END] Ошибка отправки {telegram_id}: {e}")
    except Exception as e:
        print(f"Ошибка 9787: {e}")


def force_start_rental():
    try:
        today_str = date.today().strftime("%Y-%m-%d")

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            print(1)
            # Находим арендованные машины на сегодня с залогом и подтверждённой арендой
            cursor.execute("""
                    SELECT rh.user_id, rh.car_id, rh.rent_start, c.station, c.brand_model, c.year, u.telegram_id
                    FROM rental_history rh
                    JOIN bookings b ON rh.user_id = b.user_id AND rh.car_id = b.car_id
                    JOIN cars c ON rh.car_id = c.car_id
                    JOIN users u ON rh.user_id = u.telegram_id
                    WHERE rh.status = 'confirmed'
                      AND b.deposit_status = 'paid'
                      AND rh.rent_start = ?
                      AND b.status = 'confirmed'
                """, (today_str,))

            rentals = cursor.fetchall()

            for rental in rentals:
                user_id = rental["user_id"]
                car_id = rental["car_id"]
                car_name = rental["brand_model"]
                car_year = rental["year"]
                station = rental["station"]
                telegram_id = rental["telegram_id"]

                # 1. Обновляем статус аренды как "в процессе"
                cursor.execute("""
                        UPDATE rental_history SET status = 'confirmed', end_time = ?
                        WHERE user_id = ? AND car_id = ? AND rent_start = ?
                    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id, car_id, today_str))

                conn.commit()

                # 2. Отправляем уведомление клиенту
                try:
                    msg = (
                        f"🚗 Ваша аренда автомобиля <b>{car_name} ({car_year})</b> на станции <b>{station}</b> "
                        f"была автоматически запущена в 20:00.\n\n"
                        f"❗️Пожалуйста, как можно скорее подойдите к машине или свяжитесь с администратором, "
                        f"если у вас изменились планы."
                    )
                    bot.send_message(telegram_id, msg, parse_mode="HTML")
                except Exception as e:
                    print(f"[force_start_rental] Ошибка отправки клиенту {telegram_id}: {e}")
    except Exception as e:
        print(f"Ошибка 9841: {e}")


def get_session2(chat_id):
    try:

        if chat_id not in session:
            session[chat_id] = {}  # всегда создаём словарь
        return session[chat_id]
    except Exception as e:
        print(f"Ошибка 9851: {e}")

def get_state2(chat_id):
    try:

        return get_session(chat_id).get("state")
    except Exception as e:
        print(f"Ошибка 9858: {e}")

def set_state2(chat_id, state_value):
    try:

        get_session(chat_id)["state"] = state_value
    except Exception as e:
        print(f"Ошибка 9865: {e}")

# -------------------------------
# Калькулятор цены
# -------------------------------

# Обработчик выбора "Продлить посуточно"
@bot.callback_query_handler(func=lambda call: call.data in ["extend_rental", "return_on_time"])
def handle_return_action(call):
    try:
        chat_id = call.message.chat.id

        if call.data == "extend_rental":
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("📅 Продлить посуточно", "🕒 Продлить почасово")
            kb.add("🔙 Отмена")

            bot.send_message(chat_id,
                             "🔄 Выберите, как хотите продлить аренду:\n\n"
                             "💡 <b>Посуточно</b> — дешевле, чем почасовая оплата.\n"
                             "💡 <b>Почасово</b> — если нужна машина только на немного дольше.",
                             parse_mode="HTML",
                             reply_markup=kb)

        elif call.data == "return_on_time":
            bot.send_message(chat_id, "✅ Отлично! Ждём вас в назначенное время на станции.")
    except Exception as e:
        print(f"Ошибка 9892: {e}")


@bot.message_handler(func=lambda m: m.text == "📅 Продлить посуточно")
def extend_daily_select_days(message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        set_state2(user_id, "extend_daily")  # сохраняем состояние

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                    SELECT rh.id, rh.end_time, rh.car_id, c.price
                    FROM rental_history rh
                    JOIN cars c ON rh.car_id = c.car_id
                    WHERE rh.user_id = ? AND rh.status = 'confirmed'
                    ORDER BY rh.id DESC LIMIT 1
                """, (user_id,))
            rental = cursor.fetchone()
            if not rental:
                bot.send_message(chat_id, "❌ Активная аренда не найдена.")
                return

            car_id = rental["car_id"]
            end_time_dt = datetime.strptime(rental["end_time"], "%Y-%m-%d %H:%M:%S")
            end_time_date = end_time_dt.date()

            # Проверка ближайшей брони
            cursor.execute("""
                    SELECT rent_start
                    FROM rental_history
                    WHERE car_id = ? AND status = 'confirmed' AND rent_start > ?
                    ORDER BY rent_start ASC
                    LIMIT 1
                """, (car_id, end_time_date.strftime("%Y-%m-%d")))
            next_booking = cursor.fetchone()

            if next_booking:
                next_date = datetime.strptime(next_booking["rent_start"], "%Y-%m-%d").date()
                free_days = (next_date - end_time_date).days
            else:
                free_days = 7  # максимум 7 дней

            if free_days == 1:
                bot.send_message(chat_id, "❌ Нет свободных дней для продления.")
                return

            # Клавиатура выбора дней
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for i in range(1, min(7, free_days)):
                label = f"{i} день" if i == 1 else f"{i} дня" if 1 < i < 5 else f"{i} дней"
                kb.add(label)
            kb.add("🔙 Отмена")

            bot.send_message(chat_id, "📅 На сколько дней хотите продлить аренду?", reply_markup=kb)

    except Exception as e:
        print(f"Ошибка 9953: {e}")

@bot.message_handler(func=lambda m: any(word in m.text for word in ["день", "дня", "дней"]))
def confirm_daily_extension(message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        if get_state2(user_id) != "extend_daily":
            return

        try:
            days = int(message.text.split()[0])
        except:
            bot.send_message(chat_id, "❌ Неверный формат.")
            return

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                    SELECT rh.id, rh.end_time, rh.car_id, c.price
                    FROM rental_history rh
                    JOIN cars c ON rh.car_id = c.car_id
                    WHERE rh.user_id = ? AND rh.status = 'confirmed'
                    ORDER BY rh.id DESC LIMIT 1
                """, (user_id,))
            rental = cursor.fetchone()

            if not rental:
                bot.send_message(chat_id, "❌ Аренда не найдена.")
                return

            base_price = rental["price"]
            total_price = calculate_price(base_price, days)

            old_end_time = datetime.strptime(rental["end_time"], "%Y-%m-%d %H:%M:%S")
            new_end_time = old_end_time + timedelta(days=days)
            new_rent_end = new_end_time.date()

            cursor.execute("""
                    UPDATE rental_history
                    SET end_time = ?, rent_end = ?
                    WHERE id = ?
                """, (
                new_end_time.strftime("%Y-%m-%d %H:%M:%S"),
                new_rent_end.strftime("%Y-%m-%d"),
                rental["id"]
            ))
            conn.commit()

            kb = types.InlineKeyboardMarkup()
            pay_button = types.InlineKeyboardButton(
                text="💳 Оплатить",
                callback_data=f"repay_daily_extend_{rental['id']}_{total_price}"
            )
            kb.add(pay_button)

            bot.send_message(chat_id,
                             f"✅ Аренда продлена на <b>{days} дн.</b>\n"
                             f"📆 Новый срок: до <b>{new_end_time.strftime('%d.%m.%Y %H:%M')}</b>\n"
                             f"💰 Стоимость: <b>{total_price} ₽</b>\n\n"
                             f"Для завершения продления, пожалуйста, оплатите:",
                             parse_mode="HTML",
                             reply_markup=kb)

        # Очистка состояния
        session.pop(user_id, None)

    except Exception as e:
        print(f"Ошибка 10024: {e}")

@bot.message_handler(func=lambda m: m.text == "🔙 Отмена")
def cancel_action(message):
    try:

        user_id = message.from_user.id
        session.pop(user_id, None)
        bot.send_message(message.chat.id, "❌ Действие отменено.", reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        print(f"Ошибка 10034: {e}")

@bot.message_handler(func=lambda m: m.text == "🕒 Продлить почасово")
def extend_by_hour(message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Получаем допустимые часы продления
        allowed_hours, reason = get_allowed_extension_hours(user_id)
        if not allowed_hours:
            bot.send_message(chat_id, reason)
            return

        # Генерация клавиатуры только с разрешёнными часами
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        row = []
        for h in allowed_hours:
            row.append(f"{h} час" if h == 1 else f"{h} часа" if h in [2, 3, 4] else f"{h} часов")
            if len(row) == 3:
                kb.row(*row)
                row = []
        if row:
            kb.row(*row)
        kb.add("🔙 Отмена")

        bot.send_message(chat_id, "⏱ На сколько часов продлить аренду?", reply_markup=kb)
    except Exception as e:
        print(f"Ошибка 10062: {e}")


def get_allowed_extension_hours(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # 1️⃣ Конец текущей аренды
        cur.execute("""
                SELECT end_time
                FROM rental_history
                WHERE user_id = ? AND status = 'confirmed'
                ORDER BY id DESC
                LIMIT 1
            """, (user_id,))
        current = cur.fetchone()
        if not current or not current["end_time"]:
            conn.close()
            return [], "❌ Не найдено время окончания текущей аренды."

        end_time = datetime.strptime(current["end_time"], "%Y-%m-%d %H:%M:%S")

        # 2️⃣ Начало следующей аренды
        cur.execute("""
                SELECT rent_start
                FROM rental_history
                WHERE user_id = ?
                  AND status IN ('pending', 'confirmed')
                  AND rent_start > ?
                ORDER BY rent_start ASC
                LIMIT 1
            """, (user_id, end_time.strftime("%Y-%m-%d %H:%M:%S")))
        next_rent = cur.fetchone()
        conn.close()

        if not next_rent or not next_rent["rent_start"]:
            # Нет следующей аренды — все кнопки разрешены
            return [1, 2, 3, 4, 6, 8, 10, 12], "✅ Продление без ограничений."

        # 3️⃣ Приводим rent_start к 8:00
        next_start_date = datetime.strptime(next_rent["rent_start"], "%Y-%m-%d")
        next_start = next_start_date.replace(hour=8, minute=0, second=0)
        # 4️⃣ Считаем, сколько часов доступно
        max_hours = int((next_start - end_time).total_seconds() // 3600) - 24
        if max_hours <= 0:
            return [], "❌ Продление невозможно — следующая аренда слишком близко."

        # 5️⃣ Фильтруем кнопки
        possible_hours = [1, 2, 3, 4, 6, 8, 10, 12]
        allowed = [h for h in possible_hours if h <= max_hours]

        if not allowed:
            return [], "❌ Нет доступных вариантов продления."
        return allowed, f"✅ Можно продлить максимум на {max_hours} часов."

    except Exception as e:
        print(f"Ошибка 10120: {e}")

from math import ceil


# Вспомогательная функция округления до кратного 5
def round_to_nearest_five(n):
    return int(ceil(n / 5.0)) * 5


@bot.message_handler(func=lambda m: m.text.lower().endswith(("час", "часа", "часов")))
def confirm_hour_extension(message):
    try:
        from datetime import datetime, timedelta

        chat_id = message.chat.id
        user_id = message.from_user.id

        try:
            hours = int(message.text.split()[0])
            if not 1 <= hours <= 12:
                raise ValueError
        except:
            bot.send_message(chat_id, "❌ Укажите число от 1 до 12.")
            return

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Получаем текущую аренду с фактическим end_time
            cursor.execute("""
                    SELECT rh.id AS rental_id, rh.start_time, rh.end_time, rent_start, rh.car_id, rh.status, 
                           c.price AS daily_price
                    FROM rental_history rh
                    JOIN cars c ON rh.car_id = c.car_id
                    WHERE rh.user_id = ? AND rh.status = 'confirmed'
                    ORDER BY rh.id DESC LIMIT 1
                """, (user_id,))
            rental = cursor.fetchone()

            if not rental:
                bot.send_message(chat_id, "❌ Не удалось найти активную аренду.")
                return

            current_end = datetime.strptime(rental["end_time"], "%Y-%m-%d %H:%M:%S")

            # Прибавляем часы
            new_end = current_end + timedelta(hours=hours)

            # Обновляем и end_time, и rent_end
            cursor.execute("""
                    UPDATE rental_history
                    SET end_time = ?, rent_end = ?
                    WHERE id = ?
                """, (
                new_end.strftime("%Y-%m-%d %H:%M:%S"),  # полное время
                new_end.strftime("%Y-%m-%d"),  # только дата
                rental["rental_id"]
            ))
            conn.commit()

            # 🔢 Почасовая стоимость
            base_hour_price = rental["daily_price"] / 24
            base_hour_price = round_to_nearest_five(base_hour_price)
            final_hour_price = round_to_nearest_five(base_hour_price * 1.3)
            total_price = final_hour_price * hours

            # 💳 Кнопка оплаты
            kb = types.InlineKeyboardMarkup()
            pay_button = types.InlineKeyboardButton(
                text="💳 Оплатить",
                callback_data=f"repay_extend_{rental['rental_id']}_{hours}_{total_price}"
            )
            kb.add(pay_button)

            bot.send_message(chat_id,
                             f"✅ Аренда будет продлена на <b>{hours} ч.</b>\n"
                             f"📆 Новый срок: <b>{new_end.strftime('%d.%m.%Y %H:%M')}</b>\n"
                             f"💰 Стоимость: <b>{total_price} ₽</b>\n\n"
                             f"Для продления аренды необходимо оплатить:",
                             parse_mode="HTML",
                             reply_markup=kb)
    except Exception as e:
        print(f"Ошибка 10204: {e}")


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("repay_daily_extend_") or call.data.startswith("repay_extend_"))
def handle_payment_callback(call):
    try:
        data_parts = call.data.split("_")
        rental_id = data_parts[2]
        amount = data_parts[3]
        payment_type = "Посуточное" if "daily" in call.data else "Почасовое"

        bot.answer_callback_query(call.id)

        # Здесь вставь свою ссылку на платёжную систему
        # Для примера — подставляем rental_id и сумму
        payment_url = f"https://yourpaymentlink.com/pay?rental_id={rental_id}&amount={amount}"

        bot.send_message(call.message.chat.id,
                         f"💳 {payment_type} продление\n"
                         f"Сумма к оплате: <b>{amount} ₽</b>\n"
                         f"🔗 Перейдите по ссылке для оплаты:\n"
                         f"{payment_url}",
                         parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка 10229: {e}")


def finalize_hourly_extension(rental_id: int, new_end_datetime: datetime, total_price: float, chat_id: int):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # Обновляем дату и время окончания аренды (сохраняем как строку с временем)
            cursor.execute("UPDATE rental_history SET end_time = ? WHERE id = ?",
                           (new_end_datetime.strftime("%Y-%m-%d %H:%M:%S"), rental_id))
            conn.commit()

        bot.send_message(chat_id,
                         f"✅ Оплата прошла успешно!\n"
                         f"⏰ Аренда продлена до <b>{new_end_datetime.strftime('%d.%m.%Y %H:%M')}</b>\n"
                         f"💰 Сумма оплаты: <b>{total_price} ₽</b>",
                         parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка 10247: {e}")


def notify_admin():
    # Попытка получить блокировку без ожидания — если функция уже запущена, выйдем
    try:
        if not notify_lock.acquire(blocking=False):
            print("[notify_admin] Пропуск — функция уже работает.")
            return

        start_time = datetime.now()
        try:
            print(f"[notify_admin] Запуск в {start_time}")

            check_upcoming_bookings()
            cancel_expired_bookings()
            check_rental_return_times()
        except Exception as e:
            print(f"[notify_admin] ❌ Ошибка верхнего уровня: {e}")
        finally:
            notify_lock.release()
            print(f"[notify_admin] Завершено за {datetime.now() - start_time}")
    except Exception as e:
        print(f"Ошибка 10270: {e}")


def check_rental_return_times():
    try:
        now = datetime.now()

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT b.user_id, b.car_id, u.telegram_id,
                       c.brand_model, c.year,
                       rh.end_time
                FROM bookings b
                JOIN rental_history rh ON b.user_id = rh.user_id AND b.car_id = rh.car_id
                JOIN users u ON b.user_id = u.telegram_id
                JOIN cars c ON b.car_id = c.car_id
                WHERE b.service = 'rental' AND b.status = 'process'
            """)

            rows = cursor.fetchall()

            for row in rows:
                user_id = row['user_id']
                telegram_id = row['telegram_id']
                brand_model = row['brand_model']
                year = row['year']
                end_time_str = row['end_time']

                try:
                    # Определяем формат даты
                    if len(end_time_str.strip()) == 10:  # только дата
                        end_time = datetime.strptime(end_time_str, "%Y-%m-%d")
                    else:  # дата + время
                        end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")

                    if now > end_time:
                        overdue_hours = round((now - end_time).total_seconds() / 3600)
                        warning_text = (
                            f"⚠️ Аренда автомобиля <b>{brand_model} ({year})</b> завершилась {overdue_hours} ч. назад.\n"
                            f"Пожалуйста, сдайте авто или продлите аренду, чтобы избежать штрафа."
                        )
                        bot.send_message(telegram_id, warning_text, parse_mode="HTML")

                except Exception as e:
                    print(f"[check_rental_return_times] Ошибка для user {user_id}: {e}")

    except Exception as e:
        print(f"Ошибка 10315: {e}")

def check_upcoming_bookings():
    try:
        now = datetime.now()
        current_date = now.strftime('%Y-%m-%d')

        # Сопоставление service → человекочитаемые названия на русском
        service_labels = {
            'rent': 'Аренда',
            'gazel': 'Газелист',
            'malyar': 'Маляр',
            'evacuator': 'Эвакуатор',
            'shinomontazh': 'Шиномонтаж',
            'diagnostic': 'Диагностика',
            'other': 'Другое'
        }

        try:
            with sqlite3.connect(DB_PATH, timeout=10) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                        SELECT b.id, u.name, u.telegram_id, c.brand_model, b.date, b.time, b.service
                        FROM bookings b
                        JOIN users u ON b.user_id = u.telegram_id
                        LEFT JOIN cars c ON b.car_id = c.car_id
                        WHERE b.status = 'confirmed' AND b.date = ? AND b.notified = 0
                    ''', (current_date,))
                bookings = cursor.fetchall()

            for booking in bookings:
                booking_id, name, user_id, car_model, date_str, time_str, service = booking
                try:
                    booking_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                except ValueError:
                    continue

                if now <= booking_time <= now + timedelta(minutes=5):
                    car_model_display = car_model if car_model else "—"
                    service_display = service_labels.get(service, service)  # Если нет в списке, покажем как есть

                    message = (
                        f"📣 <b>Время встречи!</b>\n\n"
                        f"🔹 <b>#{booking_id}</b>\n"
                        f"👤 Клиент: {html.escape(name)}\n"
                        f"🚗 Машина: {html.escape(car_model_display)}\n"
                        f"🛠 Услуга: <b>{html.escape(service_display)}</b>\n"
                        f"📅 Дата: <b>{date_str}</b>\n"
                        f"🕒 Время: <b>{time_str}</b>"
                    )

                    markup = InlineKeyboardMarkup()
                    markup.add(
                        InlineKeyboardButton("✅ Сделка состоялась", callback_data=f"deal_success_{booking_id}_{user_id}"),
                        InlineKeyboardButton("❌ Не состоялась", callback_data=f"deal_fail_{booking_id}_{user_id}")
                    )
                    try:
                        bot.send_message(ADMIN_ID2, message, parse_mode="HTML", reply_markup=markup)
                        with sqlite3.connect(DB_PATH, timeout=10) as conn:
                            conn.execute("UPDATE bookings SET notified = 1 WHERE id = ?", (booking_id,))
                            conn.commit()
                    except Exception as e:
                        print(f"[check_upcoming_bookings] Ошибка отправки сообщения: {e}")

        except Exception as e:
            print(f"[check_upcoming_bookings] ❌ Ошибка при проверке бронирований: {e}")

    except Exception as e:
        print(f"Ошибка 10384: {e}")

def send_meeting_notification(booking_id, name, user_id, car_model, date_str, time_str, service):
    try:
        now = datetime.now()
        booking_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        if not (now <= booking_time <= now + timedelta(minutes=60)):
            return

        message = (
            f"📣 <b>Время встречи!</b>\n\n"
            f"🔹 <b>#{booking_id}</b>\n"
            f"👤 Клиент: {html.escape(name)}\n"
            f"🚗 Машина: {html.escape(car_model)}\n"
            f"🛠 Услуга: <b>{service}</b>\n"
            f"📅 Дата: <b>{date_str}</b>\n"
            f"🕒 Время: <b>{time_str}</b>"
        )
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Сделка состоялась", callback_data=f"deal_success_{booking_id}_{user_id}"),
            InlineKeyboardButton("❌ Не состоялась", callback_data=f"deal_fail_{booking_id}_{user_id}")
        )

        bot.send_message(ADMIN_ID2, message, parse_mode="HTML", reply_markup=markup)

        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            conn.execute("UPDATE bookings SET notified = 1 WHERE id = ?", (booking_id,))
            conn.commit()

    except Exception as e:
        print(f"[send_meeting_notification] Ошибка: {e}")


import sqlite3
from datetime import datetime, timedelta, timezone


def cancel_expired_bookings():
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("""
                SELECT b.*
                FROM bookings b
                JOIN users u ON b.user_id = u.telegram_id
                WHERE u.status = 'waiting_car'
            """)
            bookings = cur.fetchall()

            now = datetime.now()
            print(f"[cancel_expired_bookings] Найдено неподтверждённых броней: {len(bookings)}")

            for booking in bookings:
                booking_id = booking["id"]
                status = booking["status"]
                user_id = booking["user_id"]
                date_raw = booking["date"]
                time_raw = booking["time"]
                deposit_status = booking["deposit_status"] if "deposit_status" in booking.keys() else "unpaid"
                if not date_raw or not time_raw:
                    print(f"[cancel_expired_bookings] Пропущена заявка #{booking_id} — отсутствует date или time")
                    continue

                booking_datetime_str = f"{date_raw} {time_raw}"
                try:
                    try:
                        booking_datetime = datetime.strptime(booking_datetime_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        booking_datetime = datetime.strptime(booking_datetime_str, "%Y-%m-%d %H:%M")
                except ValueError:
                    print(
                        f"[cancel_expired_bookings] ❌ Неверный формат даты/времени в заявке #{booking_id}: {booking_datetime_str}")
                    continue

                elapsed = now - booking_datetime

                # 🕒 Логика по статусу депозита
                if deposit_status == "paid":
                    print(deposit_status)
                    expired_limit = timedelta(days=1)
                else:
                    expired_limit = timedelta(minutes=60)

                if elapsed > expired_limit:
                    print(f"[cancel_expired_bookings] ⏳ Заявка #{booking_id} просрочена (прошло {elapsed})")
                    cancel_booking(cur, booking_id, user_id)
                else:
                    print(f"[cancel_expired_bookings] ✅ Заявка #{booking_id} ещё в пределах времени (прошло {elapsed})")

            conn.commit()
            conn.close()
            print(f"[cancel_expired_bookings] Завершено за {datetime.now() - now}")
    except Exception as e:
        print(f"Ошибка 10481: {e}")


def cancel_booking(cur, booking_id, user_id):
    try:
        # Получаем car_id перед удалением заявки
        cur.execute("SELECT car_id FROM bookings WHERE id = ?", (booking_id,))
        result = cur.fetchone()
        car_id = result["car_id"] if result else None

        if car_id is not None:
            # Освобождаем машину (is_available = 1)
            cur.execute("UPDATE cars SET is_available = 1 WHERE car_id = ?", (car_id,))
            print(f"[cancel_expired_bookings] 🚗 Авто #{car_id} освобождено (is_available = 1)")
        else:
            print(f"[cancel_expired_bookings] ⚠ Не удалось получить car_id для заявки #{booking_id}")

        # Удаляем бронь
        cur.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))

        # Удаляем связанную запись из rental_history со статусом 'confirmed'
        if car_id is not None:
            cur.execute("""
                    DELETE FROM rental_history
                    WHERE user_id = ? AND car_id = ? AND status = 'confirmed'
                """, (user_id, car_id))
            print(
                f"[cancel_expired_bookings] 📄 rental_history удалена для user_id={user_id}, car_id={car_id}, status='confirmed'")

        # Обновляем статус пользователя
        cur.execute("UPDATE users SET status = 'new' WHERE telegram_id = ?", (user_id,))
        print(f"[cancel_expired_bookings] 🗑 Заявка #{booking_id} удалена, пользователь #{user_id} → 'new'")
    except Exception as e:
        print(f"Ошибка 10514: {e}")


def check_broken_cars_and_notify():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            print("[check_broken_cars_and_notify] Запуск")

            # 1. Ищем сломанные машины с датой ремонта
            cursor.execute("SELECT * FROM cars WHERE is_broken = 1 AND fix_date IS NOT NULL")
            broken_cars = cursor.fetchall()
            print(f"Найдено сломанных машин: {len(broken_cars)}")

            for broken_car in broken_cars:
                car_id = broken_car["car_id"]
                if not car_id:
                    print("⚠️ Пропущена машина без car_id")
                    continue

                # Проверяем дату ремонта
                fix_date_str = broken_car["fix_date"]

                if not fix_date_str:
                    print(f"⚠️ Машина {car_id} пропущена — нет даты ремонта")
                    continue

                try:

                    fix_date = datetime.strptime(fix_date_str, "%Y-%m-%d").date()

                except ValueError:
                    print(f"⚠ Неверный формат fix_date у машины {car_id}: {fix_date_str}")
                    continue
                # Проверяем brand и model
                brand_model = broken_car["brand_model"]
                year = broken_car["year"]

                if not brand_model or not year:
                    print(f"⚠️ Машина {car_id} пропущена — нет brand/model/year")
                    continue
                # --- 2. Ищем брони ---
                cursor.execute("""
                    SELECT * FROM bookings 
                    WHERE car_id = ? AND status = 'confirmed' AND date <= ?
                """, (car_id, fix_date.strftime("%Y-%m-%d")))
                bookings = cursor.fetchall()

                # --- 3. Ищем арендные истории ---
                cursor.execute("""
                    SELECT * FROM rental_history
                    WHERE car_id = ? AND rent_start <= ?
                """, (car_id, fix_date.strftime("%Y-%m-%d")))
                rentals = cursor.fetchall()

                # Объединяем брони и аренды
                broken_service = broken_car["service"]  # предполагается, что у машины есть поле service

                # --- Объединяем брони и аренды ---
                all_orders = []

                # добавляем брони, если сервис сломанной машины rent
                if broken_service == "rent":
                    for b in bookings:
                        cursor.execute("SELECT brand_model, year FROM cars WHERE car_id = ?", (b["car_id"],))

                        car = cursor.fetchone()
                        all_orders.append({
                            "user_id": b["user_id"],
                            "date": b["date"],
                            "booking_id": b["id"],
                            "is_booking": True,
                            "brand_model": car["brand_model"],
                            "year": car["year"],
                            "service": "rent"
                        })

                # добавляем аренды, если сервис сломанной машины rental
                elif broken_service == "rental":
                    for r in rentals:
                        cursor.execute("SELECT brand_model, year FROM cars WHERE car_id = ?", (r["car_id"],))
                        car = cursor.fetchone()

                        # Пытаемся найти связанную бронь
                        cursor.execute("""
                            SELECT id FROM bookings 
                            WHERE car_id = ? AND user_id = ? AND status = 'confirmed'
                            LIMIT 1
                        """, (r["car_id"], r["user_id"]))
                        booking_row = cursor.fetchone()
                        booking_id = booking_row["id"] if booking_row else None

                        all_orders.append({
                            "user_id": r["user_id"],
                            "date": r["rent_start"],  # можно сразу datetime.strptime здесь
                            "booking_id": booking_id,
                            "is_booking": True,
                            "brand_model": car["brand_model"],
                            "year": car["year"],
                            "service": "rental"
                        })

                # --- Фильтруем дубликаты ---
                seen = set()
                unique_orders = []
                for order in all_orders:
                    order_date = order["date"]
                    if isinstance(order_date, str):
                        order_date = datetime.strptime(order_date, "%Y-%m-%d")

                    cursor.execute("""
                        SELECT * FROM cars 
                        WHERE is_broken = 0 AND car_id != ? AND service = ?
                    """, (r["car_id"], order["service"]))
                    other_cars = cursor.fetchall()

                    alternatives = []

                    for alt in other_cars:

                        cursor.execute("""
                            SELECT COUNT(*) FROM bookings 
                            WHERE car_id = ? AND date = ? AND status = 'confirmed'
                        """, (alt["car_id"], order_date.strftime("%Y-%m-%d")))
                        busy = cursor.fetchone()[0]

                        if busy == 0:
                            alternatives.append(alt)

                    if alternatives:
                        notification_key = (order["user_id"], order_date)
                        if notification_key in sent_notifications:
                            continue

                        kb = types.InlineKeyboardMarkup()
                        for alt in alternatives[:5]:
                            btn_text = f"{alt['brand_model']} ({alt['year']}) – {alt['station']}"

                            # 🔍 проверяем, есть ли аренда
                            cursor.execute("""
                                SELECT 1 FROM rental_history
                                WHERE user_id = ? AND car_id = ? AND rent_start = ?
                                LIMIT 1
                            """, (order["user_id"], r["car_id"], order_date.strftime("%Y-%m-%d")))
                            rental_exists = cursor.fetchone()

                            if rental_exists:
                                # 👉 формат: choosing_alt_rental_<booking_id>_<user_id>_<car_id>_<date>
                                cb_data = f"choosing_alt_rental_{order['booking_id']}_{order['user_id']}_{alt['car_id']}_{order_date.strftime('%Y-%m-%d')}"
                            else:
                                # 👉 формат: choosing_alt_booking_<booking_id>_<car_id>_<date>
                                cb_data = f"choosing_alt_booking_{order['booking_id']}_{alt['car_id']}_{order_date.strftime('%Y-%m-%d')}"
                            kb.add(types.InlineKeyboardButton(text=btn_text, callback_data=cb_data))

                        # --- кнопка возврата залога (только если бронь и залог оплачен) ---
                        cursor.execute("SELECT deposit_status, user_id, broken_notified FROM bookings WHERE id = ?",
                                       (order["booking_id"],))
                        booking = cursor.fetchone()
                        if booking and booking["deposit_status"] == "paid":
                            kb.add(types.InlineKeyboardButton(
                                text="💸 Вернуть залог",
                                callback_data=f"returning_deposit_booking_{order['booking_id']}_{order['user_id']}"
                            ))
                        if booking["broken_notified"]:
                            continue
                        bot.send_message(
                            order["user_id"],
                            f"⚠️ Извините, но ваша машина {order['brand_model']} ({order['year']}) "
                            f"сломалась и не будет доступна {order_date.strftime('%d.%m.%Y')}.\n\n"
                            "Предлагаем выбрать один из доступных вариантов:",
                            reply_markup=kb,
                            parse_mode="HTML"
                        )
                        cursor.execute("UPDATE bookings SET broken_notified = 1 WHERE id = ?", (booking["id"],))
                        conn.commit()
                        sent_notifications.add(notification_key)

    except Exception as e:
        print(f"Ошибка 10693: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("choosing_alt_booking_"))
def handle_choose_alt_booking(call):
    try:
        _, _, _, booking_id, car_id, date_str = call.data.split("_")
        booking_id = int(booking_id)
        car_id = int(car_id)

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Проверяем доступность машины
            cursor.execute("""
                SELECT COUNT(*) FROM bookings 
                WHERE car_id = ? AND date = ? AND status = 'confirmed'
            """, (car_id, date_str))
            if cursor.fetchone()[0] > 0:
                bot.answer_callback_query(call.id, "❌ Эта машина уже занята!")
                return

            # Обновляем бронь
            cursor.execute("""
                UPDATE bookings 
                SET car_id = ? 
                WHERE id = ?
            """, (car_id, booking_id))
            conn.commit()

        bot.answer_callback_query(call.id, "✅ Вы выбрали альтернативную машину!")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, f"✅ Бронь #{booking_id} обновлена на машину ID {car_id}")

    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Ошибка при выборе машины!")
        bot.send_message(call.message.chat.id, f"Ошибка: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("choosing_alt_rental_"))
def handle_choose_alt_rental(call):
    try:
        _, _, _, booking_id, user_id, car_id, date_str = call.data.split("_")
        booking_id = int(booking_id) if booking_id.isdigit() else 0
        user_id = int(user_id)
        car_id = int(car_id)

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Проверяем доступность
            cursor.execute("""
                SELECT COUNT(*) FROM bookings 
                WHERE car_id = ? AND date = ? AND status = 'confirmed'
            """, (car_id, date_str))
            if cursor.fetchone()[0] > 0:
                bot.answer_callback_query(call.id, "❌ Эта машина уже занята!")
                return

            # Обновляем rental_history
            cursor.execute("""
                UPDATE rental_history 
                SET car_id = ? 
                WHERE user_id = ? AND rent_start = ?
            """, (car_id, user_id, date_str))

            # Если аренда привязана к брони → обновляем и её
            if booking_id > 0:
                cursor.execute("""
                    UPDATE bookings
                    SET car_id = ? 
                    WHERE id = ? AND user_id = ?
                """, (car_id, booking_id, user_id))

            conn.commit()

        bot.answer_callback_query(call.id, "✅ Вы выбрали альтернативную машину!")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, f"✅ Аренда на {date_str} обновлена на машину ID {car_id}")

    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Ошибка при выборе машины!")
        bot.send_message(call.message.chat.id, f"Ошибка: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("car_returned_"))
def handle_car_returned(call):
    rental_id = call.data.split("_")[2]

    try:
        with db_lock:
            with sqlite3.connect(DB_PATH, timeout=10) as conn:
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
            # cursor.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))

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
        conn = sqlite3.connect(DB_PATH, timeout=10)
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
        start_use_kb.add(types.InlineKeyboardButton("🚀 На главную", callback_data="start_use"))

        bot.send_message(user_id, feedback_text)
        bot.send_message(user_id, "Нажмите кнопку ниже, чтобы перейти в главное меню:",
                         reply_markup=start_use_kb)

    except Exception as e:
        print(f"Ошибка в handle_feedback: {e}")
        try:
            bot.answer_callback_query(call.id, f"Ошибка: {str(e)[:40]}")  # telegram ограничивает длину
        except:
            pass


@bot.callback_query_handler(func=lambda c: c.data == "start_use")
def start_use_handler(callback_query):
    try:
        user_id = callback_query.from_user.id

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Получаем бронь
        cursor.execute("""
                SELECT id, service
                FROM bookings
                WHERE user_id = ? AND status = 'confirmed'
                ORDER BY id DESC
                LIMIT 1
            """, (user_id,))
        booking = cursor.fetchone()

        if not booking:
            bot.send_message(user_id, "❌ Нет активных подтвержденных бронирований.")
            conn.close()
            return

        booking_id = booking["id"]
        service = booking["service"]

        # Логика завершения для определённых сервисов
        if service in ("painter", "gazel", "return"):
            cursor.execute("UPDATE users SET status = 'new' WHERE telegram_id = ?", (user_id,))
            cursor.execute("UPDATE bookings SET status = 'completed' WHERE id = ?", (booking_id,))
            conn.commit()
            bot.send_message(user_id, f"Бронь завершена.\n Нажми на /go")
        else:
            cursor.execute("UPDATE users SET status = 'using_car' WHERE telegram_id = ?", (user_id,))
            conn.commit()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add("/start")  # кнопка, которая отправляет команду /start
            bot.send_message(user_id,
                             " Отлично!\n\nНажмите на кнопку снизу, чтобы вернуться в меню.",
                             reply_markup=markup)

        conn.close()
    except Exception as e:
        print(f"Ошибка 10990: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "back_to_cars")
def handle_back_to_cars(call):
    try:
        chat_id = call.message.chat.id
        print(f"[DEBUG] chat_id for sending cars: {chat_id}")
        bot.answer_callback_query(call.id)
        send_available_cars(chat_id)
        print(f"[DEBUG] chat_id for sending cars: {chat_id}")

    except Exception as e:
        print(f"Ошибка 11003: {e}")

def send_available_cars(chat_id):
    try:
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
    except Exception as e:
        print(f"Ошибка 11028: {e}")


@bot.message_handler(commands=['rental_history'])
def show_rental_history(message):
    import sqlite3

    user_telegram_id = message.from_user.id
    chat_id = message.chat.id

    try:
        conn = sqlite3.connect(DB_PATH)
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
    try:
        if message.from_user.id != ADMIN_ID2:
            return bot.send_message(message.chat.id, "⛔ У вас нет доступа к этой команде.")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*), AVG(score) FROM feedback')
        total, avg = cursor.fetchone()
        conn.close()

        if total == 0:
            bot.send_message(message.chat.id, "Пока нет ни одного отзыва.")
        else:
            avg_text = f"{avg:.2f}".replace('.', ',')
            bot.send_message(message.chat.id, f"📝 Всего отзывов: <b>{total}</b>\n⭐ Средняя оценка: <b>{avg_text} / 3</b>",
                             parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка 11111: {e}")


@bot.message_handler(commands=['users'])
def handle_users_command(message):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT id, phone, name, telegram_id, status FROM users")
        users = cursor.fetchall()
        conn.close()

        if not users:
            bot.send_message(message.chat.id, "❗️Пользователи не найдены.")
            return

        # Группируем пользователей по статусу
        grouped_users = {
            'new': [],
            'waiting_car': [],
            'awaiting_use': [],
            'using_car': [],
            'blocked': [],
            'other': []
        }

        for user in users:
            status = user['status']
            if status in grouped_users:
                grouped_users[status].append(user)
            else:
                grouped_users['other'].append(user)

        # Маппинг для красивых заголовков
        status_titles = {
            'new': "🟡 Новые пользователи",
            'waiting_car': "🕓 Ожидают машину",
            'awaiting_use': "🔄 Получили авто, не начали аренду",
            'using_car': "🟢 В процессе аренды",
            'blocked': "🛑 Заблокированные",
            'other': "❓ Прочие статусы"
        }

        # Отправка блоками
        for status, title in status_titles.items():
            user_list = grouped_users[status]
            if not user_list:
                continue

            text = f"<b>{title}:</b>\n\n"

            for user in user_list:
                user_info = (
                    f"🆔 ID: {user['id']}\n"
                    f"📱 Телефон: {user['phone'] or '—'}\n"
                    f"👤 Имя: {user['name'] or '—'}\n"
                    f"💬 Telegram ID: {user['telegram_id']}\n"
                    f"📌 Статус: {user['status']}\n\n"
                )
                text += user_info

            # Разбиваем, если слишком длинно
            for i in range(0, len(text), 4000):
                bot.send_message(message.chat.id, text[i:i + 4000], parse_mode='HTML')

    except Exception as e:
        print(f"Ошибка 11179: {e}")

import sqlite3
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler


def show_main_menu(chat_id, edit_message_id=None):
    try:
        # Получаем user_id по chat_id (telegram_id)
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (chat_id,))
        user = cursor.fetchone()
        if not user:
            # Пользователь не найден — можно просто показать меню без условий
            user_id = None
        else:
            user_id = chat_id

        # Получаем активное бронирование со статусом 'process' (или 'pending'? уточни)
        booking = None
        if user_id:
            cursor.execute("""
                    SELECT service FROM bookings 
                    WHERE user_id = ? AND status = 'process' 
                    ORDER BY created_at DESC LIMIT 1
                """, (user_id,))
            booking = cursor.fetchone()

        # Формируем клавиатуру
        inline_kb = types.InlineKeyboardMarkup(row_width=2)
        inline_kb.add(
            types.InlineKeyboardButton("👤Профиль", callback_data="menu_profile"),
            types.InlineKeyboardButton("💬 Помощь", callback_data="menu_help"),
            types.InlineKeyboardButton("⛽️ Заправки", callback_data="menu_fuel"),
            types.InlineKeyboardButton("🚗 Смотреть авто", callback_data="menu_cars"),
            types.InlineKeyboardButton("🚕 Заказать такси", callback_data="taxi")
        )

        # 🔑 Если директор — добавляем свои кнопки
        if user_id == DIRECTOR_ID:
            inline_kb.add(
                types.InlineKeyboardButton("💰 Сменить цену топлива", callback_data="admin_set_price"),
                types.InlineKeyboardButton("🎁 Сменить бонусы", callback_data="admin_set_bonus"),
                types.InlineKeyboardButton("💸 Список вакансий", callback_data="admin_set_job"),
                types.InlineKeyboardButton("👤 Добавить оператора", callback_data="admin_set_operator"),
                types.InlineKeyboardButton("📢 Сделать рассылку", callback_data="admin_set_broadcast")
            )
        # 🔑 Если админ — добавляем свои кнопки
        if user_id in ADMIN_IDS:
            inline_kb.add(
                types.InlineKeyboardButton("📋 Таблицы", callback_data="admins_tables"),
                types.InlineKeyboardButton("🚗 Добавить машину", callback_data="admins_add_car")
            )
        # В зависимости от наличия брони и типа сервиса добавляем кнопки
        if booking:
            service = booking[0]
            print(service)
            if service == 'rental':
                inline_kb.add(
                    types.InlineKeyboardButton("✅ Продлить аренду", callback_data="extend_rental"),
                    types.InlineKeyboardButton("❌ Завершить аренду", callback_data="returnrent_car")
                )
            elif service == 'rent':
                # Только завершить аренду, продлить убрать
                inline_kb.add(
                    types.InlineKeyboardButton("❌ Завершить аренду", callback_data="returnrent_car")
                )
        else:
            # Если нет активной аренды — обе кнопки не показываем
            pass

        # Отправляем или редактируем сообщение
        if edit_message_id:
            bot.edit_message_text("Выберите, что вам хочется", chat_id, edit_message_id, reply_markup=inline_kb)
        else:
            bot.send_message(chat_id, "Выберите, что вам хочется", reply_markup=inline_kb)
    except Exception as e:
        print(f"Ошибка 11241: {e}")


import math


@bot.callback_query_handler(func=lambda call: call.data == "returnrent_car")
def handle_return_car(call):
    try:
        user_id = call.from_user.id

        with db_lock:
            with get_db_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                        SELECT b.id AS booking_id, b.car_id, b.service, b.status, b.time,
                               u.name, u.phone,
                               c.brand_model, c.year, c.station, c.number, c.price
                        FROM bookings b
                        JOIN users u ON b.user_id = u.telegram_id
                        JOIN cars c ON b.car_id = c.car_id
                        WHERE b.user_id = ? AND b.status = 'process'
                        ORDER BY b.id DESC
                        LIMIT 1
                    """, (user_id,))
                booking = cursor.fetchone()

                if not booking:
                    bot.answer_callback_query(call.id, "❌ У вас нет активной аренды.")
                    return

                service = booking["service"]
                car_station = booking["station"]
                car_id = booking["car_id"]

                if service == "rental":
                    cursor.execute("""
                            SELECT rh.id AS rental_id, rh.start_time, rh.end_time, rh.rent_start, rh.rent_end, rh.car_id, rh.status,
                                   c.price AS daily_price
                            FROM rental_history rh
                            JOIN cars c ON rh.car_id = c.car_id
                            WHERE rh.user_id = ? AND rh.status = 'confirmed'
                            ORDER BY rh.id DESC LIMIT 1
                        """, (user_id,))
                    rental = cursor.fetchone()

                    if not rental:
                        bot.send_message(user_id, "❌ Не удалось найти активную аренду в истории.")
                        return

                    current_end = datetime.strptime(rental["end_time"], "%Y-%m-%d %H:%M:%S")
                    now = datetime.now()

                    if now > current_end:
                        diff = now - current_end
                        hours_overdue = math.ceil(diff.total_seconds() / 3600)
                        base_hour_price = rental["daily_price"] / 24
                        base_hour_price = round_to_nearest_five(base_hour_price)
                        final_hour_price = round_to_nearest_five(base_hour_price * 2)
                        penalty = final_hour_price * hours_overdue

                        deposit = 10000
                        refund = deposit - penalty
                        if refund < 0:
                            refund = 0

                        msg = (
                            f"⏰ Внимание! Ваша заявка была просрочена на {hours_overdue} часов.\n"
                            f"Если нет штрафов и нарушений, мы вернем вам {refund} рублей из депозита.\n"
                            f"Пожалуйста, вернитесь на станцию: {car_station}\n"
                            f"🚗 Подготовьте машину к сдаче."
                        )
                    else:
                        msg = (
                            f"📍 Вернитесь на станцию: {car_station}\n"
                            f"🚗 Подготовьте машину к сдаче.\n"
                            f"Время окончания аренды: {current_end.strftime('%Y-%m-%d %H:%M:%S')}"
                        )

                    bot.send_message(user_id, msg)

                    markup = types.InlineKeyboardMarkup()
                    markup.add(
                        types.InlineKeyboardButton("✅ Я на месте", callback_data=f"return_arrived_{booking['booking_id']}"))
                    bot.send_message(user_id, "👇 Подтвердите прибытие:", reply_markup=markup)


                else:

                    set_state(user_id, f"waiting_for_time_selection|return|{car_id}")
                    send_date_buttons(user_id)
                    return
    except Exception as e:
        print(f"Ошибка 11336: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("return_arrived_"))
def handle_return_arrival(call):
    try:
        booking_id = int(call.data.split("_")[-1])
        user_id = call.from_user.id

        with db_lock:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("""
                    SELECT b.*, u.name, u.phone, c.brand_model, c.year, c.number, c.station, rh.end_time
                    FROM bookings b
                    JOIN users u ON b.user_id = u.telegram_id
                    JOIN cars c ON b.car_id = c.car_id
                    JOIN rental_history rh ON rh.car_id = b.car_id AND rh.user_id = b.user_id
                    WHERE b.id = ?
                """, (booking_id,))
            booking = cur.fetchone()

            if not booking:
                bot.send_message(user_id, "❌ Ошибка: бронь не найдена.")
                return

            operator_id = STATION_OPERATORS.get(booking["station"])
            if not operator_id:
                bot.send_message(user_id, "⚠️ Ошибка: оператор станции не найден.")
                return

            # Сообщение оператору
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                "🔑 Ключ принят",
                callback_data=f"return_done_{booking_id}_{booking['car_id']}"
            ))
            bot.send_message(operator_id,
                             f"🚗 Возврат машины:\n"
                             f"Марка: {booking['brand_model']} ({booking['year']})\n"
                             f"Госномер: {booking['number']}\n"
                             f"Станция: {booking['station']}\n"
                             f"👤 Клиент: {booking['name']} ({booking['phone']})\n"
                             f"Пожалуйста, примите машину.",
                             reply_markup=markup)

            bot.send_message(user_id, "✅ Оператору отправлено уведомление. Пожалуйста, передайте ключи.")
    except Exception as e:
        print(f"Ошибка 11386: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("return_done_"))
def handle_return_done(call):
    try:
        _, _, booking_id_str, car_id_str = call.data.split("_")
        booking_id = int(booking_id_str)
        car_id = int(car_id_str)

        with db_lock:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # 1. Получаем бронь
            cur.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
            booking = cur.fetchone()
            if not booking:
                bot.send_message(call.message.chat.id, "❌ Ошибка при получении данных бронирования.")
                return

            user_id = booking["user_id"]

            # 2. Получаем rental_history
            cur.execute("""
                    SELECT rh.*, c.price AS daily_price
                    FROM rental_history rh
                    JOIN cars c ON rh.car_id = c.car_id
                    WHERE rh.user_id = ? AND rh.car_id = ? AND rh.status = 'confirmed'
                    ORDER BY rh.id DESC LIMIT 1
                """, (user_id, car_id))
            rental = cur.fetchone()
            if not rental:
                bot.send_message(call.message.chat.id, "❌ Ошибка: не найдена запись об аренде.")
                return

            if not rental["end_time"]:
                bot.send_message(call.message.chat.id, "❌ Ошибка: не указано время окончания аренды.")
                return

            # 3. Получаем данные клиента и машины
            cur.execute("""
                    SELECT u.name, u.phone, c.brand_model, c.year, c.number, c.station
                    FROM users u
                    JOIN cars c ON c.car_id = ?
                    WHERE u.telegram_id = ?
                """, (car_id, user_id))
            info = cur.fetchone()
            if not info:
                bot.send_message(call.message.chat.id, "❌ Ошибка при получении данных пользователя или машины.")
                return

            # 4. Проверка на опоздание
            return_time = datetime.now()
            planned_end = datetime.strptime(rental["end_time"], "%Y-%m-%d %H:%M:%S")
            late = return_time > planned_end
            late_minutes = int((return_time - planned_end).total_seconds() // 60) if late else 0

            # 5. Расчет возврата залога
            deposit = 10000
            refund_amount = deposit

            if late:
                hours_overdue = math.ceil(late_minutes / 60)
                base_hour_price = rental["daily_price"] / 24
                base_hour_price = round_to_nearest_five(base_hour_price)
                final_hour_price = round_to_nearest_five(base_hour_price * 2)  # двойной тариф
                penalty = final_hour_price * hours_overdue
                refund_amount = max(deposit - penalty, 0)

            # 6. Уведомление админов
            for admin_id in ADMIN_ID:
                bot.send_message(admin_id,
                                 f"✅ Машина возвращена:\n"
                                 f"Станция: {info['station']}\n"
                                 f"Модель: {info['brand_model']} ({info['year']})\n"
                                 f"Номер: {info['number']}\n"
                                 f"👤 Клиент: {info['name']} ({info['phone']})\n"
                                 f"{'⚠️ С опозданием на ' + str(late_minutes) + ' мин.' if late else '⏱ Вовремя'}\n\n"
                                 f"💰 К возврату из залога: {refund_amount} ₽")

            # 7. Обновление статусов
            cur.execute("UPDATE bookings SET status = 'completed' WHERE id = ?", (booking_id,))
            cur.execute("UPDATE users SET status = 'new' WHERE telegram_id = ?", (user_id,))
            cur.execute("UPDATE rental_history SET status = 'completed' WHERE id = ?", (rental["id"],))

            conn.commit()

            # 8. Сообщение пользователю
            bot.send_message(user_id,
                             "✅ Возврат успешно завершён.\n"
                             "🔧 В течение 5 дней механик проверит автомобиль.\n"
                             "💸 После этого залог будет возвращён.\n"
                             "Спасибо, что воспользовались нашей арендой!")

            bot.answer_callback_query(call.id)

    except Exception as e:
        print(f"Ошибка 11485: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def handle_main_menu_inline(call):
    try:
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
    except Exception as e:
        print(f"Ошибка 11506: {e}")


def send_profile_info(user_telegram_id, chat_id):
    try:
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
                SELECT b.car_id, c.brand_model, c.year, c.transmission, c.price,
                       b.service, b.date, b.time
                FROM bookings b
                JOIN cars c ON b.car_id = c.car_id
                WHERE b.user_id = ? AND b.status = 'process'
                ORDER BY b.created_at DESC
                LIMIT 1
            ''', (user_telegram_id,))
        booking = cursor.fetchone()

        if booking:
            car_id, brand_model, year, trans, base_price, service, date, time = booking
            rent_start = date
            rent_end = date  # временно

            # 🔹 добавляем переменные по умолчанию
            start_time = None
            end_time = None

            # Если это долгосрочная аренда — берём rent_end
            if service == "rental":
                cursor.execute('''
                        SELECT rent_start, rent_end, start_time, end_time 
                        FROM rental_history
                        WHERE user_id = ? AND car_id = ?
                        ORDER BY id DESC LIMIT 1
                    ''', (user_telegram_id, car_id))
                rent_info = cursor.fetchone()
                if rent_info:
                    rent_start, rent_end, start_time, end_time = rent_info

            # --- расчёт дней аренды ---
            days = 1
            try:
                days = (datetime.strptime(rent_end, "%Y-%m-%d") - datetime.strptime(rent_start, "%Y-%m-%d")).days
                days = max(days, 1)
            except Exception as e:
                print(f"[send_profile_info] Ошибка при подсчёте дней: {e}")

            # --- расчёт цены ---
            total_price = calculate_price(base_price, days)
            price_line = f"\n💰 <b>Стоимость:</b> {total_price:,} ₽ за {days} дней" if total_price else ""

            if service == "rent":
                date_line = f"📆 Дата начала: {rent_start}"
            else:
                date_line = f"📆 Срок: {rent_start} - {rent_end}"

            # --- формируем время ---
            start_time_line = ""
            if start_time:
                try:
                    start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                    start_time_line = f"🕒 Время начала: {start_dt.strftime('%Y-%m-%d %H:%M')}"
                except:
                    start_time_line = f"🕒 Время начала: {start_time}"

            end_time_line = ""
            if end_time:
                try:
                    end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                    end_time_line = f"🕒 Время окончания: {end_dt.strftime('%Y-%m-%d %H:%M')}"
                except:
                    end_time_line = f"🕒 Время окончания: {end_time}"

            text = (
                f"<b>Условия аренды:</b>\n"
                f"{date_line}\n"
                f"{start_time_line}\n"
                f"{end_time_line}\n\n"
                f"<b>Характеристики автомобиля:</b>\n"
                f"🚘 {brand_model} ({year})\n"
                f"🕹 Коробка: {trans}\n"
                f"{price_line}"
            )

            bot.send_message(chat_id, text, parse_mode="HTML")
        else:
            bot.send_message(chat_id, "❌ Вы пока не арендуете машину.")

        conn.close()
    except Exception as e:
        print(f"Ошибка 11608: {e}")


def send_help_menu(message):
    try:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("🔧 Ремонт", callback_data="help_repair"),
            types.InlineKeyboardButton("🫧 Записаться на мойку", callback_data="help_wash"),
            types.InlineKeyboardButton("⚠️ ДТП", callback_data="help_accident"),
            types.InlineKeyboardButton("❓ Задать админу вопрос", callback_data="help_question"),
        )
        bot.send_message(message.chat.id, "🛠Выберите вариант помощи:", reply_markup=kb)
    except Exception as e:
        print(f"Ошибка 11622: {e}")


temp_data = {}


@bot.message_handler(commands=['clear_rental_history'])
def clear_rental_history(message):
    if message.from_user.id != ADMIN_ID2:
        bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
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
    try:
        chat_id = call.message.chat.id

        # 1. Сообщение с телефоном
        bot.send_message(chat_id, "📞 Телефон экстренной помощи: +79023738833")

        # 2. Кнопка с инструкцией
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📹 Как правильно снять видео", callback_data="accident_video_guide"))

        bot.send_message(chat_id, "Если ты попал в ДТП, пожалуйста, ознакомься с инструкцией ниже:", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка 11662: {e}")


# 3. Обработка кнопки-инструкции
@bot.callback_query_handler(func=lambda call: call.data == "accident_video_guide")
def handle_video_guide(call):
    try:
        chat_id = call.message.chat.id

        # Инструкция действий при ДТП
        accident_text = (
            "🚨 *Инструкция действий клиента при ДТП:*\n\n"
            "1️⃣ Не перемещайте автомобиль и предметы, имеющие отношение к происшествию.\n"
            "2️⃣ Включите аварийную сигнализацию и установите знак аварийной остановки.\n"
            "3️⃣ Позвоните 112 и потребуйте соединения с местным ГИБДД.\n"
            "4️⃣ *Важно:* откажитесь от европротокола — вы арендуете авто, оформление должно быть через ГИБДД.\n"
            "5️⃣ Сфотографируйте и снимите на видео:\n"
            "— Повреждения автомобилей\n— Номера машин\n— Расположение ТС на дороге\n— Дорожные знаки и разметку\n"
            "6️⃣ Свяжитесь с нашим менеджером и отправьте видео/фото. Желательно не менее 10 фото.\n"
            "7️⃣ При оформлении ДТП: сфотографируйте объяснение, документы ГИБДД и передайте их при сдаче авто.\n"
            "8️⃣ Убедитесь, что все повреждения зафиксированы и нет ошибок в документах.\n"
            "9️⃣ Если будет разбор — обязательно присутствуйте и получите все итоговые документы.\n"
            "🔟 *Если было освидетельствование — предоставьте акт.* Его отсутствие может повлиять на страховое решение.\n\n"
            "⚠️ Отказ от медицинского освидетельствования = опьянение = полная материальная ответственность.\n"
            "⚠️ Неисполнение этой инструкции ведёт к возмещению ущерба арендатором в полном объёме."
        )

        bot.send_message(chat_id, accident_text, parse_mode="Markdown")

        # Инструкция по съёмке
        video_instruction = (
            "📹 *Инструкция по съёмке места ДТП:*\n\n"
            "1. Снимите общую сцену с разных сторон.\n"
            "2. Покажите номера автомобилей.\n"
            "3. Запишите повреждения крупным планом.\n"
            "4. Зафиксируйте дорожные знаки, разметку, перекрестки.\n"
            "5. Видео должно быть *чётким, без пауз и лишних разговоров*.\n\n"
            "🎥 После съёмки — отправьте видео прямо сюда."
        )

        bot.send_message(chat_id, video_instruction, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка 11704: {e}")


@bot.message_handler(content_types=['video'])
def handle_video(message):
    try:
        user_id = message.from_user.id

        # Подключение к базе данных
        conn = sqlite3.connect(DB_PATH)  # Укажи правильный путь к БД
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
    except Exception as e:
        print(f"Ошибка 11746: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "help_repair")
def show_repair_options(call):
    try:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("📅 Записаться на ремонт", callback_data="repair_book"),
            types.InlineKeyboardButton("📞 Связаться с механиком", callback_data="repair_contact"),
            types.InlineKeyboardButton("📘 Инструкция по уходу за авто", callback_data="repair_guide"),
            types.InlineKeyboardButton("🛠 Сообщить о поломке", callback_data="report_breakdown")
        )
        bot.edit_message_text("🔧 Выберите опцию ремонта:", chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except Exception as e:
        print(f"Ошибка 11761: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "repair_guide")
def send_repair_guide(call):
    try:
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

    except Exception as e:
        print(f"Ошибка 11813: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "repair_contact")
def send_mechanic_contact(call):
    try:

        bot.send_message(call.message.chat.id,
                     "📞 Позвоните механику по номеру: +79278933702")
    except Exception as e:
        print(f"Ошибка 11822: {e}")

def get_last_confirmed_car_id(user_id):
    try:

        cursor.execute('''
        SELECT b.car_id, c.brand_model, c.year, c.transmission
        FROM bookings b
        JOIN cars c ON b.car_id = c.car_id
        WHERE b.user_id = ? AND b.status = 'process'
        ORDER BY b.created_at DESC
        LIMIT 1
    ''', (user_id,))
        return cursor.fetchone()  # вернёт (car_id, brand_model, year, transmission) или None
    except Exception as e:
        print(f"Ошибка 11837: {e}")

def send_time_selection(chat_id, service, car_id, date_str):
    try:
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

    except Exception as e:
        print(f"Ошибка 11860: {e}")

def get_booked_times(date_str):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
                SELECT time FROM bookings
                WHERE date = ? AND status = 'confirmed'
            """, (date_str,))
        booked_times = set(t[0] for t in c.fetchall())
        conn.close()
        return booked_times
    except Exception as e:
        print(f"Ошибка 11874: {e}")


def get_repair_booked_dates_and_times():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT date, time FROM repair_bookings")
        booked_dates_and_times = cursor.fetchall()
        conn.close()
        return booked_dates_and_times
    except Exception as e:
        print(f"Ошибка 11886: {e}")


def get_connection():
    try:

        # timeout=10 даёт время ждать, если база занята
        return sqlite3.connect(DB_PATH, timeout=10)
    except Exception as e:
        print(f"Ошибка 11895: {e}")

def execute_query(query, params=(), fetchone=False, commit=False):
    try:
        with db_lock:
            with sqlite3.connect(DB_PATH, timeout=10) as conn:
                c = conn.cursor()
                c.execute(query, params)
                if commit:
                    conn.commit()
                if fetchone:
                    return c.fetchone()
                return c.fetchall()

    except Exception as e:
        print(f"Ошибка 11910: {e}")


REPORT_ID_COUNTER = 1  # глобальный счётчик заявок

# ---------- Сообщение о поломке ----------
BREAKDOWN_RESPONSES = {
    "issue_not_starting": "🔋 Пожалуйста, проверьте, что автомобиль в 'P' и тормоз зажат. Механик уже уведомлён.",
    "issue_flat_tire": "🛞 Понял, спасибо! Мы свяжемся с вами и заменим колесо при первой возможности.",
    "issue_noise": "🛠️ Спасибо, мы зафиксировали жалобу. Наши специалисты проверят автомобиль.",
    "issue_brakes": "🚫 Это серьёзно. Пожалуйста, не продолжайте движение. Механик будет направлен к вам.",
    "issue_ac": "💨 Уведомили техслужбу. Кондиционер будет проверен при следующем ТО.",
    "issue_check_engine": "⚙️ Спасибо. Индикатор ошибки записан. Мы свяжемся с вами при необходимости.",
    "issue_other": "🧾 Спасибо за сообщение! Мы свяжемся с вами для уточнения деталей."
}

# ---------- Сообщение о поломке ----------
@bot.callback_query_handler(func=lambda call: call.data == "report_breakdown")
def report_breakdown(call):
    try:
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

        bot.edit_message_text(
            "🚨 Выберите проблему с автомобилем:",
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )

    except Exception as e:
        print(f"Ошибка report_breakdown: {e}")

# ---------- Клиент выбрал конкретную поломку ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("issue_"))
def handle_issue_choice(call):

    try:
        global REPORT_ID_COUNTER
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        issue_key = call.data

        # Достаем телефон пользователя
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT phone FROM users WHERE telegram_id = ?", (user_id,))
        phone_row = cursor.fetchone()
        phone = phone_row[0] if phone_row else "неизвестно"

        if issue_key == "issue_other":
            # переводим пользователя в режим ввода своей проблемы
            user_states[user_id] = "waiting_custom_issue"
            bot.send_message(chat_id, "✍️ Пожалуйста, опишите проблему словами:")
            conn.close()
            return

        # Описание проблемы для админов
        human_text = {
            "issue_not_starting": "Машина не заводится",
            "issue_flat_tire": "Пробито колесо",
            "issue_noise": "Странный шум",
            "issue_brakes": "Не работают тормоза",
            "issue_ac": "Кондиционер не работает",
            "issue_check_engine": "Check Engine / Ошибка на панели"
        }.get(issue_key, "Проблема зафиксирована.")

        # Отправляем пользователю дружеский текст
        bot.send_message(chat_id, BREAKDOWN_RESPONSES[issue_key])

        # Создаём запись в памяти (можно заменить записью в БД)
        report_id = REPORT_ID_COUNTER
        REPORT_ID_COUNTER += 1
        admin_report_messages[report_id] = {
            "taken_by": None,
            "messages": {},
            "human_text": human_text,
            "user_id": user_id,
            "phone": phone
        }

        conn.close()

        # Уведомляем админов
        notify_admins_breakdown(user_id, phone, human_text, report_id)

    except Exception as e:
        print(f"Ошибка handle_issue_choice: {e}")

# ---------- Обработка текста "Другое" ----------
@bot.message_handler(func=lambda m: user_states.get(m.chat.id) == "waiting_custom_issue")
def handle_custom_issue(message):

    try:
        global REPORT_ID_COUNTER
        user_id = message.from_user.id
        chat_id = message.chat.id
        description = message.text.strip()

        if len(description) < 5:
            bot.send_message(chat_id, "⚠️ Опишите проблему чуть подробнее (не меньше 5 символов).")
            return

        user_states.pop(user_id, None)  # сбрасываем состояние
        bot.send_message(chat_id, "✅ Спасибо! Мы зафиксировали вашу проблему.")

        # достаём телефон
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT phone FROM users WHERE telegram_id = ?", (user_id,))
        phone_row = cursor.fetchone()
        phone = phone_row[0] if phone_row else "неизвестно"
        conn.close()

        report_id = REPORT_ID_COUNTER
        REPORT_ID_COUNTER += 1
        admin_report_messages[report_id] = {
            "taken_by": None,
            "messages": {},
            "human_text": description,
            "user_id": user_id,
            "phone": phone
        }

        # уведомляем админов
        notify_admins_breakdown(user_id, phone, description, report_id)

    except Exception as e:
        print(f"Ошибка handle_custom_issue: {e}")

# ---------- Функция уведомления админов ----------
def notify_admins_breakdown(user_id, phone, human_text, report_id):
    try:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("🛠️ Я отвечу", callback_data=f"take_report_{report_id}"))

        msg_text = (
            f"🚨 <b>Новая поломка!</b>\n\n"
            f"👤 Пользователь ID: {user_id}\n"
            f"📞 Телефон: {phone}\n"
            f"⚠️ Проблема: {human_text}"
        )

        for admin in ADMINS:
            sent = bot.send_message(admin, msg_text, parse_mode="HTML", reply_markup=keyboard)
            admin_report_messages[report_id]["messages"][admin] = sent.message_id

    except Exception as e:
        print(f"Ошибка notify_admins_breakdown: {e}")

# ---------- Админ взял заявку ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith("take_report_"))
def handle_take_report(call):
    try:
        report_id = int(call.data.split("_")[-1])
        admin_id = call.from_user.id

        report = admin_report_messages.get(report_id)
        if not report:
            bot.answer_callback_query(call.id, "❌ Заявка не найдена.")
            return

        if report["taken_by"]:
            bot.answer_callback_query(call.id, "Уже занят другим админом.")
            # обновляем сообщение для других админов
            for admin, msg_id in report["messages"].items():
                if admin != report["taken_by"]:
                    bot.edit_message_text(
                        f"👤 Пользователь ID: {report['user_id']}\n"
                        f"📞 Телефон: {report['phone']}\n"
                        f"⚠️ Другой админ уже занимается клиентом.\n"
                        f"Проблема: {report['human_text']}",
                        chat_id=admin,
                        message_id=msg_id
                    )
            return

        report["taken_by"] = admin_id

        # обновляем сообщения у всех админов
        for admin, msg_id in report["messages"].items():
            if admin == admin_id:
                bot.edit_message_text(
                    "✅ Вы взяли заявку на обработку.",
                    chat_id=admin,
                    message_id=msg_id
                )
            else:
                bot.edit_message_text(
                    f"👤 Пользователь ID: {report['user_id']}\n"
                    f"📞 Телефон: {report['phone']}\n"
                    f"⚠️ Другой админ уже занимается клиентом.\n"
                    f"Проблема: {report['human_text']}",
                    chat_id=admin,
                    message_id=msg_id
                )

        bot.answer_callback_query(call.id, "Заявка закреплена за вами.")

    except Exception as e:
        print(f"Ошибка handle_take_report: {e}")
@bot.callback_query_handler(func=lambda call: call.data == "repair_book")
def handle_repair_book(call):
    try:

        user_id = call.from_user.id
        chat_id = call.message.chat.id
        bot.answer_callback_query(call.id)
        start_repair_request(user_id, chat_id, call.message)  # Передаем call.message для register_next_step_handler
    except Exception as e:
        print(f"Ошибка 12045: {e}")

def start_repair_request(user_id, chat_id, message):
    try:
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
            reply_markup=markup)
        bot.register_next_step_handler(message, get_repair_date)
    except Exception as e:
        print(f"Ошибка 12079: {e}")


def get_repair_date(message):
    try:
        date_raw = message.text.strip()
        parsed = parse_russian_date(date_raw)
        if not parsed:
            bot.send_message(message.chat.id, "❌ Неверный формат даты. Пожалуйста, выберите дату с клавиатуры.")
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_repair_date)
            return

        # Убираем клавиатуру после выбора
        bot.send_message(
            message.chat.id,
            f"📅 Вы выбрали дату: {date_raw}",
            reply_markup=types.ReplyKeyboardRemove()
        )

        date_str = parsed.strftime('%Y-%m-%d')
        if message.chat.id not in temp_data:
            temp_data[message.chat.id] = {}
        temp_data[message.chat.id]['date'] = date_str
        car_id = temp_data[message.chat.id]['car_id']

        service = 'repair'

        if not sending_time_selection(message.chat.id, service, car_id, date_str):
            bot.send_message(message.chat.id, "⛔ Нет доступных времён на этот день. Попробуйте выбрать другую дату.")
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_repair_date)
    except Exception as e:
        print(f"Ошибка 12110: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('chosen_time'))
def callback_select_time(call):
    try:
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
                                       callback_data=f"repair_approve_{car_id}_{user_id_db}_{encoded_date}_{encoded_time}"),
            types.InlineKeyboardButton("🕒 Предложить другое время",
                                       callback_data=f"repair_suggest_{car_id}_{user_id_db}"),
        )
        markup.add(
            types.InlineKeyboardButton("❌ Отклонить",
                                       callback_data=f"repair_reject_{car_id}_{user_id_db}_{encoded_date}_{encoded_time}"),
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
    except Exception as e:
        print(f"Ошибка 12186: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("repair_approve_"))
def process_repair_approve(call):
    try:
        full_data = call.data[len("repair_approve_"):]
        parts = full_data.split("_")
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
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
        try:
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None
            )
        except telebot.apihelper.ApiTelegramException as e:
            if "message is not modified" not in str(e):
                raise
        bot.answer_callback_query(call.id, "Заявка подтверждена.")

    except Exception as e:
        error_text = f"Ошибка подтверждения: {e}"
        if len(error_text) > 200:
            error_text = error_text[:197] + "..."
        bot.answer_callback_query(call.id, error_text)
        print(f"❌ Ошибка в process_repair_approve: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("repair_suggest_") and
                                              not call.data.startswith("repair_suggest_time_") and
                                              not call.data.startswith("repair_select_date_"))
def process_repair_suggest(call):
    try:
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

        # Сохраняем в сессию
        session = get_session(user_id) or {}
        session['repair_suggest_car_id'] = car_id
        session['repair_suggest_user_id'] = user_id
        session['repair_suggest_date'] = None
        save_session(user_id, session)

        # ⬅ Вот это нужно, чтобы ловить сообщение с датой
        repair_selected_suggest[call.message.chat.id] = (car_id, user_id)

        bot.answer_callback_query(call.id)
        show_repair_admin_date_calendar(call.message)
    except Exception as e:
        print(f"Ошибка 12294: {e}")


def show_repair_admin_date_calendar(message):
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        booked_dates_and_times = get_booked_dates_and_times_repair()
        booked_dates = {date for date, _ in booked_dates_and_times}

        today = datetime.today()
        buttons = []

        for i in range(30):
            day = today + timedelta(days=i)
            day_num = day.day
            month_name = list(MONTHS_RU_GEN.keys())[day.month - 1]
            button_text = f"{day_num} {month_name}"
            buttons.append(types.KeyboardButton(button_text))

        for i in range(0, len(buttons), 3):
            markup.row(*buttons[i:i + 3])

        markup.add(types.KeyboardButton("🔙 Отмена"))

        bot.send_message(message.chat.id, "📅 Выберите дату для предложения клиенту:", reply_markup=markup)

    except Exception as e:
        print(f"Ошибка 12321: {e}")

@bot.message_handler(func=lambda message: message.chat.id in repair_selected_suggest)
def handle_repair_suggest_date_choice(message):
    try:
        admin_id = message.from_user.id
        car_id, target_user_id = repair_selected_suggest.get(message.chat.id, (None, None))
        if not car_id:
            bot.send_message(message.chat.id, "❌ Данные не найдены.")
            return

        MONTHS_RU = {
            "янв": 1, "января": 1,
            "фев": 2, "февраля": 2,
            "мар": 3, "марта": 3,
            "апр": 4, "апреля": 4,
            "май": 5, "мая": 5,
            "июн": 6, "июня": 6,
            "июл": 7, "июля": 7,
            "авг": 8, "августа": 8,
            "сен": 9, "сентября": 9,
            "окт": 10, "октября": 10,
            "ноя": 11, "ноября": 11,
            "дек": 12, "декабря": 12
        }

        try:
            now = datetime.now()
            parts = message.text.strip().lower().split()
            if len(parts) != 2:
                raise ValueError("Wrong format")
            day = int(parts[0])
            month = MONTHS_RU.get(parts[1])
            if not month:
                raise ValueError("Unknown month")

            chosen_date = datetime(year=now.year, month=month, day=day)
            if chosen_date.date() < now.date():
                chosen_date = chosen_date.replace(year=now.year + 1)

            date_str = chosen_date.strftime("%Y-%m-%d")
        except ValueError:
            bot.send_message(message.chat.id, "❌ Неверный формат даты. Пример: 10 авг")
            return

        session['repair_suggest_date'] = date_str
        save_session(admin_id, session)

        car_id, target_user_id = repair_selected_suggest.pop(message.chat.id, (None, None))
        if not car_id or not target_user_id:
            bot.send_message(message.chat.id, "❌ Не удалось найти данные для продолжения.")
            return
        bot.send_message(
            message.chat.id,
            f"📅 Вы выбрали дату: {message.text}. Теперь выберите время:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        show_repair_admin_suggest_calendar(message, car_id, target_user_id, date_str)


    except Exception as e:
        print(f"Ошибка 12382: {e}")
def show_repair_admin_suggest_calendar(message, car_id, user_id, date_str):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT time FROM repair_bookings WHERE car_id=? AND date=? AND status='confirmed'", (car_id, date_str))
        booked_times = [row[0] for row in c.fetchall()]
        conn.close()

        keyboard = types.InlineKeyboardMarkup(row_width=3)
        for hour in range(10, 19):
            for minute in range(0, 60, 30):  # каждые 10 минут
                time_str = f"{hour:02}:{minute:02}"
                if time_str in booked_times:
                    btn = types.InlineKeyboardButton(f"⛔ {time_str}", callback_data="busy")
                else:
                    btn = types.InlineKeyboardButton(time_str,
                                                     callback_data=f"repair_suggest_time_{car_id}_{user_id}_{date_str}_{time_str}")
                keyboard.add(btn)

        bot.send_message(message.chat.id, f"Выберите время для ремонта:", reply_markup=keyboard)
    except Exception as e:
        print(f"Ошибка 12404: {e}")


@bot.message_handler(func=lambda message: message.chat.id in repair_selected_suggest)
def handle_repair_suggest_date_choice(message):
    try:
        bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message.message_id,
            reply_markup=None
        )
        MONTHS_RU = {
            "янв": 1, "января": 1,
            "фев": 2, "февраля": 2,
            "мар": 3, "марта": 3,
            "апр": 4, "апреля": 4,
            "май": 5, "мая": 5,
            "июн": 6, "июня": 6,
            "июл": 7, "июля": 7,
            "авг": 8, "августа": 8,
            "сен": 9, "сентября": 9,
            "окт": 10, "октября": 10,
            "ноя": 11, "ноября": 11,
            "дек": 12, "декабря": 12
        }

        text = message.text.strip()

        # Отмена
        if text == "🔙 Отмена":
            bot.send_message(
                message.chat.id,
                "Отменено.",
                reply_markup=types.ReplyKeyboardRemove()  # убрать обычные кнопки
            )
            repair_selected_suggest.pop(message.chat.id, None)
            return

        # Парсинг даты
        try:
            now = datetime.now()
            parts = text.lower().split()
            if len(parts) != 2:
                raise ValueError

            day = int(parts[0])
            month = MONTHS_RU.get(parts[1])
            if not month:
                raise ValueError

            chosen_date = datetime(year=now.year, month=month, day=day)
            if chosen_date.date() < now.date():
                chosen_date = chosen_date.replace(year=now.year + 1)

            date_str = chosen_date.strftime("%Y-%m-%d")
        except ValueError:
            bot.send_message(message.chat.id, "❌ Неверный формат даты. Пожалуйста, выберите дату с клавиатуры.")
            return

        # Получаем данные из словаря
        car_id, user_id = repair_selected_suggest.pop(message.chat.id, (None, None))
        if not car_id:
            bot.send_message(message.chat.id, "❌ Данные не найдены.")
            return

        # Убираем обычные кнопки после выбора даты
        bot.send_message(
            message.chat.id,
            f"📅 Дата выбрана: {text}. Теперь выберите время:",
            reply_markup=types.ReplyKeyboardRemove()
        )

        # Сохраняем в сессию
        session = get_session(user_id)
        session["repair_suggest_date"] = date_str
        save_session(user_id, session)

        # Показ времени
        show_repair_time_selection(message, car_id, user_id, date_str)
    except Exception as e:
        print(f"Ошибка 12484: {e}")


def show_repair_time_selection(message, car_id, user_id, date_str):
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT time FROM repair_bookings 
                WHERE car_id=? AND date=? AND status='confirmed'
            """, (car_id, date_str))
            booked_times = [row[0] for row in c.fetchall()]

        keyboard = types.InlineKeyboardMarkup(row_width=3)
        for hour in range(10, 19):
            for minute in range(0, 60, 30):  # каждые 10 минут
                time_str = f"{hour:02}:{minute:02}"
                if time_str in booked_times:
                    btn = types.InlineKeyboardButton(f"⛔ {time_str}", callback_data="busy")
                else:
                    btn = types.InlineKeyboardButton(
                        time_str,
                        callback_data=f"repair_suggest_time_{car_id}_{user_id}_{date_str}_{time_str}"
                    )
                keyboard.add(btn)

        bot.send_message(message.chat.id, "Выберите время для ремонта:", reply_markup=keyboard)
    except Exception as e:
        print(f"Ошибка 12512: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("repair_suggest_time_"))
def process_repair_time_selection(call):
    # Убираем inline-кнопки из сообщения
    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=None
    )

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
            with sqlite3.connect(DB_PATH, timeout=10) as conn:
                c = conn.cursor()
                c.execute("SELECT telegram_id FROM users WHERE id = ?", (telegram_id,))
                result = c.fetchone()
                if not result:
                    bot.send_message(call.message.chat.id, "❌ Не найден пользователь.")
                    return

                user_id = result[0]
                service = 'repair'

                c.execute("""
                    INSERT INTO repair_bookings (user_id, car_id, service, date, time, status)
                    VALUES (?, ?, ?, ?, ?, 'suggested')
                """, (user_id, car_id, service, date_str, time_str))
                conn.commit()

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            "OK",
            callback_data=f"repair_ok_{service}_{car_id}_{user_id}_{date_str}_{time_str}"
        ))

        bot.send_message(
            user_id,
            f"📩 Администратор предлагает: {date_str} в {time_str}\nЕсли согласны, нажмите кнопку ниже.",
            reply_markup=markup
        )
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
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
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


@bot.message_handler(
    func=lambda message: message.from_user and message.from_user.id in globals().get("repair_reject_reasons", {}))
def handle_repair_rejection_reason(message):
    try:
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
    try:
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
    except Exception as e:
        print(f"Ошибка 12765: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "help_wash")
def handle_help_wash(call):
    try:
        user_id = call.from_user.id
        session = get_session(user_id)

        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📅 Выберите дату:", reply_markup=create_date_markup_wash())

        session.clear()
        set_state(user_id, "carwash_waiting_for_date")
    except Exception as e:
        print(f"Ошибка 12780: {e}")


@bot.message_handler(func=lambda msg: get_state(msg.from_user.id) == "carwash_waiting_for_date")
def handle_carwash_date(message):
    try:
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
    except Exception as e:
        print(f"Ошибка 12807: {e}")


@bot.message_handler(func=lambda msg: get_state(msg.from_user.id) == "carwash_waiting_for_time")
def handle_carwash_time(message):
    try:
        user_id = message.from_user.id
        session = get_session(user_id)

        selected_date = session.get("selected_date")
        selected_time = message.text.strip()
        call_sign = session.get("driver_call_sign", "Без имени")

        if selected_date:
            add_booking_wash(user_id, selected_date, selected_time, call_sign)
            bot.send_message(message.chat.id, f"✅ Вы записаны на мойку {selected_date} в {selected_time}.",
                             reply_markup=clear_keyboard())
        else:
            bot.send_message(message.chat.id, "❌ Ошибка: дата не выбрана.")

        user_sessions.pop(user_id, None)  # очищаем сессию после записи
    except Exception as e:
        print(f"Ошибка 12829: {e}")


# ==== Функция добавления записи ====
def add_booking_wash(user_id, date, time, name):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
                INSERT INTO bookings_wash (user_id, name, date, time, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, name or "Без имени", date, time, "confirmed"))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка 12844: {e}")


def has_available_slots(date_str):
    try:
        booked = get_booked_dates_and_times_wash()
        time_slots = [f"{h:02d}:{m:02d}" for h in range(10, 19) for m in range(0, 60, 30)]

        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

        for slot in time_slots:
            slot_time = datetime.strptime(slot, "%H:%M").time()

            if (date_str, slot) not in booked:
                if date_obj > datetime.today().date():
                    return True
                elif date_obj == datetime.today().date() and slot_time > datetime.now().time():
                    return True
        return False
    except Exception as e:
        print(f"Ошибка 12864: {e}")


def create_date_markup_wash():
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        today = datetime.today().date()

        for i in range(0, 30):  # Следующие 14 дней
            date = today + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')

            if has_available_slots(date_str):
                # Формируем вид даты как "21 июля"
                day = date.day
                month_name = list(MONTHS_RU_GEN.keys())[date.month - 1]
                readable = f"{day} {month_name}"
                markup.add(types.KeyboardButton(readable))

        return markup
    except Exception as e:
        print(f"Ошибка 12885: {e}")


# ==== Клавиатура времени ====
def create_time_markup(selected_date: str):
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
        booked = get_booked_dates_and_times_wash()

        # Преобразуем дату
        selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
        now = datetime.now()

        # Временные слоты с 9:00 до 19:30
        time_slots = [f"{h:02d}:{m:02d}" for h in range(10, 19) for m in range(0, 60, 30)]

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
    except Exception as e:
        print(f"Ошибка 12917: {e}")


# ==== Проверка занятых слотов ====
def get_booked_dates_and_times_wash():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT date, time FROM bookings_wash WHERE status = 'confirmed'")
        booked = c.fetchall()
        conn.close()
        return set(booked)
    except Exception as e:
        print(f"Ошибка 12930: {e}")


def send_booking_reminder():
    if not notify_lock.acquire(blocking=False):
        print("[notify_admin] Пропуск — функция уже работает.")
        return

    start_time = datetime.now()
    try:

        print(f"[notify_admin] Запуск в {start_time}")

        check_upcoming_washing()
        check_broken_cars_and_notify()
    except Exception as e:
        print(f"[notify_admin] ❌ Ошибка верхнего уровня: {e}")
    finally:
        notify_lock.release()
        print(f"[notify_admin] Завершено за {datetime.now() - start_time}")


def check_upcoming_washing():
    now = datetime.now()
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Выбираем все подтвержденные и ожидающие мойки
        cursor.execute(
            "SELECT id, user_id, date, time, status, notified FROM bookings_wash WHERE status IN ('confirmed', 'pending')")
        bookings = cursor.fetchall()

        for booking in bookings:
            booking_id = booking["id"]
            user_id = booking["user_id"]
            date = booking["date"]
            time_ = booking["time"]
            status = booking["status"]
            notified = bookings["notified"]
            booking_time = datetime.strptime(f"{date} {time_}", "%Y-%m-%d %H:%M")
            seconds_until = (booking_time - now).total_seconds()
            seconds_after = (now - booking_time).total_seconds()

            # Напоминание за 1 час до мойки (только для pending)
            if 0 < seconds_until <= 3600 and notified == 0:
                bot.send_message(user_id, f"🔔 Напоминание: через 1 час мойка на {date} в {time_}.")
                cursor.execute("UPDATE bookings_wash SET status = 'confirmed' WHERE id = ?", (booking_id,))
                cursor.execute("UPDATE bookings_wash SET notified = 1 WHERE id = ?", (booking_id,))
                conn.commit()



            # Сообщение о завершении сразу после времени
            elif 0 <= seconds_after <= 1800:  # до 30 минут после
                bot.send_message(user_id, f"✅ Ваша мойка на {date} в {time_} завершена.")
                cursor.execute("UPDATE bookings_wash SET status = 'completed' WHERE id = ?", (booking_id,))
                conn.commit()

    finally:
        conn.close()
        # --- Обработка напоминаний о сдаче авто ---
        # cursor.execute("""
        #     SELECT h.id, h.user_id, h.rent_end, u.telegram_id
        #     FROM rental_history h
        #     JOIN users u ON h.user_id = u.id
        # """)
        # rentals = cursor.fetchall()
        #
        # for rental in rentals:
        #     rent_end_str = rental["rent_end"]
        #     telegram_id = rental["telegram_id"]
        #
        #     try:
        #         rent_end = datetime.strptime(rent_end_str, "%Y-%m-%d %H:%M")
        #     except ValueError:
        #         rent_end = datetime.strptime(rent_end_str, "%Y-%m-%d")
        #         rent_end = rent_end.replace(hour=23, minute=59)  # или любое разумное значение
        #
        #     # Напоминание за 1 сутки
        #     notify_day_before = rent_end - timedelta(days=1)
        #     if notify_day_before.strftime("%Y-%m-%d %H:%M") == now_str:
        #         bot.send_message(telegram_id,
        #                          f"📅 Напоминание: завтра вы должны сдать автомобиль в {rent_end.strftime('%H:%M')}.")
        #
        #     # Напоминание в 08:00 утра в день сдачи
        #     notify_morning = rent_end.replace(hour=8, minute=0)
        #     if notify_morning.strftime("%Y-%m-%d %H:%M") == now_str:
        #         bot.send_message(telegram_id,
        #                          f"🚗 Сегодня сдача автомобиля в {rent_end.strftime('%H:%M')} — не забудьте сообщить администратору!")


@bot.callback_query_handler(func=lambda c: c.data.startswith("help_question"))
def handle_unknown_messages(call):
    try:

        bot.send_message(call.message.chat.id, "Задавай вопрос")
        bot.register_next_step_handler(call.message, question_function)
    except Exception as e:
        print(f"Ошибка 13029: {e}")

@bot.message_handler(commands=["rental_history"])
def rental_history(message):
    telegram_id = message.from_user.id

    try:
        with sqlite3.connect(DB_PATH) as conn:
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


@bot.message_handler(
    func=lambda message: get_state(message.from_user.id) and get_state(message.from_user.id).startswith(
        "waiting_for_time_pick|"))
def handle_time_pick(message):
    try:
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
    except Exception as e:
        print(f"Ошибка 12122: {e}")


from apscheduler.schedulers.background import BackgroundScheduler


@bot.message_handler(commands=['admin'])
def admin_panel(message):
    try:
        if message.from_user.id not in ADMIN_IDS:
            return bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📋 Заявки", callback_data="admin_bookings"))
        markup.add(types.InlineKeyboardButton("👤 Пользователи", callback_data="admin_users"))
        markup.add(types.InlineKeyboardButton("🧼 Мойки", callback_data="admin_wash"))
        markup.add(types.InlineKeyboardButton(" 🚗 Машины", callback_data="admin_avtopark"))
        markup.add(types.InlineKeyboardButton("❓ Вопросы", callback_data="admin_questions"))
        if message.from_user.id == DIRECTOR_ID:
            markup.add(types.InlineKeyboardButton("Операторы", callback_data="admin_operators"))
            markup.add(types.InlineKeyboardButton("📊 Смены", callback_data="admin_shifts"))
            markup.add(types.InlineKeyboardButton("⛽ Заправки", callback_data="admin_gas"))

        bot.send_message(message.chat.id, "🛠 Админ-панель", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка 13145: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "admin_questions")
def handle_admin_questions(call):
    try:
        bot.answer_callback_query(call.id)

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                    SELECT * FROM questions
                    ORDER BY id DESC
                """)
            questions = cursor.fetchall()

            if not questions:
                bot.send_message(call.message.chat.id, "❓ Вопросов нет.")
                return

            for q in questions:
                answered_status = "✅ Отвечено" if q["answered"] else "⏳ Не отвечено"
                answer_text = q["answer_text"] if q["answer_text"] else "—"

                text = (
                    f"❓ <b>Вопрос #{q['id']}</b>\n"
                    f"👤 Пользователь: @{q['username']} (ID: {q['user_id']})\n"
                    f"💬 Вопрос: {q['question_text']}\n"
                    f"📝 Ответ: {answer_text}\n"
                    f"📌 Статус: {answered_status}"
                )

                bot.send_message(call.message.chat.id, text, parse_mode="HTML")

    except Exception as e:
        print(f"Ошибка 13182: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "admin_gas")
def handle_admin_gas(call):
    try:
        bot.answer_callback_query(call.id)

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT 
                    h."№",
                    h."Дата",
                    h."Адрес",
                    h."Топливо",
                    h."Рубли",
                    h."Литры",
                    h."Оплата",
                    u.phone
                FROM history h
                LEFT JOIN users u ON h."Telegram_ID" = u.telegram_id
                WHERE DATE(h."Дата") = DATE('now', 'localtime')
                ORDER BY h."Дата" DESC
            """)
            records = cursor.fetchall()

            if not records:
                bot.send_message(call.message.chat.id, "⛽ Заправок нет.")
                return

            for record in records:
                # перевод станции в адрес
                address = STATION_NAMES.get(record['Адрес'], record['Адрес'])

                text = (
                    f"⛽ <b>Заправка №{record['№']}</b>\n"
                    f"📅 Дата: {record['Дата']}\n"
                    f"🏢 Адрес: {address}\n"
                    f"⛽ Топливо: {record['Топливо']}\n"
                    f"💵 Рубли: {record['Рубли']}\n"
                    f"🧪 Литры: {record['Литры']}\n"
                    f"💳 Оплата: {record['Оплата']}\n"
                    f"📱 Телефон: {record['phone'] or 'не указан'}"
                )
                bot.send_message(call.message.chat.id, text, parse_mode="HTML")

    except Exception as e:
        print(f"Ошибка 13220: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "admin_wash")
def handle_admin_wash(call):
    try:
        bot.answer_callback_query(call.id)

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                    SELECT b.*, u.name as user_name, u.phone
                    FROM bookings_wash b
                    JOIN users u ON b.user_id = u.telegram_id
                    ORDER BY b.date DESC, b.time DESC
                """)
            bookings = cursor.fetchall()

            if not bookings:
                bot.send_message(call.message.chat.id, "🧼 Заявок на мойку нет.")
                return

            for booking in bookings:
                status = STATUS_MAP.get(booking["status"], booking["status"])
                text = (
                    f"🧼 <b>Заявка на мойку #{booking['id']}</b>\n"
                    f"👤 Клиент: {booking['user_name']} ({booking['phone']})\n"
                    f"📅 Дата: {booking['date']} {booking['time']}\n"
                    f"🚗 Название услуги: {booking['name']}"
                )
                bot.send_message(call.message.chat.id, text, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка 13260: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "admin_shifts")
def handle_admin_shifts(call):
    try:
        bot.answer_callback_query(call.id)

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                    SELECT s.*, o.name as operator_name 
                    FROM shifts s
                    LEFT JOIN operators o ON s.operator_id = o.id
                    ORDER BY s.id DESC
                """)
            shifts = cursor.fetchall()

            if not shifts:
                bot.send_message(call.message.chat.id, "📊 Смен нет.")
                return

            for shift in shifts:
                # Перевод станции в адрес
                station_key = shift["station"].replace(" ", "_").lower()
                station_address = STATION_NAMES.get(station_key, shift["station"])

                active_status = "🟢 Активна" if shift["active"] else "🔴 Неактивна"

                text = (
                    f"🕒 <b>Смена #{shift['id']}</b>\n"
                    f"Оператор: {shift['operator_name'] or '—'}\n"
                    f"🏢 Станция: {station_address}\n"
                    f"⚡ Статус: {active_status}\n"
                    f"⛽ Заправка (бензин): {shift['gasoline_liters']} л\n"
                    f"⛽ Заправка (газ): {shift['gas_liters']} л\n"
                    f"💰 Продажи: {shift['sales_sum']} ₽\n"
                    f"🎁 Бонус: {shift['bonus_sum']}\n"
                    f"🚗 Машин продано: {shift['cars_sold']}\n"
                    f"💰 Сумма продажи машин: {shift['sold_sum']}\n"
                    f"🕘 Начало: {shift['start_time'] or '—'}\n"
                    f"🕘 Конец: {shift['end_time'] or '—'}"
                )

                bot.send_message(call.message.chat.id, text, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка 13308: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "admin_operators")
def handle_admin_operators(call):
    try:
        bot.answer_callback_query(call.id)

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM operators ORDER BY id DESC")
            operators = cursor.fetchall()

            if not operators:
                bot.send_message(call.message.chat.id, "Операторов нет.")
                return

            for op in operators:
                # Переводим station в адрес
                station_key = op["station"].replace(" ", "_").lower()  # например "station 1" -> "station_1"
                station_address = STATION_NAMES.get(station_key, op["station"])

                registered_status = "✅ Зарегистрирован" if op["registered"] else "❌ Не зарегистрирован"
                active_status = "🟢 Активен" if op["active"] else "🔴 Неактивен"

                text = (
                    f"<b>{op['name'] or '—'}</b>\n"
                    f"📞 Телефон: {op['phone'] or '—'}\n"
                    f"🏢 Станция: {station_address}\n"
                    f"🔑 PIN: {op['pin'] or '—'}\n"
                    f"📋 {registered_status}\n"
                    f"⚡ {active_status}"
                )

                # создаем клавиатуру с кнопкой "Удалить"
                keyboard = types.InlineKeyboardMarkup()
                delete_btn = types.InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=f"deleting_operator_{op['id']}"
                )
                keyboard.add(delete_btn)

                bot.send_message(call.message.chat.id, text, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        print(f"Ошибка 13346: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("deleting_operator_"))
def handle_delete_operator(call):
    try:
        operator_id = int(call.data.split("_")[-1])

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM operators WHERE id = ?", (operator_id,))
            conn.commit()

        bot.answer_callback_query(call.id, "Оператор удалён ✅")
        bot.edit_message_text(
            "Оператор был удалён.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )

    except Exception as e:
        print(f"Ошибка при удалении оператора: {e}")
        bot.answer_callback_query(call.id, "Ошибка при удалении ❌")

user_photos_messages = {}


# --- Обработчик кнопки "Пользователи" ---
@bot.callback_query_handler(func=lambda call: call.data == "admin_users")
def handle_admin_users(call):
    try:
        bot.answer_callback_query(call.id)

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY id DESC")
            users = cursor.fetchall()

            if not users:
                bot.send_message(call.message.chat.id, "👤 Пользователей нет.")
                return

            status_map = {
                "new": "Новичок",
                "waiting_car": "Скоро должен забрать авто/на оплате залога",
                "waiting_rental": "Ждёт время аренды",
                "using_car": "Использует машину"
            }
            purpose_map = {
                "taxi": "Под такси",
                "personal": "Личное пользование"
            }

            for user in users:
                status_rus = status_map.get(user["status"], user["status"])
                purpose_rus = purpose_map.get(user["purpose"], user["purpose"] or "—")

                text = (
                    f"👤 <b>{user['name'] or '—'}</b>\n"
                    f"📌 Полное имя: {user['full_name'] or '—'}\n"
                    f"📞 Телеграм: {user['telegram_id']}\n"
                    f"📱 Телефон: {user['phone'] or '—'}\n"
                    f"📄 Статус: {status_rus}\n"
                    f"🎯 Цель: {purpose_rus}\n"
                    f"⭐ Бонусы: {user['bonus'] or 0}"
                )

                kb = types.InlineKeyboardMarkup()
                kb.add(
                    types.InlineKeyboardButton(
                        text="📎 Документы",
                        callback_data=f"user_docs_{user['id']}"
                    ),
                    types.InlineKeyboardButton(
                        text="⛽ Заправки",
                        callback_data=f"user_gas_{user['telegram_id']}"
                    )
                )

                bot.send_message(call.message.chat.id, text, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        print(f"Ошибка 13405: {e}")

# --- Обработчик кнопки "Документы" ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("user_gas_"))
def handle_user_gas(call):
    try:
        bot.answer_callback_query(call.id)
        telegram_id = call.data.replace("user_gas_", "")

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    h."№",
                    h."Дата",
                    h."Адрес",
                    h."Топливо",
                    h."Рубли",
                    h."Литры",
                    h."Оплата"
                FROM history h
                WHERE h."Telegram_ID" = ?
                ORDER BY h."Дата" DESC
            """, (telegram_id,))
            records = cursor.fetchall()

            if not records:
                bot.send_message(call.message.chat.id, "⛽ У этого пользователя заправок нет.")
                return

            for record in records:
                address = STATION_NAMES.get(record['Адрес'], record['Адрес'])
                text = (
                    f"⛽ <b>Заправка №{record['№']}</b>\n"
                    f"📅 Дата: {record['Дата']}\n"
                    f"🏢 Адрес: {address}\n"
                    f"⛽ Топливо: {record['Топливо']}\n"
                    f"💵 Рубли: {record['Рубли']}\n"
                    f"🧪 Литры: {record['Литры']}\n"
                    f"💳 Оплата: {record['Оплата']}"
                )
                bot.send_message(call.message.chat.id, text, parse_mode="HTML")

    except Exception as e:
        print(f"Ошибка handle_user_gas: {e}")
@bot.callback_query_handler(func=lambda call: call.data.startswith("user_docs_"))
def handle_user_docs(call):
    try:
        user_id = int(call.data.split("_")[2])

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()

        if not user:
            bot.answer_callback_query(call.id, "Пользователь не найден.")
            return

        media = []
        try:
            if user["driver_license_photo"]:
                media.append(types.InputMediaPhoto(user["driver_license_photo"], caption="Водительское удостоверение"))
            if user["passport_front_photo"]:
                media.append(types.InputMediaPhoto(user["passport_front_photo"], caption="Паспорт (лицевая сторона)"))
            if user["passport_back_photo"]:
                media.append(types.InputMediaPhoto(user["passport_back_photo"], caption="Паспорт (обратная сторона)"))
        except Exception as e:
            bot.answer_callback_query(call.id, f"Ошибка загрузки фото: {e}")
            return

        if media:
            # Отправляем все фото одной группой
            sent_msgs = bot.send_media_group(call.message.chat.id, media)
            user_photos_messages[user_id] = [msg.message_id for msg in sent_msgs]

            # Добавляем кнопку "Скрыть фото"
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("Скрыть фото", callback_data=f"hiden_docs_{user_id}"))
            bot.send_message(call.message.chat.id, f"Документы пользователя {user['full_name'] or '—'}:", reply_markup=kb)
        else:
            bot.answer_callback_query(call.id, "Документы отсутствуют.")
    except Exception as e:
        print(f"Ошибка 13447: {e}")


# --- Обработчик кнопки "Скрыть фото" ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("hiden_docs_"))
def handle_hide_docs(call):
    try:
        user_id = int(call.data.split("_")[2])

        # Удаляем все сообщения с медиа
        if user_id in user_photos_messages:
            for msg_id in user_photos_messages[user_id]:
                try:
                    bot.delete_message(call.message.chat.id, msg_id)
                except:
                    pass
            del user_photos_messages[user_id]

        # Удаляем сообщение с кнопкой
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        bot.answer_callback_query(call.id, "Документы скрыты.")
    except Exception as e:
        print(f"Ошибка 13473: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "admin_bookings")
def handle_admin_bookings(call):
    try:
        bot.answer_callback_query(call.id)

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Получаем все заявки
            cursor.execute("""
                SELECT b.*, u.name as user_name, u.phone
                FROM bookings b
                JOIN users u ON b.user_id = u.telegram_id
                ORDER BY b.created_at DESC
            """)
            bookings = cursor.fetchall()

            if not bookings:
                bot.send_message(call.message.chat.id, "📋 Заявок нет.")
                return

            # Карты статусов
            status_map = {
                "pending": "В ожидании",
                "confirmed": "Подтверждена",
                "process": "В процессе",
                "completed": "Завершена"
            }
            deposit_map = {
                "paid": "Внесён",
                "unpaid": "Не внесён"
            }

            for booking in bookings:
                service = booking["service"]

                # Проверяем стандартные сервисы
                service_display = {
                    "rent": "аренда",
                    "rental": "прокат"
                }.get(service, None)

                # Если кастомная профессия — ищем в jobs
                if service_display is None:
                    cursor.execute("SELECT title FROM jobs WHERE profession = ?", (service,))
                    job = cursor.fetchone()
                    if job:
                        service_display = job["title"]
                    else:
                        service_display = service  # fallback

                status = status_map.get(booking["status"], booking["status"])
                deposit_status = deposit_map.get(booking["deposit_status"], booking["deposit_status"])

                text = (
                    f"📋 <b>Заявка #{booking['id']}</b>\n"
                    f"👤 Клиент: {booking['user_name']} ({booking['phone']})\n"
                    f"🚗 Услуга: {service_display}\n"
                    f"📅 Дата: {booking['date']} {booking['time']}\n"
                    f"📦 Статус: {status}\n"
                    f"💰 Залог: {deposit_status}\n"
                )

                # Если сервис rental — достаём доп.инфо из rental_history
                if booking["service"] == "rental":
                    cursor.execute("""
                        SELECT rent_start, rent_end, price
                        FROM rental_history
                        WHERE user_id = ? AND car_id = ?
                    """, (booking["user_id"], booking["car_id"]))
                    rental_info = cursor.fetchone()
                    if rental_info:
                        text += (
                            f"📆 Период аренды: {rental_info['rent_start']} → {rental_info['rent_end']}\n"
                            f"💵 Цена: {rental_info['price']} ₽\n"
                        )

                bot.send_message(call.message.chat.id, text, parse_mode="HTML")

    except Exception as e:
        print(f"Ошибка 13545: {e}")
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread
import signal
import time
import sys

scheduler = BackgroundScheduler()
import telebot
import openpyxl
import os


def access_check(func):
    def wrapper(message, *args, **kwargs):
        try:
            if message.from_user.id not in OPERATORS_IDS and message.from_user.id != ADMIN_ID:
                return bot.reply_to(message, "Нет доступа к боту.")
            return func(message, *args, **kwargs)
        except Exception as e:
            print(f"Ошибка 13567: {e}")

    return wrapper


# --- Команда админа для добавления оператора ---
@bot.message_handler(commands=['add_operator'])
def add_operator_step1(message):
    try:
        if message.from_user.id != ADMIN_ID2:
            return bot.reply_to(message, "Нет доступа.")
        bot.send_message(message.chat.id, "Введите имя оператора:")
        bot.register_next_step_handler(message, add_operator_step2)
    except Exception as e:
        print(f"Ошибка 13581: {e}")


# Шаг 2 — ввод имени
def add_operator_step2(message):
    try:
        name = message.text.strip()
        if not name:
            return bot.send_message(message.chat.id, "Имя не может быть пустым. Попробуйте снова.")

        bot.user_data = getattr(bot, "user_data", {})
        bot.user_data[message.chat.id] = {"name": name}

        bot.send_message(message.chat.id, "Введите номер телефона оператора:")
        bot.register_next_step_handler(message, add_operator_step_phone)
    except Exception as e:
        print(f"Ошибка 13597: {e}")


# Новый шаг — ввод телефона
def normalize_phone(phone: str) -> str | None:
    # Оставляем только цифры
    digits = "".join(filter(str.isdigit, phone))

    if not digits:
        return None

    # Если начинается с 8 → заменяем на +7
    if digits.startswith("8") and len(digits) == 11:
        return "+7" + digits[1:]

    # Если уже начинается с 7 и длина 11 → ставим +
    if digits.startswith("7") and len(digits) == 11:
        return "+" + digits

    # Если уже в формате +7 (12 символов с плюсом)
    if phone.startswith("+7") and len(digits) == 11:
        return "+7" + digits[1:]

    # Если не подходит под форматы РФ → возвращаем None
    return None


def add_operator_step_phone(message):
    try:
        phone_raw = message.text.strip()
        phone = normalize_phone(phone_raw)

        if not phone:
            return bot.send_message(
                message.chat.id,
                "⚠️ Введите корректный номер телефона в формате 8XXXXXXXXXX или +7XXXXXXXXXX."
            )

        bot.user_data[message.chat.id]["phone"] = phone

        # Показываем список адресов станций
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for address in STATION_CODES_TO_ADDRESSES.values():
            markup.add(address)

        bot.send_message(message.chat.id, f"Телефон сохранён: {phone}\n\nВыберите станцию:", reply_markup=markup)
        bot.register_next_step_handler(message, add_operator_step3)

    except Exception as e:
        print(f"Ошибка 13616: {e}")

# Шаг 3 — выбор станции и сохранение в БД
def add_operator_step3(message):
    try:
        address = message.text.strip()

        station_code = None
        for code, addr in STATION_CODES_TO_ADDRESSES.items():
            if addr == address:
                station_code = code
                break

        if not station_code:
            return bot.send_message(message.chat.id, "Неверный адрес. Попробуйте снова.")

        user_data = bot.user_data.get(message.chat.id, {})
        name = user_data.get("name")
        phone = user_data.get("phone")

        if not name or not phone:
            return bot.send_message(message.chat.id, "Ошибка: данные оператора не найдены. Начните заново.")

        cursor.execute(
            "INSERT INTO operators (name, phone, station) VALUES (?, ?, ?)",
            (name, phone, station_code)
        )
        conn.commit()

        bot.send_message(
            message.chat.id,
            f"✅ Оператор '{name}' с телефоном '{phone}' добавлен на станцию '{address}'.",
            reply_markup=types.ReplyKeyboardRemove()
        )

        bot.user_data.pop(message.chat.id, None)
    except Exception as e:
        print(f"Ошибка 13654: {e}")


# --- Выбор имени ---
user_password_wait = {}


@bot.message_handler(
    func=lambda m: m.text in [row[0] for row in cursor.execute("SELECT name FROM operators").fetchall()])
@access_check
def choose_operator(message):
    try:
        name = message.text.strip()
        cursor.execute("SELECT id, registered FROM operators WHERE name=?", (name,))
        op = cursor.fetchone()
        if not op:
            return bot.send_message(message.chat.id, "Оператор не найден.")

        op_id, registered = op
        if not registered:
            bot.send_message(message.chat.id, "Придумайте 4-значный пароль:")
            bot.register_next_step_handler(message, set_pin, op_id)
        else:
            user_password_wait[message.chat.id] = op_id
            bot.send_message(message.chat.id, "Введите пароль:")
    except Exception as e:
        print(f"Ошибка 13680: {e}")


@bot.message_handler(func=lambda m: m.chat.id in user_password_wait)
def check_password(message):
    try:
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение: {e}")

        if message.text == "/cancel":
            user_password_wait.pop(message.chat.id, None)
            bot.send_message(message.chat.id, "Ввод пароля отменён.")
            start(message)
            return

        op_id = user_password_wait.pop(message.chat.id, None)
        if not op_id:
            bot.send_message(message.chat.id, "Сессия входа устарела. Выберите оператора заново.")
            return

        pin = message.text.strip()
        cursor.execute("SELECT pin FROM operators WHERE id=?", (op_id,))
        row = cursor.fetchone()
        correct_pin = row[0] if row else None

        if pin == correct_pin:
            bot.send_message(message.chat.id, "Пароль верный. Добро пожаловать!")
            show_operator_menu(message, op_id)
        else:
            bot.send_message(message.chat.id, "Неверный пароль. Попробуйте снова или выберите оператора заново.")
    except Exception as e:
        print(f"Ошибка 13713: {e}")
    # Сначала удаляем сообщение с паролем


def set_pin(message, op_id):
    try:
        pin = message.text.strip()
        if not (pin.isdigit() and len(pin) == 4):
            return bot.send_message(message.chat.id, "Пароль должен быть из 4 цифр.")
        cursor.execute("UPDATE operators SET pin=?, registered=1 WHERE id=?", (pin, op_id))
        conn.commit()
        bot.send_message(message.chat.id, "Регистрация завершена.")
        show_operator_menu(message, op_id)
    except Exception as e:
        print(f"Ошибка 13727: {e}")


def show_operator_menu(message, op_id):
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cursor.execute("SELECT 1 FROM shifts WHERE operator_id=? AND active=1", (op_id,))
        markup.add("Начать смену")
        markup.add("Назад")
        bot.send_message(message.chat.id, "Меню:", reply_markup=markup)
        bot.register_next_step_handler(message, handle_menu, op_id)
    except Exception as e:
        print(f"Ошибка 13739: {e}")


def handle_menu(message, op_id):
    try:
        actions = {
            "Начать смену": start_shift,
            "Закончить смену": end_shift,
            "Назад": start
        }
        action = actions.get(message.text)
        if action:
            if message.text == "Назад":
                action(message)
            else:
                action(message, op_id)
        else:
            bot.send_message(message.chat.id, "Неизвестная команда.")
            show_operator_menu(message, op_id)
    except Exception as e:
        print(f"Ошибка 13759: {e}")


def request_input(message, prompt, callback, op_id):
    try:

        bot.send_message(message.chat.id, prompt)
        bot.register_next_step_handler(message, callback, op_id)
    except Exception as e:
        print(f"Ошибка 13768: {e}")

def start_shift(message, op_id):
    try:
        # Получаем код станции и имя оператора
        cursor.execute("SELECT station, name FROM operators WHERE id=?", (op_id,))
        result = cursor.fetchone()
        if not result:
            bot.send_message(message.chat.id, "Ошибка: оператор не найден.")
            return
        station_code, operator_name = result
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Вставляем новую запись в shifts с именем оператора
        cursor.execute("""
                INSERT INTO shifts (operator_id, station, active, start_time)
                VALUES (?, ?, 1, ?)
            """, (op_id, station_code, start_time))

        # Обновляем статус оператора в таблице operators на active = 1
        cursor.execute("""
                UPDATE operators SET active=1 WHERE id=?
            """, (op_id,))

        conn.commit()

        # Отправляем сообщение с удалением клавиатуры
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "Смена успешно начата.", reply_markup=markup)
    except Exception as e:
        print(f"Ошибка 13798: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("end_shift:"))
def handle_end_shift_callback(call):
    try:
        op_id = int(call.data.split(":")[1])
        end_shift(call.message, op_id)
        bot.answer_callback_query(call.id, "Смена завершена!")
    except Exception as e:
        print(f"Ошибка 13808: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("operator_choose:"))
def handle_choose_operator_callback(call):
    try:
        op_id = int(call.data.split(":")[1])
        # Здесь вызывай логику выбора оператора — например, запрос пароля или сразу меню
        # Например:
        cursor.execute("SELECT registered FROM operators WHERE id=?", (op_id,))
        registered = cursor.fetchone()[0]
        if not registered:
            bot.send_message(call.message.chat.id, "Придумайте 4-значный пароль:")
            bot.register_next_step_handler(call.message, set_pin, op_id)
        else:
            user_password_wait[call.message.chat.id] = op_id
            bot.send_message(call.message.chat.id, "Введите пароль:")
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Ошибка 13826: {e}")


def end_shift(message, op_id):
    import sqlite3
    from datetime import datetime
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Получаем смену
            cursor.execute("""
                    SELECT gasoline_liters, gas_liters, sales_sum, bonus_sum, cars_sold, start_time, station
                    FROM shifts WHERE operator_id=? AND active=1
                """, (op_id,))
            shift = cursor.fetchone()

            if not shift:
                bot.send_message(message.chat.id, "Нет активной смены.")
                return show_operator_menu(message, op_id)

            gasoline, gas, sales_sum, bonus_sum, cars_sold, start_time, station_code = shift
            end_time = datetime.now().strftime("%Y-%m-%d %H:%M")

            # --- Проверка заправок ---
            # Получаем адрес станции
            station_address = STATION_CODES_TO_ADDRESSES.get(station_code, "Неизвестно")
            print(station_address, start_time, end_time)
            # Ищем заправки на этой станции за время смены
            cursor.execute("""
                    SELECT "Telegram_ID"
                    FROM history
                    WHERE "Адрес" = ?
                      AND datetime("Дата") BETWEEN datetime(?) AND datetime(?)
                """, (station_code, start_time, end_time))

            fuel_records = cursor.fetchall()
            print(fuel_records)
            # Считаем количество заправок по каждому клиенту
            from collections import Counter
            counts = Counter([row["Telegram_ID"] for row in fuel_records])

            # Получаем данные оператора
            cursor.execute("SELECT name, phone FROM operators WHERE id=?", (op_id,))
            op_info = cursor.fetchone()
            operator_name = op_info["name"] if op_info else "Неизвестно"
            operator_phone = op_info["phone"] if op_info else "Неизвестно"

            # Проверяем превышение
            for telegram_id, count in counts.items():
                if count > 2:  # больше 2 заправок
                    # Имя пользователя
                    cursor.execute("SELECT name FROM users WHERE telegram_id=?", (telegram_id,))
                    user_name = cursor.fetchone()
                    user_name = user_name["name"] if user_name else "Неизвестный клиент"

                    bot.send_message(
                        ADMIN_ID2,
                        f"⚠️ Внимание!\n"
                        f"Клиент *{user_name}* ({telegram_id}) заправлялся {count} раз(а) "
                        f"на станции *{station_address}* во время смены.\n"
                        f"Оператор: {operator_name}, Телефон: {operator_phone}",
                        parse_mode="Markdown"
                    )

            # --- Закрываем смену ---
            cursor.execute("""
                    UPDATE shifts SET active=0, end_time=? WHERE operator_id=? AND active=1
                """, (end_time, op_id))

            cursor.execute("""
                    UPDATE operators SET active=0 WHERE id=?
                """, (op_id,))

            conn.commit()

        bot.send_message(message.chat.id, f"""Смена завершена.
        Начало: {start_time}
        Конец: {end_time}
        Бензин: {gasoline} л
        Газ: {gas} л
        Сумма продаж: {sales_sum} руб
        Сумма продажи: {bonus_sum} бонусов
        Продано машин: {cars_sold}""")
    except Exception as e:
        print(f"Ошибка 13912: {e}")




@bot.callback_query_handler(func=lambda call: call.data.startswith("deleting_job_"))
def delete_job(call):
    try:
        if call.from_user.id != DIRECTOR_ID:
            return bot.answer_callback_query(call.id, "⛔ Нет доступа")

        job_id = int(call.data.split("_")[-1])

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        conn.commit()
        conn.close()

        bot.answer_callback_query(call.id, "✅ Вакансия удалена")
        admin_manage_jobs(call)  # Обновляем список
    except Exception as e:
        print(f"[ERROR] Ошибка 14894: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "add_job")
def add_job_start(call):
    try:
        if call.from_user.id != DIRECTOR_ID:
            return

        user_sessions[call.from_user.id] = {"jobs_add_step": "title"}
        bot.send_message(call.message.chat.id, "✏ Введите название вакансии:")
    except Exception as e:
        print(f"[ERROR] Ошибка 14905: {e}")

@bot.message_handler(func=lambda m: user_sessions.get(m.from_user.id, {}).get("jobs_add_step") == "title")
def add_job_title(message):
    try:
        user_sessions[message.from_user.id]["title"] = message.text
        user_sessions[message.from_user.id]["jobs_add_step"] = "profession"
        bot.send_message(message.chat.id, "✏ Введите английское название профессии:")
    except Exception as e:
        print(f"[ERROR] Ошибка 14914: {e}")
@bot.message_handler(func=lambda m: user_sessions.get(m.from_user.id, {}).get("jobs_add_step") == "profession")
def add_job_profession(message):
    try:
        user_sessions[message.from_user.id]["profession"] = message.text
        user_sessions[message.from_user.id]["jobs_add_step"] = "description"
        bot.send_message(message.chat.id, "✏ Введите описание вакансии:")
    except Exception as e:
        print(f"[ERROR] Ошибка 14922: {e}")
@bot.message_handler(func=lambda m: user_sessions.get(m.from_user.id, {}).get("jobs_add_step") == "description")
def add_job_description(message):
    try:
        data = user_sessions[message.from_user.id]
        title, profession, description = data["title"], data["profession"], message.text

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO jobs (title, profession, description) VALUES (?, ?, ?)",
                       (title, profession, description))
        conn.commit()
        conn.close()

        bot.send_message(message.chat.id, f"✅ Вакансия '{title}' добавлена!")
        user_sessions.pop(message.from_user.id, None)
    except Exception as e:
        print(f"[ERROR] Ошибка 14939: {e}")

@bot.message_handler(commands=['clear_all'])
def clear_all_tables(message):
    try:
        if message.from_user.id != DAN_TELEGRAM_ID:
            return bot.send_message(message.chat.id, "⛔ У вас нет доступа к этой команде.")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        tables = [
            "users", "fuel", "bookings_taxi", "jobs", "history",
            "bookings", "repair_bookings", "bookings_wash", "cars",
            "rental_history", "questions", "feedback", "operators", "shifts"
        ]

        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
            # для sqlite можно сбросить счетчик AUTOINCREMENT
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")

        conn.commit()
        conn.close()

        bot.send_message(message.chat.id, "✅ Все таблицы успешно очищены.")
    except Exception as e:
        print(f"Ошибка очистки таблиц: {e}")
        bot.send_message(message.chat.id, f"❌ Ошибка при очистке таблиц: {e}")


def shutdown_scheduler(signum, frame):
    print("🛑 Останавливаем scheduler...")
    if scheduler.running:
        scheduler.shutdown(wait=False)
    sys.exit(0)

def run_flask():
    app.run(host="0.0.0.0", port=10000)

def start_scheduler():
    try:
        if not scheduler.get_job('notify_admin_job'):
            scheduler.add_job(notify_admin, 'interval', minutes=1, id='notify_admin_job')
        if not scheduler.get_job('reminder_job'):
            scheduler.add_job(send_booking_reminder, 'interval', seconds=70, id='reminder_job')

        if not scheduler.get_job('rental_pickup_notification'):
            scheduler.add_job(send_pickup_notifications, 'cron', hour=8, minute=0, id='rental_pickup_notification')
        if not scheduler.get_job('rental_late_pickup_notification'):
            scheduler.add_job(send_late_pickup_notifications, 'cron', hour=12, minute=0,
                              id='rental_late_pickup_notification')

        if not scheduler.get_job('rental_force_start_notification'):
            scheduler.add_job(force_start_rental, 'cron', hour=20, minute=0, id='rental_force_start_notification')
        if not scheduler.running:
            scheduler.start()
        print("✅ Scheduler запущен")
    except Exception as e:
        print(f"Ошибка при запуске scheduler: {e}")


def main():
    bot.remove_webhook()

    signal.signal(signal.SIGINT, shutdown_scheduler)
    signal.signal(signal.SIGTERM, shutdown_scheduler)

    # Запуск Flask в отдельном потоке
    Thread(target=run_flask, daemon=True).start()

    # Настройка и запуск scheduler
    start_scheduler()

    # Настройка БД и бот
    setup_tables()
    print("✅ Бот запущен")

    # Основной polling
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            print(f"❌ Ошибка polling: {e}")
            time.sleep(5)

# === Точка входа ===
if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(f"🔥 Критическая ошибка: {e}. Перезапуск через 5 секунд")
            time.sleep(5)
