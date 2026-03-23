
from flask import Flask, session, redirect, request, render_template, flash
import sqlite3
import os
from flask import send_file
import pandas as pd
import io
from flask import Response, stream_with_context
import time
import sqlite3
import json
import openpyxl
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "cars_new.db")

STATION_NAMES = {
    "station_1": "Южное шоссе 129",
    "station_2": "Южное шоссе 12/2",
    "station_3": "Лесная 66А",
    "station_4": "Борковская 72/1"

}
#755909251
STATION_OPERATORS = {
    "Южное шоссе 129": 755909251,
    "Южное шоссе 12/2": 8766687678,
    "Лесная 66А": 31313131231,
    "Борковская 72/1": 4674574545
}
ADMIN_IDS = [5035760364]  # Сюда вставить ID админа Telegram


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


from datetime import datetime, timezone, timedelta

def samara_now():
    """Возвращает текущее время в Самарском часовом поясе (UTC+4)"""
    samara_tz = timezone(timedelta(hours=4))
    return datetime.now(samara_tz).strftime("%Y-%m-%d %H:%M:%S")


#-----------ВХОД В СИСТЕМУ----------------



@app.route("/")
def index():
    if "user_id" in session:
        return redirect("/dashboard")
    return "🌐 Войдите через Telegram (/login?telegram_id=YOUR_TELEGRAM_ID)"


@app.route("/login")
def login():
    telegram_id = request.args.get("telegram_id")
    if not telegram_id:
        return "❌ Telegram ID не указан", 400

    telegram_id_int = int(telegram_id)

    # Проверка активных смен по базе (можно оставить)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM shifts WHERE active = 1 LIMIT 1")
    active_shift = cur.fetchone()
    if active_shift:
        print("✅ Есть активные смены")
    else:
        print("❌ Нет активных смен")

    # Проверяем обычного пользователя
    cur.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id_int,))
    user = cur.fetchone()

    # Проверка оператора через словарь STATION_OPERATORS
    operator_station = None
    for station_name, op_id in STATION_OPERATORS.items():
        if op_id == telegram_id_int:
            operator_station = station_name
            break

    if not user and not operator_station:
        conn.close()
        return "❌ Нет доступа", 403

    session["telegram_id"] = telegram_id_int
    session["is_admin"] = telegram_id_int in ADMIN_IDS

    if operator_station:
        # Оператор найден
        session["pending_operator"] = telegram_id_int
        session["station"] = operator_station  # сохраняем станцию оператора
        conn.close()
        return redirect("/operator/login")

    # Обычный пользователь
    session["role"] = "user"
    session["user_id"] = user["id"] if user else None

    conn.close()
    return redirect("/dashboard")

@app.route("/operator/login", methods=["GET", "POST"])
def operator_login():
    telegram_id = session.get("pending_operator")
    if not telegram_id:
        return redirect("/")

    if request.args.get("reset"):
        session.pop("selected_operator_id", None)
        return redirect("/operator/login")

    conn = get_db()
    cur = conn.cursor()

    # Находим станцию
    station_id = None
    station_name = None
    for sid, name in STATION_NAMES.items():
        if STATION_OPERATORS.get(name) == telegram_id:
            station_id = sid
            station_name = name
            break
    if not station_id:
        conn.close()
        return "❌ На этой станции нет операторов"

    # Получаем операторов станции
    cur.execute("SELECT id, name, station, pin FROM operators WHERE station=?", (station_id,))
    operators = cur.fetchall()

    selected_id = session.get("selected_operator_id")
    selected_operator = None
    if selected_id:
        for op in operators:
            if op['id'] == int(selected_id):
                # создаём копию словаря, чтобы можно было менять PIN локально
                selected_operator = dict(op)
                break
        if not selected_operator:
            session.pop("selected_operator_id", None)
            return redirect("/operator/login")

    error = None  # сообщение об ошибке

    if request.method == "POST":
        # Выбор оператора
        if not selected_operator:
            operator_id = request.form.get("operator_id")
            if not operator_id:
                error = "❌ Выберите оператора"
            else:
                session["selected_operator_id"] = operator_id
                return redirect("/operator/login")

        else:
            op = selected_operator

            # Если PIN ещё нет — создаём
            if not op["pin"] or str(op["pin"]).strip() == "":
                new_pin = request.form.get("new_pin", "").strip()
                if not new_pin.isdigit() or len(new_pin) != 4:
                    error = "❌ PIN должен быть 4 цифры"
                else:
                    cur.execute("UPDATE operators SET pin=? WHERE id=?", (new_pin, op['id']))
                    conn.commit()
                    # обновляем локально словарь
                    op['pin'] = new_pin
                    flash("✅ PIN создан, теперь войдите с этим PIN", "success")
                    return redirect("/operator/login")

            # Проверка существующего PIN
            else:
                pin = request.form.get("pin", "").strip()
                if str(op["pin"]).strip() != pin:
                    error = "❌ Неверный PIN"
                else:
                    # успешный вход
                    session.pop("pending_operator")
                    session.pop("selected_operator_id", None)
                    session["telegram_id"] = telegram_id
                    session["role"] = "operator"
                    session["operator_id"] = op["id"]
                    session["station"] = op["station"]
                    conn.close()
                    return redirect("/operator")

    conn.close()
    return render_template(
        "operator_login.html",
        operators=operators,
        selected_operator=selected_operator,
        station=station_name,
        error=error
    )
