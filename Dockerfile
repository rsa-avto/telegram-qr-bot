FROM python:3.11-slim

# Обновляем пакеты и устанавливаем зависимости для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . /app/

# Открываем порт Flask
EXPOSE 8000

# Запуск бота
CMD ["python", "main.py"]