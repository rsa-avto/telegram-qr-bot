import time
import signal
import sys
from threading import Thread
import os
import sqlite3
from app_2_0 import app
from bot import bot

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Путь к БД
if os.name == "nt":  # Windows
    DB_PATH = os.path.join(BASE_DIR, "cars.db")
else:  # Linux / Docker
    DB_PATH = "/app/cars.db"

# Подключение к БД
def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")  # включаем поддержку внешних ключей
    conn.row_factory = sqlite3.Row
    return conn

def get_db():
    return sqlite3.connect(DB_PATH)

# Создание таблиц
def setup_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

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
            purpose TEXT,
            is_admin INTEGER DEFAULT 0
        )
    ''')


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_tokens (
            token TEXT PRIMARY KEY,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            "Telegram_ID" INTEGER,
            points REAL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            shift_id INTEGER
        )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        points REAL DEFAULT 0,
        fuel TEXT,
        litres REAL,
        amount_rub REAL,
        seen INTEGER DEFAULT 0,
        order_id INTEGER,
        type TEXT,
        payment_method TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            name TEXT,
            phone TEXT,
            station TEXT,
            pin TEXT,
            registered INTEGER DEFAULT 0,
            active INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fuel (
        fuel_type TEXT PRIMARY KEY,
        price_per_litre REAL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operator_id INTEGER,
        station TEXT,
        active INTEGER DEFAULT 1,
        start_time TEXT,
        end_time TEXT
        )
        ''')

    conn.commit()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fuel_bonus (
            fuel_type TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            points_per_litre REAL DEFAULT 0,
            PRIMARY KEY (fuel_type, payment_method))''')


    cursor.execute('''
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
    ''')

    conn.commit()
    conn.close()

# Корректное завершение работы
def shutdown_scheduler(signum, frame):
    print("🛑 Останавливаем Flask и Telegram-бота...")
    sys.exit(0)

# Запуск Flask
def run_flask():
    app.run(
        host="0.0.0.0",
        port=10001,
        debug=True,
        use_reloader=False,
        threaded=True
    )

# Главная функция
def main():
    bot.remove_webhook()
    signal.signal(signal.SIGINT, shutdown_scheduler)
    signal.signal(signal.SIGTERM, shutdown_scheduler)

    # Запуск Flask в отдельном потоке
    Thread(target=run_flask, daemon=True).start()
    print("✅ Flask запущен")

    # Запуск Telegram-бота
    print("🤖 Telegram-бот запущен")
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            print(f"❌ Ошибка polling: {e}")
            time.sleep(5)

if __name__ == "__main__":
    setup_tables()  # создаём таблицы
    main()