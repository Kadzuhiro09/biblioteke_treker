import sqlite3

conn = sqlite3.connect("library.db")
cursor = conn.cursor()

# Делаем пользователя 'test' администратором
cursor.execute("UPDATE users SET is_admin = 1 WHERE username = 'test'")
conn.commit()
conn.close()
print("Пользователь test теперь имеет права администратора!")