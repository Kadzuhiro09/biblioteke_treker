import random
import string
from locust import HttpUser, task, between

def generate_random_string(length=8):
    """Генерація випадкового рядка для унікальних логінів та назв книг."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


class LibraryUser(HttpUser):
    # Імітуємо затримку між діями користувача від 1 до 3 секунд
    wait_time = between(1, 3)

    def on_start(self):
        """Цей метод викликається автоматично, коли віртуальний користувач 'народжується'."""
        self.username = f"user_{generate_random_string(5)}"
        self.password = "password123"
        self.register_and_login()

    def register_and_login(self):
        # 1. Реєструємо нового унікального користувача
        self.client.post("/register", data={
            "username": self.username,
            "password": self.password
        })

        # 2. Логінимося в систему
        self.client.post("/login", data={
            "username": self.username,
            "password": self.password
        })

    @task(3)
    def view_shelf(self):
        """Користувач просто заходить на головну сторінку та дивиться свою полицю (високий пріоритет task(3))."""
        self.client.get("/")

    @task(2)
    def add_and_manage_book(self):
        """Користувач додає книгу, а потім оновлює її статус."""
        book_title = f"Книга {generate_random_string(6)}"
        book_author = f"Автор {generate_random_string(4)}"

        # Додаємо книгу через POST-запит
        # Перенаправлення (catch_response) обробляємо вручну, щоб Locust не вважав 302 Redirect помилкою
        with self.client.post("/add", data={
            "title": book_title,
            "author": book_author,
            "genre": "Тест"
        }, catch_response=True) as response:
            if response.status_code in [200, 302]:
                response.success()

        # Для імітації реального життя, іноді оновлюємо статус (якщо у користувача вже є книги)
        # Оскільки ми не парсимо HTML для пошуку ID книги в цьому простому тесті,
        # ми просто шлемо POST-запит на оновлення умовної книги (наприклад з ID 1 або 2),
        # щоб перевірити як сервер тримає навантаження на маршруті /update
        random_id = random.randint(1, 10)
        with self.client.post(f"/update/{random_id}", data={
            "status": "Читаю",
            "rating": 4,
            "review": "Автоматичний тест навантаження"
        }, catch_response=True) as response:
            if response.status_code in [200, 302, 404]:  # 404 теж ок, якщо книги з таким ID немає
                response.success()

    def on_stop(self):
        """Викликається, коли тест закінчується або користувач відключається."""
        self.client.get("/logout")