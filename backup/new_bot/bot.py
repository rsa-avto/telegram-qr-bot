<<<<<<< HEAD
import telebot
import uuid
import sqlite3
import socket
from telebot import types
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

DB_PATH = "cars.db"
BASE_URL = "192.168.1.182"  # IP/домен, где работает Flask

user_sessions = {}

# 🔹 Получение локального IP
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# 🔹 Команда для входа на сайт
@bot.message_handler(commands=["site"])
def send_site_link(message):
    telegram_id = message.from_user.id

    # Проверяем наличие пользователя
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT telegram_id FROM users WHERE telegram_id IS NOT NULL")
    rows = cur.fetchall()

    for row in rows:
        print(row[0])
    cur.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cur.fetchone()
    if not user:
        bot.send_message(message.chat.id, "❌ Вы не зарегистрированы")
        conn.close()
        return
    user_id = user[0]

    # Создаём токен для входа
    token = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO login_tokens (token, user_id) VALUES (?, ?)",
        (token, user_id)
    )
    conn.commit()
    conn.close()

    link = f"http://{BASE_URL}:10001/login?telegram_id={telegram_id}"
    bot.send_message(message.chat.id, f"🌐 Войти в личный кабинет:\n{link}")


# 🔹 Обработка выбора станции
@bot.callback_query_handler(func=lambda call: call.data.startswith("station_"))
def handle_station(call):
    chat_id = call.message.chat.id
    station_code = call.data.split("_")[1]

    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}
    user_sessions[chat_id]['station'] = station_code

    markup = types.InlineKeyboardMarkup()
    for fuel in ["Бензин", "Дизель", "Газ"]:
        markup.add(types.InlineKeyboardButton(fuel, callback_data=f"fuel_{fuel}"))

    bot.send_message(chat_id, f"Вы выбрали станцию {station_code}. Выберите тип топлива:", reply_markup=markup)


# 🔹 Обработка выбора топлива
@bot.callback_query_handler(func=lambda call: call.data.startswith("fuel_"))
def handle_fuel(call):
    chat_id = call.message.chat.id
    fuel_type = call.data.split("_")[1]

    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}
    user_sessions[chat_id]['fuel'] = fuel_type

    markup = types.InlineKeyboardMarkup()
    for amount in [500, 1000, 1500, 2000]:
        markup.add(types.InlineKeyboardButton(f"{amount} руб.", callback_data=f"sum_{amount}"))

    bot.send_message(chat_id, f"Вы выбрали {fuel_type}. Выберите сумму:", reply_markup=markup)


# 🔹 Обработка выбора суммы
@bot.callback_query_handler(func=lambda call: call.data.startswith("sum_"))
def handle_sum(call):
    chat_id = call.message.chat.id
    amount = int(call.data.split("_")[1])

    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}
    user_sessions[chat_id]['amount'] = amount

    session_data = user_sessions[chat_id]
    station = session_data.get("station", "не выбрано")
    fuel = session_data.get("fuel", "не выбрано")

    bot.send_message(chat_id, f"✅ Вы выбрали:\nСтанция: {station}\nТопливо: {fuel}\nСумма: {amount} руб.")


# 🔹 Запуск polling
if __name__ == "__main__":
    print("🤖 Бот запущен")
    bot.infinity_polling()
=======
import telebot
import uuid
import sqlite3
import socket
from telebot import types

BOT_TOKEN = "6419852337:AAHQGZagCRReSMWwCEFdX5BVEn7IZHEbxVk"
bot = telebot.TeleBot(BOT_TOKEN)

DB_PATH = "cars.db"
BASE_URL = "192.168.1.182"  # IP/домен, где работает Flask

user_sessions = {}

# 🔹 Получение локального IP
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# 🔹 Команда для входа на сайт
@bot.message_handler(commands=["site"])
def send_site_link(message):
    telegram_id = message.from_user.id

    # Проверяем наличие пользователя
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT telegram_id FROM users WHERE telegram_id IS NOT NULL")
    rows = cur.fetchall()

    for row in rows:
        print(row[0])
    cur.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cur.fetchone()
    if not user:
        bot.send_message(message.chat.id, "❌ Вы не зарегистрированы")
        conn.close()
        return
    user_id = user[0]

    # Создаём токен для входа
    token = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO login_tokens (token, user_id) VALUES (?, ?)",
        (token, user_id)
    )
    conn.commit()
    conn.close()

    link = f"http://{BASE_URL}:10000/login?telegram_id={telegram_id}"
    bot.send_message(message.chat.id, f"🌐 Войти в личный кабинет:\n{link}")


# 🔹 Обработка выбора станции
@bot.callback_query_handler(func=lambda call: call.data.startswith("station_"))
def handle_station(call):
    chat_id = call.message.chat.id
    station_code = call.data.split("_")[1]

    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}
    user_sessions[chat_id]['station'] = station_code

    markup = types.InlineKeyboardMarkup()
    for fuel in ["Бензин", "Дизель", "Газ"]:
        markup.add(types.InlineKeyboardButton(fuel, callback_data=f"fuel_{fuel}"))

    bot.send_message(chat_id, f"Вы выбрали станцию {station_code}. Выберите тип топлива:", reply_markup=markup)


# 🔹 Обработка выбора топлива
@bot.callback_query_handler(func=lambda call: call.data.startswith("fuel_"))
def handle_fuel(call):
    chat_id = call.message.chat.id
    fuel_type = call.data.split("_")[1]

    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}
    user_sessions[chat_id]['fuel'] = fuel_type

    markup = types.InlineKeyboardMarkup()
    for amount in [500, 1000, 1500, 2000]:
        markup.add(types.InlineKeyboardButton(f"{amount} руб.", callback_data=f"sum_{amount}"))

    bot.send_message(chat_id, f"Вы выбрали {fuel_type}. Выберите сумму:", reply_markup=markup)


# 🔹 Обработка выбора суммы
@bot.callback_query_handler(func=lambda call: call.data.startswith("sum_"))
def handle_sum(call):
    chat_id = call.message.chat.id
    amount = int(call.data.split("_")[1])

    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}
    user_sessions[chat_id]['amount'] = amount

    session_data = user_sessions[chat_id]
    station = session_data.get("station", "не выбрано")
    fuel = session_data.get("fuel", "не выбрано")

    bot.send_message(chat_id, f"✅ Вы выбрали:\nСтанция: {station}\nТопливо: {fuel}\nСумма: {amount} руб.")


# 🔹 Запуск polling
if __name__ == "__main__":
    print("🤖 Бот запущен")
    bot.infinity_polling()
>>>>>>> 155af79 (fix: мои правки)
