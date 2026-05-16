import sqlite3

conn = sqlite3.connect("library.db")
cursor = conn.cursor()

try:
    # Додаємо колонку user_id до існуючої таблиці books
    cursor.execute("ALTER TABLE books ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1;")
    conn.commit()
    print("Колонку user_id успішно додано!")
except sqlite3.OperationalError:
    print("Колонка вже існує або виникла інша помилка.")

conn.close()