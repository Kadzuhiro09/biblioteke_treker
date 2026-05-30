import sqlite3

DATABASE_NAME = "library.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Таблиця користувачів (додано стовпчик is_admin)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            date_reg TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Таблиця книг
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            genre TEXT,
            status TEXT NOT NULL DEFAULT 'Хочу прочитати',
            rating INTEGER DEFAULT 0,
            review TEXT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    # Автоматично створюємо одного адміна для тестів, якщо таблиця порожня
    # Логін: admin, Пароль: admin123 (хеш: 24004524c56e29db1a4d952a13ee42a5a037803d2ec4e3d30e3776bf38b1d9d9)
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = "admin"')
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            'INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)',
            ('admin', '24004524c56e29db1a4d952a13ee42a5a037803d2ec4e3d30e3776bf38b1d9d9', 1)
        )

    conn.commit()
    conn.close()
    print("Базу даних успішно ініціалізовано!")


if __name__ == "__main__":
    init_db()