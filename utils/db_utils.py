import sqlite3

# Функция для выполнения SQL-запроса
def execute_query(db_path: str, query: str, params: tuple = ()):
    """
    Выполняет SQL-запрос к базе данных SQLite.
    
    :param db_path: путь к файлу базы данных
    :param query: SQL-запрос
    :param params: кортеж параметров для запроса
    :return: результат запроса (список кортежей)
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        # Если это SELECT, возвращаем результат
        if query.strip().upper().startswith("SELECT"):
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.rowcount  # количество изменённых строк
        
        cursor.close()
        conn.close()
        return result
    except sqlite3.Error as e:
        print(f"Ошибка при работе с базой данных: {e}")
        return None