#---------------ПОЛЬЗОВАТЕЛЬСКИЙ БЛОК----------------------

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "telegram_id" not in session:
        return redirect("/")

    role = session.get("role")

    # 👉 ОПЕРАТОР
    if role == "operator":
        conn = get_db()
        cur = conn.cursor()
        # Берем все заявки на станции, последние 50, новые сверху
        cur.execute(
            "SELECT * FROM history WHERE Адрес = ? ORDER BY rowid DESC LIMIT 50",
            (session["station"],)
        )
        orders = cur.fetchall()
        conn.close()
        return render_template("operator_dashboard.html", orders=orders)

    # 👉 ОБЫЧНЫЙ пользователь
    fuels = ["Газ", "Бензин"]

    conn = get_db()
    cur = conn.cursor()

    # Получаем новые уведомления
    cur.execute("""
        SELECT * FROM notifications 
        WHERE telegram_id=? AND seen=0
        ORDER BY created_at DESC
    """, (session["telegram_id"],))
    notifications = cur.fetchall()

    # Помечаем уведомления как просмотренные
    cur.execute("UPDATE notifications SET seen=1 WHERE telegram_id=? AND seen=0", (session["telegram_id"],))
    conn.commit()
    conn.close()

    if request.method == "POST":
        station_code = request.form.get("station")
        station_name = STATION_NAMES.get(station_code, station_code)

        # Проверка активной смены
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM shifts WHERE station=? AND active=1", (station_code,))
        active_shift = cur.fetchone()
        if not active_shift:
            conn.close()
            flash(f"❌ На станции {station_name} нет активной смены. Заказ невозможен.", "error")
            return redirect("/dashboard")

        # Формируем заказ
        order = {
            "station": station_code,
            "fuel": request.form.get("fuel"),
            "amount_type": request.form.get("amount_type"),
            "amount": request.form.get("amount"),
            "full_tank": request.form.get("amount_type") == "full_tank"
        }
        session["current_order"] = order

        if order["full_tank"]:
            # Полный бак — сразу в history и на loading
            cur.execute("""
                INSERT INTO history (Адрес, Топливо, Telegram_ID, Оплата, status, Дата)
                VALUES (?, ?, ?, ?, 'pending_full_tank', ?)
            """, (station_code, order["fuel"], session["telegram_id"], "pending_full_tank", samara_now()))
            conn.commit()
            order_id = cur.lastrowid
            conn.close()
            flash(f"✅ Заказ на полный бак на станции {station_name} отправлен оператору.", "success")
            return redirect(f"/loading/{order_id}")
        else:
            # Обычный заказ — сначала подтверждение
            conn.close()
            return redirect("/confirm")

    return render_template(
        "dashboard.html",
        stations=STATION_NAMES,
        fuels=fuels,
        is_admin=session.get("is_admin", False),
        notifications=notifications
    )





@app.route("/operator/orders_json")
def operator_orders_json():
    if session.get("role") != "operator":
        return {"error": "no access"}, 403

    conn = get_db()
    cur = conn.cursor()

    # Обычные заказы
    cur.execute("""
        SELECT * FROM history
        WHERE status='pending' AND shift_id IS NULL AND Адрес=?
        ORDER BY rowid DESC
    """, (session["station"],))
    pending = cur.fetchall()

    # Заказы "полный бак"
    cur.execute("""
        SELECT * FROM history
        WHERE status='pending_full_tank' AND shift_id IS NULL AND Адрес=?
        ORDER BY rowid DESC
    """, (session["station"],))
    full_tank = cur.fetchall()

    conn.close()

    def serialize(rows):
        return [{
            "id": r["№"],
            "fuel": r["Топливо"],
            "litres": r["Литры"] or 0,
            "rub": r["Рубли"] or 0,
            "payment": r["Оплата"],
            "date": r["Дата"],
            "status": r["status"]
        } for r in rows]

    return {"orders": serialize(pending), "full_tank_orders": serialize(full_tank)}



@app.route("/confirm_full_tank", methods=["GET"])
def confirm_full_tank():
    if "user_id" not in session or "current_order" not in session:
        return redirect("/dashboard")

    order = session["current_order"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO history (Адрес, Топливо, Telegram_ID, Оплата, status) VALUES (?, ?, ?, ?, ?)",
        (order["station"], order["fuel"], session["telegram_id"], "pending_full_tank", "pending_full_tank")
    )
    conn.commit()
    conn.close()
    session.pop("current_order")
    flash("✅ Заказ отправлен оператору. Ожидайте подтверждения.", "success")
    return redirect("/dashboard")


@app.route("/loading/<int:order_id>")
def loading(order_id):
    if "telegram_id" not in session:
        return redirect("/dashboard")

    return render_template("loading.html", order_id=order_id)


@app.route("/confirm", methods=["GET", "POST"])
def confirm():
    if "user_id" not in session or "current_order" not in session:
        return redirect("/dashboard")

    order = session["current_order"]

    conn = get_db()
    cur = conn.cursor()

    # Получаем цену топлива
    cur.execute("SELECT price_per_litre FROM fuel WHERE fuel_type = ?", (order["fuel"],))
    row = cur.fetchone()
    price = row["price_per_litre"] if row else 0
    cur.execute("SELECT bonus FROM users WHERE telegram_id=?", (session["telegram_id"],))
    user = cur.fetchone()
    bonus = user["bonus"] if user else 0
    if request.method == "POST":
        payment = request.form.get("payment_method")
        amount = float(order["amount"])

        if order["amount_type"] == "rub":
            rub = amount
            litres = round(amount / price, 2) if price else 0
        else:
            litres = amount
            rub = round(amount * price, 2)

        # Сохраняем заказ как pending для оператора
        cur.execute("""
            INSERT INTO history (Адрес, Топливо, Рубли, Литры, Оплата, Telegram_ID, status, Дата)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (order["station"], order["fuel"], rub, litres, payment, session["telegram_id"], samara_now()))
        conn.commit()
        order_id = cur.lastrowid  # <-- ДО закрытия соединения
        conn.close()
        return redirect(f"/order_sent/{order_id}") # перенаправляем на страницу ожидания

    conn.close()
    station_name = STATION_NAMES.get(order["station"], order["station"])

    return render_template(
        "confirm.html",
        order=order,
        price=price,
        station_name=station_name,
        bonus=bonus
    )




@app.route("/order_sent/<int:order_id>")
def order_sent(order_id):
    if "telegram_id" not in session:
        return redirect("/dashboard")
    return render_template("order_sent.html", order_id=order_id)

@app.route("/api/done_orders")
def api_done_orders():
    if "telegram_id" not in session or session.get("role") == "operator":
        return {"orders": []}

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT h."№", h.Литры, h.Топливо, h.Оплата, fb.points_per_litre
        FROM history h
        LEFT JOIN fuel_bonus fb
        ON h.Топливо = fb.fuel_type AND h.Оплата = fb.payment_method
        WHERE h.Telegram_ID = ? AND h.status='done'
        ORDER BY h.Дата DESC
        LIMIT 5
    """, (session["telegram_id"],))
    done_orders = cur.fetchall()
    conn.close()

    notifications = []
    for order in done_orders:
        litres = order["Литры"] or 0
        points_per_litre = order["points_per_litre"] or 0
        points = round(litres * points_per_litre, 2)
        notifications.append({
            "order_id": order["№"],
            "fuel": order["Топливо"],
            "litres": litres,
            "points": points,
            "payment": order["Оплата"]
        })

    return {"orders": notifications}




