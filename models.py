import sqlite3

import config


class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):

        return sqlite3.connect(self.db_path)

    def init_database(self):

        conn = self.get_connection()
        cursor = conn.cursor()

        # Таблица товаров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT,
                quantity INTEGER DEFAULT 0,
                is_new INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица категорий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')

        # Таблица отзывов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                product_name TEXT,
                rating INTEGER DEFAULT 5,
                review_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица возвратов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                order_details TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица продавцов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sellers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                user_name TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица "О нас"
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS about_us (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица заказов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                items TEXT NOT NULL,
                total_price REAL NOT NULL,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')



        # Создаем таблицу поставщиков
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_person TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                rating DECIMAL(3,2) DEFAULT 0.0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Добавляем базовые данные если таблицы пустые
        self._add_default_data(cursor)

        conn.commit()
        conn.close()

    def _add_default_data(self, cursor):

        # Категории
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            categories = [
                ('Фрукты'),
                ('Овощи'),
            ]
            cursor.executemany(
                "INSERT INTO categories (name, description) VALUES (?, ?)",
                categories
            )

        # Товары
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            products = [
                ('Яблоки Голден', 'Фрукты', 120.0, 'Свежие сладкие яблоки', 50, 0),
                ('Бананы', 'Фрукты', 85.0, 'Спелые бананы', 30, 0),
                ('Помидоры Черри', 'Овощи', 180.0, 'Сладкие помидорки черри', 40, 1),
                ('Огурцы', 'Овощи', 95.0, 'Свежие грунтовые огурцы', 60, 0),
            ]
            cursor.executemany(
                '''INSERT INTO products (name, category, price, description, quantity, is_new) 
                   VALUES (?, ?, ?, ?, ?, ?)''',
                products
            )

        # Раздел "О нас"
        cursor.execute("SELECT COUNT(*) FROM about_us")
        if cursor.fetchone()[0] == 0:
            about_data = [
                ('welcome',
                 '🌿 **Добро пожаловать в наш магазин свежих овощей и фруктов!**\n\nМы работаем с 2018 года, чтобы обеспечивать наших клиентов только самой качественной и свежей продукцией.'),
                ('advantages',
                 '✅ **Наши преимущества:**\n• Свежие продукты с ферм\n• Прямые поставки от производителей\n• Экологически чистая продукция\n• Быстрая доставка (2-3 часа)\n• Гарантия качества\n• Доступные цены'),
                ('mission',
                 '**Наша миссия:**\nМы верим, что здоровое питание должно быть доступным для всех. Наша цель - обеспечить каждого свежими и полезными продуктами прямо к столу.'),
                ('contacts',
                 f'📍 **Контакты:**\n• Адрес: {config.CONTACT_ADDRESS}\n• Телефон: {config.CONTACT_PHONE}\n• Часы работы: {config.WORKING_HOURS}\n• Email: info@freshfoods.ru'),
                ('social',
                 '**Мы в социальных сетях:**\n• Instagram: @freshfoods_shop\n• VK: vk.com/freshfoods\n• Телеграм: @freshfoods_bot')
            ]
            cursor.executemany(
                "INSERT INTO about_us (section, content) VALUES (?, ?)",
                about_data
            )