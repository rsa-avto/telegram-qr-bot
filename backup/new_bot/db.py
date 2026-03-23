<<<<<<< HEAD
import sqlite3

DB_PATH = "cars.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
=======
import sqlite3

DB_PATH = "cars.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
>>>>>>> 155af79 (fix: мои правки)
    return conn