# @app.route("/order_success/<int:order_id>")
# def order_success(order_id):
#     conn = get_db()
#     cur = conn.cursor()
#     cur.execute("SELECT * FROM history WHERE rowid=?", (order_id,))
#     order = cur.fetchone()
#     conn.close()
#
#     if not order:
#         return "Заказ не найден", 404
#
#     fuel = order['Топливо']
#     litres = order['Литры'] or 0
#     rub = order['Рубли'] or 0
#     points = order['Баллы']  # оставляем как есть
#     payment = order['Оплата']
#
#     # --- Отладка прямо в шаблон ---
#     debug_info = f"DEBUG: payment={payment}, points={points}"
#
#     bonus_message = payment == "bonus"
#
#     return render_template(
#         "order_success.html",
#         fuel=fuel,
#         litres=litres,
#         rub=rub,
#         points=points,
#         bonus_message=bonus_message,
#         debug_info=debug_info
#     )




@app.route("/notifications/stream")
def notifications_stream():
    telegram_id = request.args.get("telegram_id")

    def event_stream():
        conn = get_db()
        cur = conn.cursor()

        while True:
            cur.execute("""
                SELECT * FROM notifications
                WHERE telegram_id=? AND seen=0
                ORDER BY created_at ASC
            """, (telegram_id,))
            rows = cur.fetchall()

            if rows:
                for row in rows:
                    data = dict(row)
                    yield f"data: {json.dumps(data)}\n\n"
                    cur.execute("UPDATE notifications SET seen=1 WHERE id=?", (row["id"],))
                    conn.commit()
            else:
                # Отправляем пустое событие каждые 2 сек
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

            time.sleep(2)

    return Response(event_stream(), content_type="text/event-stream")





#----------ПОТОК ОПЕРАТОРА----------------------


@app.route("/operator", methods=["GET", "POST"])
def operator_panel():
    if session.get("role") != "operator":
        return "❌ Доступ запрещен", 403

    station = session.get("station")
    op_id = session.get("operator_id")

    conn = get_db()
    cur = conn.cursor()

    # --- Получаем оператора ---
    cur.execute("SELECT * FROM operators WHERE id=?", (op_id,))
    operator = cur.fetchone()
    if not operator:
        conn.close()
        return "❌ Оператор не найден"

    # --- Проверяем активную смену ---
    cur.execute("SELECT * FROM shifts WHERE operator_id=? AND active=1", (op_id,))
    shift = cur.fetchone()
    shift_dict = dict(shift) if shift else None

    from datetime import datetime

    # --- НАЧАТЬ СМЕНУ ---
    if request.method == "POST" and request.form.get("action") == "start":
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            "INSERT INTO shifts (operator_id, station, active, start_time) VALUES (?, ?, 1, ?)",
            (op_id, station, samara_now())
        )
        conn.commit()
        # получаем id новой смены
        shift_id = cur.lastrowid
        cur.execute("UPDATE operators SET active=1 WHERE id=?", (op_id,))
        conn.commit()
        conn.close()
        return redirect("/operator")

    # --- ЗАКОНЧИТЬ СМЕНУ ---
    if request.method == "POST" and request.form.get("action") == "end" and shift:
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Обновляем смену
        cur.execute(
            "UPDATE shifts SET active=0, end_time=? WHERE id=?",
            (samara_now(), shift["id"])
        )
        cur.execute("UPDATE operators SET active=0 WHERE id=?", (op_id,))

        # Помечаем все обычные заявки этой смены как done
        cur.execute(
            "UPDATE history SET status='done', shift_id=? WHERE Адрес=? AND status='pending'",
            (shift["id"], station)
        )

        # Помечаем все заказы 'полный бак' как done
        cur.execute(
            "UPDATE history SET status='done', shift_id=? WHERE Адрес=? AND status='pending_full_tank'",
            (shift["id"], station)
        )
        conn.commit()

        # Считаем итоги по топливу только этой смены
        cur.execute(
            "SELECT Топливо, SUM(Литры) AS total_litres, SUM(Рубли) AS total_rub "
            "FROM history WHERE shift_id=? GROUP BY Топливо",
            (shift["id"],)
        )
        fuel_summary = [dict(row) for row in cur.fetchall()]

        conn.close()

        # Сохраняем данные смены и итоги в сессию для summary
        session["shift_summary"] = {
            "station": station,
            "start_time": shift["start_time"],
            "end_time": end_time,
            "fuel_summary": fuel_summary
        }

        return redirect("/operator/summary")

    # --- Загружаем новые заявки ---
    pending_orders = []
    full_tank_orders = []
    if shift:
        # Обычные заказы
        cur.execute(
            "SELECT * FROM history WHERE status='pending' AND shift_id IS NULL AND Адрес=? ORDER BY rowid DESC",
            (station,)
        )
        pending_orders = [dict(row) for row in cur.fetchall()]

        # Заказы полный бак
        cur.execute(
            "SELECT * FROM history WHERE status='pending_full_tank' AND shift_id IS NULL AND Адрес=? ORDER BY rowid DESC",
            (station,)
        )
        full_tank_orders = [dict(row) for row in cur.fetchall()]

    conn.close()

    return render_template(
        "operator_panel.html",
        shift=shift_dict,
        station=station,
        orders=pending_orders,
        full_tank_orders=full_tank_orders,
        STATION_NAMES=STATION_NAMES
    )


