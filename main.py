from flask import Flask, render_template, request, redirect, url_for, session
from database import get_db_connection, init_db
import hashlib
import sqlite3

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_library_app'

# Ініціалізація БД при старті
init_db()


def hash_password(password):
    """Хешування пароля в SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    # Вибираємо книги лише поточного користувача
    books = conn.execute(
        'SELECT * FROM books WHERE user_id = ? ORDER BY status DESC, date_added DESC',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    return render_template('index.html', books=books, username=session['username'])


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        if username and password:
            conn = get_db_connection()
            try:
                conn.execute(
                    'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                    (username, hash_password(password))
                )
                conn.commit()
                conn.close()
                return redirect(url_for('login', msg="Реєстрація успішна! Увійдіть у профіль."))
            except sqlite3.IntegrityError:
                conn.close()
                return render_template('auth.html', mode='register', error="Це ім'я користувача вже зайняте.")
    return render_template('auth.html', mode='register')


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = request.args.get('msg')
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password_hash = ?',
            (username, hash_password(password))
        ).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return render_template('auth.html', mode='login', error="Невірне ім'я користувача або пароль.")

    return render_template('auth.html', mode='login', msg=msg)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/add', methods=['POST'])
def add_book():
    if 'user_id' not in session: return redirect(url_for('login'))

    title = request.form['title']
    author = request.form['author']
    genre = request.form['genre']

    if title and author:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO books (user_id, title, author, genre) VALUES (?, ?, ?, ?)',
            (session['user_id'], title, author, genre)
        )
        conn.commit()
        conn.close()
    return redirect(url_for('index'))


@app.route('/update/<int:id>', methods=['POST'])
def update_book(id):
    if 'user_id' not in session: return redirect(url_for('login'))

    status = request.form['status']
    rating = int(request.form['rating'])
    review = request.form['review']

    conn = get_db_connection()
    conn.execute(
        'UPDATE books SET status = ?, rating = ?, review = ? WHERE id = ? AND user_id = ?',
        (status, rating, review, id, session['user_id'])
    )
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/delete/<int:id>', methods=['POST'])
def delete_book(id):
    if 'user_id' not in session: return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM books WHERE id = ? AND user_id = ?', (id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
