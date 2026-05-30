from flask import Flask, render_template, request, redirect, url_for, session, abort
from database import get_db_connection, init_db
import hashlib

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_library_app'

init_db()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Якщо увійшов адмін, перенаправляємо його на адмін-панель
    if session.get('is_admin') == 1:
        return redirect(url_for('admin_panel'))

    conn = get_db_connection()
    books = conn.execute(
        'SELECT * FROM books WHERE user_id = ? ORDER BY status DESC, date_added DESC',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    return render_template('index.html', books=books, username=session['username'])


# --- ПАНЕЛЬ АДМІНІСТРАТОРА ---
@app.route('/admin')
def admin_panel():
    # Перевірка безпеки: якщо не адмін — показуємо помилку 403 (Доступ заборонено)
    if 'user_id' not in session or session.get('is_admin') != 1:
        abort(403)

    conn = get_db_connection()
    # Вибираємо всіх користувачів, КРІМ самого себе (щоб адмін випадково не видалив себе)
    users = conn.execute(
        'SELECT id, username, date_reg FROM users WHERE is_admin = 0 ORDER BY date_reg DESC').fetchall()
    conn.close()
    return render_template('admin.html', users=users, username=session['username'])


@app.route('/admin/delete_user/<int:id>', methods=['POST'])
def delete_user(id):
    if 'user_id' not in session or session.get('is_admin') != 1:
        abort(403)

    conn = get_db_connection()
    # Видаляємо користувача. Завдяки ON DELETE CASCADE у базі, всі його книги видаляться автоматично!
    conn.execute('DELETE FROM users WHERE id = ? AND is_admin = 0', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))


# -----------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        if username and password:
            if username.lower() == 'admin':
                return render_template('auth.html', mode='register', error="Ім'я 'admin' зарезервоване.")

            conn = get_db_connection()
            try:
                conn.execute(
                    'INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 0)',
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
            session['is_admin'] = user['is_admin']  # Зберігаємо статус адміна в сесію
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
    if 'user_id' not in session or session.get('is_admin') == 1: return redirect(url_for('login'))
    title = request.form['title']
    author = request.form['author']
    genre = request.form['genre']
    if title and author:
        conn = get_db_connection()
        conn.execute('INSERT INTO books (user_id, title, author, genre) VALUES (?, ?, ?, ?)',
                     (session['user_id'], title, author, genre))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))


@app.route('/update/<int:id>', methods=['POST'])
def update_book(id):
    if 'user_id' not in session or session.get('is_admin') == 1: return redirect(url_for('login'))
    status = request.form['status']
    rating = int(request.form['rating'])
    review = request.form['review']
    conn = get_db_connection()
    conn.execute('UPDATE books SET status = ?, rating = ?, review = ? WHERE id = ? AND user_id = ?',
                 (status, rating, review, id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/delete/<int:id>', methods=['POST'])
def delete_book(id):
    if 'user_id' not in session or session.get('is_admin') == 1: return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM books WHERE id = ? AND user_id = ?', (id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)