@app.route("/operator/change_pin", methods=["GET", "POST"])
def change_pin():
    if session.get("role") != "operator":
        return "❌ Доступ запрещен", 403

    op_id = session.get("operator_id")
    conn = get_db()
    cur = conn.cursor()

    # Получаем текущего оператора
    cur.execute("SELECT * FROM operators WHERE id=?", (op_id,))
    operator = cur.fetchone()
    if not operator:
        conn.close()
        return "❌ Оператор не найден"

    message = None  # для уведомления об ошибке или успехе

    if request.method == "POST":
        old_pin = request.form.get("old_pin", "").strip()
        new_pin = request.form.get("new_pin", "").strip()

        print(f"OLD PIN: '{old_pin}', DB PIN: '{operator['pin']}', NEW PIN: '{new_pin}'")

        # Проверяем старый PIN
        if str(operator['pin']).strip() != old_pin:
            message = "❌ Неверный текущий PIN"
        # Проверяем новый PIN
        elif not new_pin.isdigit() or len(new_pin) != 4:
            message = "❌ Новый PIN должен быть 4 цифры"
        else:
            # Обновляем PIN
            cur.execute("UPDATE operators SET pin=? WHERE id=?", (new_pin, op_id))
            conn.commit()
            conn.close()
            print(f"PIN успешно изменён: {new_pin}")
            # После успешной смены PIN → редирект обратно на панель оператора
            return redirect("/operator")

    conn.close()
    return render_template("change_pin.html", operator=operator, message=message)



@app.route("/operator/done_order/<int:order_id>")
def operator_done_order(order_id):
    if session.get("role") != "operator":
        return "❌ Нет доступа", 403

    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM history WHERE "№"=?', (order_id,))
    order = cur.fetchone()
    if not order:
        conn.close()
        return "❌ Заказ не найден"

    # Можно здесь сделать перевод способа оплаты на русский
    payment_labels = {'card': 'Карта', 'cash': 'Наличка', 'bonus': 'Бонусы'}
    order_payment_ru = payment_labels.get(order["Оплата"], order["Оплата"])

    conn.close()
    return render_template(
        "operator_done_order.html",
        order=order,
        order_payment_ru=order_payment_ru
    )

@app.route("/operator/full_tank/<int:order_id>", methods=["GET", "POST"])
def operator_full_tank_submit(order_id):
    if session.get("role") != "operator":
        return "❌ Нет доступа", 403

    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM history WHERE "№"=?', (order_id,))
    order = cur.fetchone()
    if not order:
        conn.close()
        return "❌ Заказ не найден"

    station_name = STATION_NAMES.get(order["Адрес"], order["Адрес"])

    if request.method == "POST":
        litres = float(request.form.get("litres"))

        # обновляем литры и статус ожидания оплаты
        cur.execute("""
            UPDATE history
            SET Литры=?, status='waiting_payment'
            WHERE "№"=?
        """, (litres, order_id))

        # 🔥 уведомление для SSE
        cur.execute("""
            INSERT INTO notifications (telegram_id, message, type, order_id)
            VALUES (?, ?, ?, ?)
        """, (order["Telegram_ID"], "Подтвердите оплату", "full_tank_ready", order_id))

        conn.commit()
        conn.close()

        # оператор перенаправляется на страницу ожидания
        return redirect(f"/operator/wait_payment/{order_id}")
    conn.close()
    return render_template("confirm_full_tank.html", order=order, station_name=station_name)


#ОПЕРАТОР ЖДЕТ ПОЛЬЗОВАТЕЛЯ ПОКА ОН ВЫБЕРЕТ СПОСОБ ОПЛАТЫ

@app.route("/operator/wait_payment/<int:order_id>")
def operator_wait_payment(order_id):
    if session.get("role") != "operator":
        return "❌ Нет доступа", 403

    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM history WHERE "№"=?', (order_id,))
    order = cur.fetchone()
    if not order:
        conn.close()
        return "❌ Заказ не найден"

    # Оплата бонусами уже завершена
    if order["Оплата"] == "bonus" and order["status"] == "done":
        conn.close()
        return redirect(f"/operator/order_done_bonus/{order_id}")

    station_address = STATION_NAMES.get(order["Адрес"], order["Адрес"])
    operator_telegram_id = STATION_OPERATORS.get(station_address)

    conn.close()
    return render_template(
        "operator_wait_payment.html",
        order=order,
        operator_telegram_id=operator_telegram_id
    )
@app.route("/operator/accept_payment/<int:order_id>", methods=["GET", "POST"])
def operator_accept_payment(order_id):
    if session.get("role") != "operator":
        return "❌ Нет доступа", 403

    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM history WHERE "№"=?', (order_id,))
    order = cur.fetchone()

    if not order:
        conn.close()
        return "❌ Заказ не найден"

    if request.method == "POST":
        # Просто подтверждаем оплату (не меняем cash/card/bonus)
        cur.execute("""
            UPDATE history
            SET status='done'
            WHERE "№"=?
        """, (order_id,))

        # Отправляем уведомление пользователю
        cur.execute("""
            INSERT INTO notifications (
                telegram_id, message, type, order_id, fuel, litres, amount_rub, points, payment_method
            ) VALUES (?, ?, 'order_done', ?, ?, ?, ?, ?, ?)
        """, (
            order["Telegram_ID"],
            f"Оплата подтверждена оператором",
            order_id,
            order["Топливо"],
            order["Литры"],
            order["Рубли"],
            0,
            order["Оплата"]   # <- оставляем старый способ оплаты без изменений
        ))

        conn.commit()
        conn.close()

        # Редирект на done_order
        return redirect(f"/operator/done_order/{order_id}")

    conn.close()
    return render_template("operator_accept_payment.html", order=order)

@app.route("/operator/order_ready/<int:order_id>")
def operator_order_ready(order_id):
    print(f"[DEBUG] operator_order_ready for order #{order_id}")
    if session.get("role") != "operator":
        print("[DEBUG] Нет доступа")
        return "❌ Нет доступа", 403

    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM history WHERE "№"=?', (order_id,))
    order = cur.fetchone()
    conn.close()

    if not order:
        print("[DEBUG] Заказ не найден")
        return "❌ Заказ не найден"

    print(f"[DEBUG] Оператор видит заказ: #{order_id}, Статус: {order['status']}, Оплата: {order['Оплата']}")
    return render_template("operator_order_ready.html", order=order)

