FROM python:3.11-slim

# системные пакеты
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    sqlite3 \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# зависимости python
COPY requirements.txt /app/
RUN pip install --upgrade pip certifi
RUN pip install --no-cache-dir -r requirements.txt

# копируем код
COPY . /app/

# порт для сайта
EXPOSE 10000

# запускаем только main.py (бот + Flask)
CMD ["python", "main.py"]