@app.route("/confirmed_analog/<int:order_id>", methods=["GET", "POST"])
def confirmed_analog(order_id):
    if "telegram_id" not in session:
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()

    # Получаем заказ
    cur.execute('SELECT * FROM history WHERE "№"=?', (order_id,))
    order = cur.fetchone()
    if not order:
        conn.close()
        return "❌ Заказ не найден"

    # Цена топлива
    cur.execute("SELECT price_per_litre FROM fuel WHERE fuel_type=?", (order["Топливо"],))
    fuel_row = cur.fetchone()
    price_per_litre = fuel_row["price_per_litre"] if fuel_row else 0

    litres = order["Литры"] or 0
    rub = round(litres * price_per_litre, 2)

    # Имя станции
    station_name = STATION_NAMES.get(order["Адрес"], order["Адрес"])

    # Баланс пользователя
    cur.execute("SELECT bonus FROM users WHERE telegram_id=?", (session["telegram_id"],))
    user = cur.fetchone()
    user_bonus = user["bonus"] if user else 0

    if request.method == "POST":
        payment = request.form.get("payment_method")

        if payment == "bonus":
            # Оплата бонусами сразу
            cur.execute("""
                UPDATE history
                SET Оплата='bonus', status='done', Рубли=?, points=0
                WHERE "№"=?
            """, (rub, order_id))

            # Уведомление оператору о бонусной оплате
            operator_telegram_id = STATION_OPERATORS.get(station_name)
            cur.execute("""
                INSERT INTO notifications (telegram_id, message, type, order_id)
                VALUES (?, ?, 'bonus_paid', ?)
            """, (
                operator_telegram_id,
                f"Пользователь оплатил заказ #{order_id} бонусами",
                order_id
            ))

            conn.commit()
            conn.close()
            return redirect(f"/order_success_analog/{order_id}")

        else:
            # Обычная оплата (cash/card)
            cur.execute("""
                UPDATE history
                SET Оплата=?, status='waiting_operator_confirm'
                WHERE "№"=?
            """, (payment, order_id))

            # Уведомление оператору о выборе способа оплаты
            operator_telegram_id = STATION_OPERATORS.get(station_name)
            cur.execute("""
                INSERT INTO notifications (telegram_id, message, type, order_id)
                VALUES (?, ?, 'waiting_payment', ?)
            """, (
                operator_telegram_id,
                f"Клиент выбрал способ оплаты: {payment} для заказа #{order_id}",
                order_id
            ))

            conn.commit()
            conn.close()
            return redirect(f"/pay_order/{order_id}")

    conn.close()
    return render_template(
        "confirmed_analog.html",
        order=order,
        rub=rub,
        station_name=station_name,
        user_bonus=user_bonus
    )



@app.route("/pay_order/<int:order_id>")
def pay_order(order_id):
    # Проверяем, что пользователь зашел через Telegram
    if "telegram_id" not in session:
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM history WHERE "№"=?', (order_id,))
    order = cur.fetchone()
    conn.close()

    if not order:
        return "❌ Заказ не найден"

    # Просто страница ожидания оператора
    return render_template("pay_order.html", order_id=order_id)

@app.route("/order_success_analog/<int:order_id>")
def order_success_analog(order_id):
    if "telegram_id" not in session:
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()

    # Получаем данные заказа с бонусами и ценой топлива
    cur.execute("""
        SELECT h.Литры, h.Топливо, h.Оплата, h."Рубли", fb.points_per_litre, f.price_per_litre, h.Telegram_ID
        FROM history h
        LEFT JOIN fuel_bonus fb
            ON h.Топливо = fb.fuel_type AND h.Оплата = fb.payment_method
        LEFT JOIN fuel f
            ON h.Топливо = f.fuel_type
        WHERE h."№"=?
    """, (order_id,))
    order = cur.fetchone()
    if not order:
        conn.close()
        return "❌ Заказ не найден"

    litres = order["Литры"] or 0
    price_per_litre = order["price_per_litre"] or 0
    rub = order["Рубли"] or round(litres * price_per_litre, 2)

    points = 0
    if order["Оплата"] == "bonus":
        # Получаем текущий баланс
        cur.execute("SELECT bonus FROM users WHERE telegram_id=?", (order["Telegram_ID"],))
        user = cur.fetchone()
        user_bonus = user["bonus"] if user else 0

        if user_bonus >= rub:
            # списываем
            cur.execute("""
                UPDATE users
                SET bonus = bonus - ?
                WHERE telegram_id = ?
            """, (rub, order["Telegram_ID"]))
        else:
            print(f"[ERROR] Недостаточно бонусов у пользователя {order['Telegram_ID']}")
    # Начисляем бонусы только если оплата не бонусами
    if order["Оплата"] != "bonus":
        points_per_litre = order["points_per_litre"] or 0
        points = round(litres * points_per_litre, 2)

        if points > 0:
            # Обновляем историю и начисляем бонусы пользователю
            cur.execute("""
                UPDATE history
                SET points = ?
                WHERE "№" = ?
            """, (points, order_id))

            cur.execute("""
                UPDATE users
                SET bonus = bonus + ?
                WHERE telegram_id = ?
            """, (points, order["Telegram_ID"]))

            # Создаем уведомление для Telegram
            cur.execute("""
                INSERT INTO notifications (telegram_id, message, points, type, order_id, fuel, litres, amount_rub)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order["Telegram_ID"],
                f"✅ Начислено {points} бонусных баллов за заказ #{order_id}",
                points,
                "bonus_added",
                order_id,
                order["Топливо"],
                litres,
                rub
            ))

    conn.commit()
    conn.close()

    return render_template(
        "order_success_analog.html",
        points=points,
        fuel=order["Топливо"],
        litres=litres,
        rub=rub,
        payment_method=order["Оплата"]
    )

@app.route("/operator/confirm_payment/<int:order_id>", methods=["POST"])
def confirm_payment(order_id):
    if session.get("role") != "operator":
        return "❌ Нет доступа", 403

    conn = get_db()
    cur = conn.cursor()

    # Получаем заказ
    cur.execute('SELECT * FROM history WHERE "№"=?', (order_id,))
    order = cur.fetchone()
    if not order:
        conn.close()
        return "❌ Заказ не найден"

    litres = order["Литры"] or 0

    # --- Получаем цену топлива ---
    cur.execute("SELECT price_per_litre FROM fuel WHERE fuel_type=?", (order["Топливо"],))
    price_row = cur.fetchone()
    price_per_litre = price_row["price_per_litre"] if price_row else 0
    rub = round(litres * price_per_litre, 2)

    # --- Получаем бонусные баллы ---
    cur.execute("""SELECT points_per_litre FROM fuel_bonus
                   WHERE fuel_type=? AND payment_method=?""",
                (order["Топливо"], order["Оплата"]))
    row = cur.fetchone()
    points_per_litre = row["points_per_litre"] if row else 0
    points = round(litres * points_per_litre, 2)

    # --- Обновляем историю сразу с рублями и баллами ---
    cur.execute("""
        UPDATE history
        SET status='done',
            Рубли=?,
            points=?
        WHERE "№"=?
    """, (rub, points, order_id))

    # --- Начисляем бонус пользователю ---
    if points > 0:
        cur.execute("UPDATE users SET bonus = bonus + ? WHERE telegram_id=?",
                    (points, order["Telegram_ID"]))

    # --- Отправляем уведомление пользователю ---
    cur.execute("""INSERT INTO notifications (
                        telegram_id, message, type, order_id, fuel, litres, rub, points
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    order["Telegram_ID"],
                    "Ваш заказ выполнен",
                    "order_done",
                    order_id,
                    order["Топливо"],
                    litres,
                    rub,
                    points
                ))

    conn.commit()
    conn.close()

    return redirect("/operator")


@app.route("/api/order_status/<int:order_id>")
def order_status(order_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT status FROM history WHERE "№"=?', (order_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return {"status": "not_found"}
    return {"status": row["status"]}



@app.route("/operator/start_full_tank/<int:order_id>", methods=["POST"])
def start_full_tank(order_id):
    if session.get("role") != "operator":
        return "❌ Нет доступа", 403

    conn = get_db()
    cur = conn.cursor()

    # Проверяем, существует ли заказ и статус pending_full_tank
    cur.execute('SELECT * FROM history WHERE "№"=? AND status="pending_full_tank"', (order_id,))
    order = cur.fetchone()
    if not order:
        conn.close()
        return "❌ Заказ не найден или уже в работе"

    # Меняем статус на in_progress
    cur.execute('UPDATE history SET status="in_progress" WHERE "№"=?', (order_id,))
    conn.commit()
    conn.close()

    # Перенаправляем на страницу ввода литров
    return redirect(f"/operator/full_tank/{order_id}")


@app.route("/operator/complete_full_tank/<int:order_id>", methods=["POST"])
def complete_full_tank(order_id):
    if session.get("role") != "operator":
        return "❌ Нет доступа", 403

    # Получаем данные из формы
    litres = float(request.form.get("litres", 0))
    payment = request.form.get("payment_method")  # cash или card

    conn = get_db()
    cur = conn.cursor()

    # Получаем заказ
    cur.execute('SELECT * FROM history WHERE "№"=?', (order_id,))
    order = cur.fetchone()
    if not order:
        conn.close()
        return "❌ Заказ не найден"

    fuel_type = order["Топливо"]

    # Получаем цену топлива
    cur.execute("SELECT price_per_litre FROM fuel WHERE fuel_type=?", (fuel_type,))
    row = cur.fetchone()
    price_per_litre = row["price_per_litre"] if row else 0
    rub = round(litres * price_per_litre, 2)

    # --- Обновляем заказ как выполненный ---
    cur.execute("""
        UPDATE history 
        SET Литры=?, Рубли=?, Оплата=?, status='done'
        WHERE "№"=?
    """, (litres, rub, payment, order_id))

    # --- Начисляем бонусы ---
    cur.execute("""
        SELECT points_per_litre FROM fuel_bonus
        WHERE fuel_type=? AND payment_method=?
    """, (fuel_type, payment))
    row = cur.fetchone()
    points_per_litre = row["points_per_litre"] if row else 0
    points = round(litres * points_per_litre, 2)

    if points > 0:
        cur.execute("""
            UPDATE users SET bonus = bonus + ? 
            WHERE telegram_id=?
        """, (points, order["Telegram_ID"]))

    # --- Уведомляем пользователя ---
    cur.execute("""
        INSERT INTO notifications (
            telegram_id, message, type, order_id, fuel, litres, amount_rub, points
        )
        VALUES (?, ?, 'order_done', ?, ?, ?, ?, ?)
    """, (
        order["Telegram_ID"],
        "Ваш заказ выполнен",
        order_id,
        fuel_type,
        litres,
        rub,
        points
    ))

    conn.commit()
    conn.close()

    return redirect("/operator")

@app.route("/operator/complete/<int:order_id>", methods=["POST"])
def operator_complete_order(order_id):
    if session.get("role") != "operator":
        return "❌ Доступ запрещен", 403

    op_id = session.get("operator_id")
    conn = get_db()
    cur = conn.cursor()

    # Проверяем активную смену
    cur.execute("SELECT * FROM shifts WHERE operator_id=? AND active=1", (op_id,))
    shift = cur.fetchone()
    if not shift:
        conn.close()
        return "❌ Нет активной смены"

    # Получаем заказ (обычный или полный бак)
    cur.execute('SELECT * FROM history WHERE "№"=? AND status IN ("pending", "pending_full_tank")', (order_id,))
    order = cur.fetchone()
    if not order:
        conn.close()
        return "❌ Заказ не найден или уже выполнен"

    litres = order["Литры"] or 0
    fuel_type = order["Топливо"]

    # Получаем цену топлива
    cur.execute("SELECT price_per_litre FROM fuel WHERE fuel_type=?", (fuel_type,))
    fuel_row = cur.fetchone()
    price_per_litre = fuel_row["price_per_litre"] if fuel_row else 0
    amount_rub = round(litres * price_per_litre, 2)

    # --- Вычисляем баллы ---
    payment = order["Оплата"]
    points_earned = 0
    if payment and payment not in ["pending", "pending_full_tank"]:
        cur.execute("""
            SELECT points_per_litre 
            FROM fuel_bonus 
            WHERE fuel_type=? AND payment_method=?
        """, (fuel_type, payment))
        row = cur.fetchone()
        points_per_litre = row["points_per_litre"] if row else 0
        points_earned = round(litres * points_per_litre, 2)

    # --- Обновляем историю ---
    cur.execute("""
        UPDATE history
        SET status='done',
            shift_id=?,
            Рубли=?,
            points=?
        WHERE "№"=?
    """, (shift["id"], amount_rub, points_earned, order_id))

    # --- Начисляем баллы пользователю ---
    if points_earned > 0:
        cur.execute("UPDATE users SET bonus = bonus + ? WHERE telegram_id=?", (points_earned, order["Telegram_ID"]))

    # --- Создаем уведомление ---
    cur.execute("""
        INSERT INTO notifications (
            telegram_id, message, type, order_id, fuel, litres, amount_rub, points, created_at
        ) VALUES (?, ?, 'order_done', ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        order["Telegram_ID"],
        "Ваш заказ выполнен ✅",
        order_id,
        fuel_type,
        litres,
        amount_rub,
        points_earned
    ))

    conn.commit()
    conn.close()

    print(f"💡 DEBUG: order_id={order_id}, litres={litres}, rub={amount_rub}, points={points_earned}, payment={payment}")

    return redirect("/operator")


@app.route("/operator/summary", methods=["GET", "POST"])
def operator_summary():
    if session.get("role") != "operator":
        return "❌ Доступ запрещен", 403

    summary = session.get("shift_summary")
    if not summary:
        return redirect("/operator")  # если данных нет, возвращаемся

    if request.method == "POST":
        telegram_id = session.get("telegram_id")  # сохраняем telegram_id
        # очищаем все данные оператора
        for key in ["role", "operator_id", "station", "shift_summary"]:
            session.pop(key, None)
        # ставим pending_operator, чтобы оператор смог выбрать себя
        session["pending_operator"] = telegram_id
        return redirect("/operator/login")

    return render_template("shift_summary.html", summary=summary)










#-----------ИСТОРИЯ-------------------------



@app.route("/history")
def history():
    if "telegram_id" not in session:
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()

    # --- Выборка заявок ---
    if session.get("is_admin"):
        # Админ видит все заявки, лимит 50 последних
        cur.execute("SELECT * FROM history ORDER BY Дата DESC LIMIT 50")
    else:
        # Обычный пользователь видит только свои заявки, лимит 50
        cur.execute(
            "SELECT * FROM history WHERE Telegram_ID=? ORDER BY rowid DESC LIMIT 50",
            (session["telegram_id"],)
        )

    rows = [dict(row) for row in cur.fetchall()]

    # --- Словарь для перевода оплаты ---
    PAYMENT_NAMES = {
        "cash": "💵 Наличные",
        "card": "💳 Карта",
        "bonus": "🎁 Баллами",
        "pending_full_tank": "⛽ Полный бак (ожидание)",
        "pending": "⏳ В обработке"
    }

    # --- Словарь названий станций ---
    STATION_NAMES = {
        "station_1": "Южное шоссе 129",
        "station_2": "Южное шоссе 12/2",
        "station_3": "Лесная 66А",
        "station_4": "Борковская 72/1"
    }

    for row in rows:
        # --- Сохраняем оригинальный код оплаты ---
        payment_code = row.get("Оплата")

        # --- Расчёт баллов ---
        litres = row.get("Литры") or 0
        cur.execute("""
            SELECT points_per_litre
            FROM fuel_bonus
            WHERE fuel_type=? AND payment_method=?
        """, (row["Топливо"], payment_code))
        result = cur.fetchone()
        points_per_litre = result["points_per_litre"] if result else 0
        row["Баллы"] = round(litres * points_per_litre, 2)

        # --- Перевод оплаты в русский текст ---
        row["Оплата"] = PAYMENT_NAMES.get(payment_code, payment_code)

        # --- Перевод кода станции в название ---
        row["Станция"] = STATION_NAMES.get(row.get("Адрес"), row.get("Адрес"))

    conn.close()

    return render_template(
        "history.html",
        rows=rows,
        is_admin=session.get("is_admin", False)
    )



@app.route("/history/export")
def export_history():
    if "user_id" not in session:
        return redirect("/")

    if not session.get("is_admin"):
        return "❌ Доступ запрещен", 403

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    df = pd.read_sql_query("SELECT * FROM history ORDER BY Дата DESC", conn)
    conn.close()

    # --- Справочники ---
    PAYMENT_NAMES = {
        "cash": "Наличные",
        "card": "Карта",
        "bonus": "Баллами"
    }

    # --- Преобразования ---
    if "Адрес" in df.columns:
        df["Адрес"] = df["Адрес"].map(lambda x: STATION_NAMES.get(x, x))

    if "Оплата" in df.columns:
        df["Оплата"] = df["Оплата"].map(lambda x: PAYMENT_NAMES.get(x, x))

    # Убираем None → "-"
    df = df.fillna("-")

    # --- Экспорт ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='История')

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="history.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.route("/prices")
def view_fuel_prices():
    conn = get_db()
    cur = conn.cursor()

    # Берём все топлива и их цены
    cur.execute("SELECT fuel_type, price_per_litre FROM fuel")
    fuels = cur.fetchall()
    conn.close()

    # Рендерим шаблон с таблицей цен
    return render_template("prices.html", fuels=fuels)
@app.route("/my_points")
def my_points():
    if "telegram_id" not in session:
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()

    # Получаем бонусы пользователя
    cur.execute("SELECT bonus FROM users WHERE telegram_id=?", (session["telegram_id"],))
    user = cur.fetchone()
    user_bonus = user["bonus"] if user else 0

    # Получаем все баллы за топливо
    cur.execute("SELECT fuel_type, payment_method, points_per_litre FROM fuel_bonus")
    rows = cur.fetchall()

    # Формируем структуру: fuel -> {cash: X, card: Y}
    fuel_bonus = {}
    for row in rows:
        fuel = row["fuel_type"]
        method = row["payment_method"]
        points = row["points_per_litre"]
        if fuel not in fuel_bonus:
            fuel_bonus[fuel] = {"cash": 0, "card": 0}
        if method.lower() in ["cash", "нал", "наличные"]:
            fuel_bonus[fuel]["cash"] = points
        else:
            fuel_bonus[fuel]["card"] = points

    conn.close()
    return render_template(
        "my_points.html",
        user_bonus=user_bonus,
        fuel_bonus=fuel_bonus
    )











#---------------АДМИНСКИЕ ФИШКИ-------------------------------

@app.route("/admin/set_bonus", methods=["GET", "POST"])
def set_bonus():
    if not session.get("is_admin", False):
        return "❌ Доступ запрещен", 403

    fuels = ["Бензин", "Газ"]
    payments = ["cash", "card"]
    payments_ru = {"cash": "💵 Наличные", "card": "💳 Карта"}  # русские подписи

    conn = get_db()
    cur = conn.cursor()
    # Создаем таблицу бонусов, если нет
    cur.execute('''
        CREATE TABLE IF NOT EXISTS fuel_bonus (
            fuel_type TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            points_per_litre REAL DEFAULT 0,
            PRIMARY KEY (fuel_type, payment_method)
        )
    ''')
    conn.commit()

    if request.method == "POST":
        fuel = request.form.get("fuel")
        payment = request.form.get("payment_method")
        points = float(request.form.get("points", 0))
        cur.execute('''
            INSERT INTO fuel_bonus (fuel_type, payment_method, points_per_litre)
            VALUES (?, ?, ?)
            ON CONFLICT(fuel_type, payment_method) DO UPDATE SET points_per_litre=excluded.points_per_litre
        ''', (fuel, payment, points))
        conn.commit()
        flash(f"Баллы для {fuel} ({payments_ru[payment]}) обновлены: {points} балл/л")
        return redirect("/dashboard")

    # Текущие значения
    cur.execute("SELECT * FROM fuel_bonus")
    rows = cur.fetchall()
    points = {}
    for row in rows:
        if row['fuel_type'] not in points:
            points[row['fuel_type']] = {}
        points[row['fuel_type']][row['payment_method']] = row['points_per_litre']
    conn.close()

    return render_template(
        "set_bonus.html",
        fuels=fuels,
        payments=payments,
        payments_ru=payments_ru,
        points=points
    )





@app.route("/admin/add_operator", methods=["GET", "POST"])
def add_operator():
    if "user_id" not in session:
        return redirect("/")

    # Проверка на админа через сессию, а не БД
    if not session.get("is_admin"):
        return "❌ Доступ запрещен", 403

    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        station = request.form.get("station")

        # Получаем Telegram ID по станции
        telegram_id = STATION_OPERATORS.get(STATION_NAMES.get(station, ""), None)
        if telegram_id is None:
            flash(f"Не найден Telegram ID для станции {station}")
            return redirect("/admin/add_operator")

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO operators (name, phone, station, telegram_id) VALUES (?, ?, ?, ?)",
            (name, phone, station, telegram_id)
        )
        conn.commit()
        conn.close()

        flash(f"Оператор {name} успешно добавлен! Telegram ID: {telegram_id}")
        return redirect("/dashboard")

    return render_template("add_operator.html", stations=STATION_NAMES)





@app.route("/admin/operators", methods=["GET", "POST"])
def list_operators():
    if "user_id" not in session or not session.get("is_admin"):
        return "❌ Доступ запрещен", 403

    conn = get_db()
    cur = conn.cursor()

    # --- УДАЛЕНИЕ ОПЕРАТОРА ---
    if request.method == "POST":
        op_id = request.form.get("operator_id")
        action = request.form.get("action")
        if action == "delete":
            cur.execute("DELETE FROM operators WHERE id = ?", (op_id,))
            conn.commit()

    # --- ПОЛУЧАЕМ ВСЕХ ОПЕРАТОРОВ ---
    cur.execute("SELECT * FROM operators")
    operators = cur.fetchall()  # словари благодаря row_factory

    # --- ПОЛУЧАЕМ ВСЕ АКТИВНЫЕ СМЕНЫ ---
    cur.execute("SELECT * FROM shifts WHERE active = 1")
    shifts = cur.fetchall()  # словари

    conn.close()

    return render_template(
        "operators.html",
        operators=operators,
        station_names=STATION_NAMES,
        shifts=shifts
    )



# --- Изменение цены топлива ---
@app.route("/admin/set_prices", methods=["GET", "POST"])
def set_prices():
    if "user_id" not in session or not session.get("is_admin", False):
        return "❌ Доступ запрещен", 403

    fuels = ["Бензин", "Газ"]
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT fuel_type, price_per_litre FROM fuel")
    rows = cur.fetchall()
    conn.close()

    prices = {row["fuel_type"]: row["price_per_litre"] for row in rows}

    if request.method == "POST":
        fuel = request.form.get("fuel")
        price = float(request.form.get("price"))
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE fuel SET price_per_litre = ? WHERE fuel_type = ?", (price, fuel))
        conn.commit()
        conn.close()
        flash(f"Цена для {fuel} обновлена: {price} ₽/л")
        return redirect("/dashboard")

    return render_template("set_prices.html", fuels=fuels, prices=prices)
import random
EXIT_MESSAGES = [
    "Топливо ждёт, а ты — приходи снова!",
    "Бензин на месте, а ты — всегда можешь заглянуть!",
    "Бак пуст? Не переживай, мы тут всегда рядом!",
    "Ты вышел, а бензин всё ещё ждёт тебя!",
    "Даже колонки отдыхают — возвращайся скоро!"
]

@app.route("/logout")
def exit_page():
    message = random.choice(EXIT_MESSAGES)
    return render_template("logout.html", message=message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10001, debug=True, threaded=True)

