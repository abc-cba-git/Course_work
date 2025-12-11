import sqlite3
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import json
from datetime import datetime

# Конфигурация
SELLER_PASSWORD = "123"  # Пароль для продавца

# Глобальные словари для хранения данных
cart = {}
user_product_lists = {}
user_states = {}  # Для отслеживания состояния пользователя (возврат, отзыв и т.д.)
seller_sessions = {}  # Для хранения авторизованных продавцов

# Создаем базу данных и таблицу при запуске
def init_database():
    conn = sqlite3.connect('../shop.db')
    cursor = conn.cursor()

    # Создаем таблицу товаров
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            quantity INTEGER DEFAULT 0
        )
    ''')

    # Создаем таблицу отзывов
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

    # Создаем таблицу возвратов
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

    # Создаем таблицу продавцов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sellers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            user_name TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
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

    # Создаем таблицу "О нас" для хранения информации о магазине
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS about_us (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Добавляем тестовые данные для "О нас", если таблица пустая
    cursor.execute("SELECT COUNT(*) FROM about_us")
    if cursor.fetchone()[0] == 0:
        about_us_data = [
            ('main_info',
             '🌿 **Добро пожаловать в наш магазин свежих овощей и фруктов!**\n\nМы работаем с 2018 года, чтобы обеспечивать наших клиентов только самой качественной и свежей продукцией.'),
            ('advantages',
             '✅ **Наши преимущества:**\n• Свежие продукты с ферм и садов\n• Прямые поставки от производителей\n• Экологически чистая продукция\n• Быстрая доставка (2-3 часа)\n• Гарантия качества\n• Доступные цены'),
            ('mission',
             '**Наша миссия:**\nМы верим, что здоровое питание должно быть доступным для всех. Наша цель - обеспечить каждого свежими и полезными продуктами прямо к столу.')
        ]

        cursor.executemany('''
            INSERT INTO about_us (section, content)
            VALUES (?, ?)
        ''', about_us_data)

    # Добавляем тестовые данные для поставщиков, если таблица пустая
    cursor.execute("SELECT COUNT(*) FROM suppliers")
    if cursor.fetchone()[0] == 0:
        suppliers_data = [
            ('Ферма "Яблочный сад"', 'Иван Федоров', '+79161112233', 'apples@farm.ru',
             'Московская обл., д. Садовое', 4.8, 1),
            ('Овощная база "Урожай"', 'Петр Сидоров', '+79162223344', 'vegetables@urozhay.ru',
             'Московская обл., г. Подольск', 4.5, 1),
            ('Ягодная ферма "Лесная"', 'Мария Иванова', '+79163334455', 'berries@forest.ru',
             'Тульская обл., п. Ягодное', 4.9, 1),
            ('Тепличный комплекс "Зеленый"', 'Алексей Петров', '+79164445566', 'greens@greenhouse.ru',
             'Калужская обл., с. Тепличное', 4.3, 1),
            ('Фруктовый опт "Солнечный"', 'Ольга Смирнова', '+79165556677', 'fruits@sunny.ru',
             'Рязанская обл., г. Фруктовый', 4.6, 1),
            ('Органическая ферма "Био"', 'Елена Васнецова', '+79167778899', 'organic@bio.ru',
             'Московская обл., с. Органическое', 5.0, 1),
            ('Грибная ферма "Лесник"', 'Сергей Лесной', '+79168889900', 'mushrooms@forester.ru',
             'Владимирская обл., п. Грибное', 4.4, 1)
        ]

        cursor.executemany('''
            INSERT INTO suppliers (name, contact_person, phone, email, address, rating, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', suppliers_data)

    # Добавляем тестовые данные для товаров, если таблица пустая
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        sample_products = [
            ('Яблоки', 'Фрукты', 100.0, 'Свежие яблоки', 50),
            ('Бананы', 'Фрукты', 80.0, 'Спелые бананы', 30),
            ('Апельсины', 'Фрукты', 120.0, 'Сладкие апельсины', 40),
            ('Помидоры', 'Овощи', 150.0, 'Красные помидоры', 60),
            ('Огурцы', 'Овощи', 90.0, 'Свежие огурцы', 70),
            ('Морковь', 'Овощи', 60.0, 'Сочная морковь', 80),
        ]

        cursor.executemany('''
            INSERT INTO products (name, category, price, description, quantity)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_products)

    conn.commit()
    conn.close()
    print("База данных инициализирована")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    welcome_text = f"""
Привет, {user.full_name}!

Мы очень рады, что ты посетил наш Интернет-магазин, здесь можешь заказать овощи или фрукты, выбери необходимый пункт:

"""
    keyboard = [
        ["Каталог", "О нас"],
        ["Новые продукты", "Наличие в магазине"],
        ["Для покупателя", "Для продавца"]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = """
🌿 Добро пожаловать в наш магазин свежих овощей и фруктов!

Мы работаем, чтобы обеспечивать наших клиентов только самой качественной и свежей продукцией.

✅ Наши преимущества:
• Свежие продукты с ферм и садов
• Прямые поставки от производителей
• Экологически чистая продукция
• Быстрая доставка (2-3 часа)
• Гарантия качества
• Доступные цены

Наша миссия:
Мы верим, что здоровое питание должно быть доступным для всех. Наша цель - обеспечить каждого свежими и полезными продуктами прямо к столу.

"""
    keyboard = [["🔙 В главное меню"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(about_text, reply_markup=reply_markup)

async def catalog_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Все товары", "Фрукты"],
        ["Овощи"],
        ["🔙 В главное меню"]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Каталог товаров. Выберите категорию:",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str | None = update.message.text
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name

    # Инициализируем корзину для пользователя если ее нет
    if user_id not in cart:
        cart[user_id] = {}

    # Самый простой обработчик для кнопки "О нас"
    if text == "О нас":
        await about_command(update, context)
        return

    # Проверяем, ожидает ли пользователь пароль продавца
    if user_id in user_states and user_states[user_id].get('type') == 'waiting_for_seller_password':
        if text == SELLER_PASSWORD:
            # Сохраняем продавца в БД
            conn = sqlite3.connect('../shop.db')
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO sellers (user_id, user_name, is_active)
                    VALUES (?, ?, ?)
                ''', (user_id, user_name, 1))
                conn.commit()
            except:
                cursor.execute('''
                    UPDATE sellers SET is_active = 1 WHERE user_id = ?
                ''', (user_id,))
                conn.commit()
            conn.close()

            # Авторизуем продавца
            seller_sessions[user_id] = True
            del user_states[user_id]

            # Показываем меню продавца
            keyboard = [
                ["📦 Склад", "📝 Товары", "👥 Поставщики"],
                ["ℹ️ О нас", "🔙 В главное меню"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                "✅ Доступ разрешен!\n\n👨‍💼 Добро пожаловать в панель продавца:",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text("❌ Неверный пароль. Попробуйте снова или напишите 'отмена'")
            return

    # Обработка отмены ввода пароля
    elif user_id in user_states and user_states[user_id].get(
            'type') == 'waiting_for_seller_password' and text.lower() == 'отмена':
        del user_states[user_id]
        await update.message.reply_text("❌ Вход в панель продавца отменен")
        await start_command(update, context)
        return

    # Проверяем, авторизован ли пользователь как продавец для доступа к функциям продавца
    elif text == "Для продавца":
        if user_id in seller_sessions and seller_sessions[user_id]:
            # Если уже авторизован, показываем меню
            keyboard = [
                ["📦 Склад", "📝 Товары", "👥 Поставщики"],
                ["ℹ️ О нас", "🔙 В главное меню"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                "👨‍💼 Панель продавца. Выберите раздел:",
                reply_markup=reply_markup
            )
        else:
            # Запрашиваем пароль
            user_states[user_id] = {
                'type': 'waiting_for_seller_password'
            }
            await update.message.reply_text(
                "🔐 Для доступа к панели продавца требуется пароль.\n\n"
                "Пожалуйста, введите пароль:\n"
                "(или напишите 'отмена' для отмены)"
            )
        return

    # Функции продавца (доступны только авторизованным)
    elif text == "📦 Склад" and user_id in seller_sessions and seller_sessions[user_id]:
        await show_stock(update, context)
        return

    elif text == "📝 Товары" and user_id in seller_sessions and seller_sessions[user_id]:
        await manage_products(update, context)
        return

    elif text == "👥 Поставщики" and user_id in seller_sessions and seller_sessions[user_id]:
        await manage_suppliers(update, context)
        return

    elif text == "ℹ️ О нас" and user_id in seller_sessions and seller_sessions[user_id]:
        await manage_about_info(update, context)
        return

    # Добавление товара
    elif text == "➕ Добавить товар" and user_id in seller_sessions and seller_sessions[user_id]:
        user_states[user_id] = {
            'type': 'adding_product',
            'step': 1
        }
        await update.message.reply_text(
            "➕ **Добавление нового товара**\n\n"
            "Введите название товара:"
        )
        return

    # Удаление товара
    elif text == "🗑️ Удалить товар" and user_id in seller_sessions and seller_sessions[user_id]:
        user_states[user_id] = {
            'type': 'deleting_product',
            'step': 1
        }
        await update.message.reply_text(
            "🗑️ **Удаление товара**\n\n"
            "Введите ID товара для удаления:\n"
            "(чтобы посмотреть список товаров с ID, нажмите '📋 Список товаров')"
        )
        return

    # Добавление поставщика
    elif text == "➕ Добавить поставщика" and user_id in seller_sessions and seller_sessions[user_id]:
        user_states[user_id] = {
            'type': 'adding_supplier',
            'step': 1
        }
        await update.message.reply_text(
            "➕ **Добавление нового поставщика**\n\n"
            "Введите название компании/фермы:"
        )
        return

    # Удаление поставщика
    elif text == "🗑️ Удалить поставщика" and user_id in seller_sessions and seller_sessions[user_id]:
        user_states[user_id] = {
            'type': 'deleting_supplier',
            'step': 1
        }
        await update.message.reply_text(
            "🗑️ **Удаление поставщика**\n\n"
            "Введите ID поставщика для удаления:\n"
            "(чтобы посмотреть список поставщиков с ID, нажмите '📋 Список поставщиков')"
        )
        return

    # Список товаров (для продавца)
    elif text == "📋 Список товаров" and user_id in seller_sessions and seller_sessions[user_id]:
        await show_product_list_for_seller(update, context)
        return

    # Список поставщиков (для продавца)
    elif text == "📋 Список поставщиков" and user_id in seller_sessions and seller_sessions[user_id]:
        await show_supplier_list(update, context)
        return

    # Активные поставщики
    elif text == "✅ Активные поставщики" and user_id in seller_sessions and seller_sessions[user_id]:
        await show_active_suppliers(update, context)
        return

    # Лучшие поставщики
    elif text == "⭐ Лучшие поставщики" and user_id in seller_sessions and seller_sessions[user_id]:
        await show_top_suppliers(update, context)
        return

    # Редактирование раздела "О нас"
    elif text.startswith("✏️ Раздел: ") and user_id in seller_sessions and seller_sessions[user_id]:
        section_name = text.replace("✏️ Раздел: ", "")
        user_states[user_id] = {
            'type': 'editing_about_section',
            'section': section_name
        }

        # Получаем текущее содержание раздела
        conn = sqlite3.connect('../shop.db')
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM about_us WHERE section = ?", (section_name,))
        result = cursor.fetchone()
        conn.close()

        current_content = result[0] if result else ""

        await update.message.reply_text(
            f"✏️ **Редактирование раздела: {section_name}**\n\n"
            f"Текущее содержание:\n{current_content}\n\n"
            "Введите новое содержание раздела:"
        )
        return

    # Возврат в меню продавца
    elif text == "🔙 Назад к продавцу" and user_id in seller_sessions and seller_sessions[user_id]:
        keyboard = [
            ["📦 Склад", "📝 Товары", "👥 Поставщики"],
            ["ℹ️ О нас", "🔙 В главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "👨‍💼 Панель продавца. Выберите раздел:",
            reply_markup=reply_markup
        )
        return

    # Возврат к управлению "О нас"
    elif text == "🔙 Назад к управлению" and user_id in seller_sessions and seller_sessions[user_id]:
        await manage_about_info(update, context)
        return

    # Возврат к управлению поставщиками
    elif text == "🔙 Назад к поставщикам" and user_id in seller_sessions and seller_sessions[user_id]:
        await manage_suppliers(update, context)
        return

    # Возврат к просмотру "О нас"
    elif text == "🔙 Назад к просмотру":
        await about_command(update, context)
        return

    # Если пользователь не авторизован, но пытается получить доступ к функциям продавца
    elif any(func in text for func in
             ["📦 Склад", "📝 Товары", "👥 Поставщики", "ℹ️ О нас", "➕ Добавить товар", "🗑️ Удалить товар"]):
        if user_id not in seller_sessions or not seller_sessions[user_id]:
            await update.message.reply_text("❌ Доступ запрещен. Сначала войдите в панель продавца")
            return

    # Обработка состояний пользователя (должно быть перед обработкой цифр!)
    if user_id in user_states:
        state = user_states[user_id]

        # Обработка добавления товара
        if state['type'] == 'adding_product':
            if state['step'] == 1:
                user_states[user_id]['name'] = text
                user_states[user_id]['step'] = 2
                await update.message.reply_text("Введите категорию товара (например: Фрукты, Овощи, Экзотика):")
            elif state['step'] == 2:
                user_states[user_id]['category'] = text
                user_states[user_id]['step'] = 3
                await update.message.reply_text("Введите цену товара (руб.):")
            elif state['step'] == 3:
                try:
                    price = float(text)
                    if price <= 0:
                        raise ValueError
                    user_states[user_id]['price'] = price
                    user_states[user_id]['step'] = 4
                    await update.message.reply_text("Введите описание товара:")
                except ValueError:
                    await update.message.reply_text("❌ Неверная цена. Введите положительное число:")
            elif state['step'] == 4:
                user_states[user_id]['description'] = text
                user_states[user_id]['step'] = 5
                await update.message.reply_text("Введите количество товара на складе:")
            elif state['step'] == 5:
                try:
                    quantity = int(text)
                    if quantity < 0:
                        raise ValueError

                    # Сохраняем товар в БД
                    conn = sqlite3.connect('../shop.db')
                    cursor = conn.cursor()

                    cursor.execute('''
                        INSERT INTO products (name, category, price, description, quantity)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        state['name'],
                        state['category'],
                        state['price'],
                        state['description'],
                        quantity
                    ))

                    conn.commit()
                    conn.close()

                    del user_states[user_id]

                    await update.message.reply_text(
                        f"✅ Товар '{state['name']}' успешно добавлен!\n\n"
                        "Вы можете вернуться к списку товаров через меню продавца."
                    )
                except ValueError:
                    await update.message.reply_text("❌ Неверное количество. Введите целое неотрицательное число:")
            return

        # Обработка удаления товара
        elif state['type'] == 'deleting_product':
            if state['step'] == 1:
                try:
                    product_id = int(text)

                    # Проверяем существование товара
                    conn = sqlite3.connect('../shop.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM products WHERE id = ?", (product_id,))
                    product = cursor.fetchone()

                    if product:
                        # Удаляем товар
                        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
                        conn.commit()
                        conn.close()

                        del user_states[user_id]

                        await update.message.reply_text(
                            f"✅ Товар '{product[0]}' (ID: {product_id}) успешно удален!"
                        )
                    else:
                        await update.message.reply_text(f"❌ Товар с ID {product_id} не найден.")
                        del user_states[user_id]

                except ValueError:
                    await update.message.reply_text("❌ Неверный формат ID. Введите числовой ID товара:")
                return

        # Обработка добавления поставщика
        elif state['type'] == 'adding_supplier':
            if state['step'] == 1:
                user_states[user_id]['name'] = text
                user_states[user_id]['step'] = 2
                await update.message.reply_text("Введите контактное лицо:")
            elif state['step'] == 2:
                user_states[user_id]['contact_person'] = text
                user_states[user_id]['step'] = 3
                await update.message.reply_text("Введите телефон (например: +79161234567):")
            elif state['step'] == 3:
                user_states[user_id]['phone'] = text
                user_states[user_id]['step'] = 4
                await update.message.reply_text("Введите email:")
            elif state['step'] == 4:
                user_states[user_id]['email'] = text
                user_states[user_id]['step'] = 5
                await update.message.reply_text("Введите адрес:")
            elif state['step'] == 5:
                user_states[user_id]['address'] = text
                user_states[user_id]['step'] = 6
                await update.message.reply_text("Введите рейтинг (от 0.0 до 5.0, например: 4.5):")
            elif state['step'] == 6:
                try:
                    rating = float(text)
                    if rating < 0 or rating > 5:
                        raise ValueError

                    # Сохраняем поставщика в БД
                    conn = sqlite3.connect('../shop.db')
                    cursor = conn.cursor()

                    cursor.execute('''
                        INSERT INTO suppliers (name, contact_person, phone, email, address, rating, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        state['name'],
                        state['contact_person'],
                        state['phone'],
                        state['email'],
                        state['address'],
                        rating,
                        1  # Активный по умолчанию
                    ))

                    conn.commit()
                    conn.close()

                    del user_states[user_id]

                    await update.message.reply_text(
                        f"✅ Поставщик '{state['name']}' успешно добавлен!\n\n"
                        "Вы можете вернуться к списку поставщиков через меню продавца."
                    )
                except ValueError:
                    await update.message.reply_text("❌ Неверный рейтинг. Введите число от 0.0 до 5.0:")
            return

        # Обработка удаления поставщика
        elif state['type'] == 'deleting_supplier':
            if state['step'] == 1:
                try:
                    supplier_id = int(text)

                    # Проверяем существование поставщика
                    conn = sqlite3.connect('../shop.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM suppliers WHERE id = ?", (supplier_id,))
                    supplier = cursor.fetchone()

                    if supplier:
                        # Деактивируем поставщика вместо удаления
                        cursor.execute("UPDATE suppliers SET is_active = 0 WHERE id = ?", (supplier_id,))
                        conn.commit()
                        conn.close()

                        del user_states[user_id]

                        await update.message.reply_text(
                            f"✅ Поставщик '{supplier[0]}' (ID: {supplier_id}) деактивирован!"
                        )
                    else:
                        await update.message.reply_text(f"❌ Поставщик с ID {supplier_id} не найден.")
                        del user_states[user_id]

                except ValueError:
                    await update.message.reply_text("❌ Неверный формат ID. Введите числовой ID поставщика:")
                return

        # Обработка редактирования раздела "О нас"
        elif state['type'] == 'editing_about_section':
            section = state['section']
            new_content = text

            # Обновляем раздел в базе данных
            conn = sqlite3.connect('../shop.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO about_us (section, content)
                VALUES (?, ?)
            ''', (section, new_content))

            conn.commit()
            conn.close()

            del user_states[user_id]

            await update.message.reply_text(
                f"✅ Раздел '{section}' успешно обновлен!\n\n"
                "Вы можете просмотреть изменения в разделе 'О нас'."
            )

            # Возвращаемся к управлению
            await manage_about_info(update, context)
            return

        # Обработка возврата товара
        elif state['type'] == 'waiting_for_return_reason':
            # Сохраняем запрос на возврат
            conn = sqlite3.connect('../shop.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO returns (user_id, user_name, order_details, reason, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, user_name, state['order_details'], text, 'pending'))

            conn.commit()
            conn.close()

            del user_states[user_id]

            await update.message.reply_text(
                "✅ Ваш запрос на возврат принят!\n\n"
                "Наш менеджер свяжется с вами в течение 24 часов для уточнения деталей.\n"
                "Спасибо за обращение!"
            )
            return

        # Обработка отзыва
        elif state['type'] == 'waiting_for_review':
            # Сохраняем отзыв
            conn = sqlite3.connect('../shop.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO reviews (user_id, user_name, product_name, rating, review_text)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, user_name, state.get('product'), state.get('rating', 5), text))

            conn.commit()
            conn.close()

            del user_states[user_id]

            await update.message.reply_text(
                "⭐ Спасибо за ваш отзыв!\n\n"
                "Ваше мнение очень важно для нас и поможет улучшить наш сервис."
            )
            return

    # ТОЛЬКО ПОСЛЕ обработки всех состояний проверяем цифры!
    if text.isdigit():
        # Проверяем, есть ли у пользователя список товаров
        if user_id in user_product_lists:
            product_index = int(text) - 1
            product_list = user_product_lists[user_id]

            if 0 <= product_index < len(product_list):
                name, price, quantity = product_list[product_index]

                # Проверяем, есть ли товар на складе
                if quantity > 0:
                    # Добавляем товар в корзину
                    if name in cart[user_id]:
                        cart[user_id][name] += 1
                    else:
                        cart[user_id][name] = 1

                    cart_quantity = cart[user_id][name]
                    await update.message.reply_text(
                        f"✅ {name} добавлен в корзину!\nКоличество в корзине: {cart_quantity} шт.\nЦена: {price} руб.")
                else:
                    await update.message.reply_text(f"❌ {name} закончился на складе.")
            else:
                await update.message.reply_text(f"❌ Нет товара с номером {text}. Выберите номер из списка.")
        else:
            await update.message.reply_text("Сначала выберите категорию товаров.")
        return

    # Основной обработчик сообщений продолжается...
    if text == "Каталог":
        await catalog_command(update, context)

    elif text == "Все товары":
        conn = sqlite3.connect('../shop.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, price, quantity FROM products")
        products = cursor.fetchall()
        conn.close()

        if products:
            response = "Все товары:\n\n"
            user_product_lists[user_id] = []

            for i, (name, price, quantity) in enumerate(products, 1):
                response += f"{i}. {name} - {price} руб. (осталось: {quantity} шт.)\n"
                user_product_lists[user_id].append((name, price, quantity))

            response += "\n👇 Чтобы добавить товар, напишите его номер (1, 2, 3...):"
            keyboard = [["🔙 Назад"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(response, reply_markup=reply_markup)

    # Добавьте также проверку в оформлении заказа:
    elif text == "✅ Оформить заказ":
        if cart[user_id]:
            # Проверяем наличие всех товаров перед оформлением
            conn = sqlite3.connect('../shop.db')
            cursor = conn.cursor()

            unavailable_items = []
            available_items = []

            for product_name, quantity in cart[user_id].items():
                cursor.execute("SELECT quantity FROM products WHERE name = ?", (product_name,))
                result = cursor.fetchone()
                if result:
                    available_quantity = result[0]
                    if available_quantity < quantity:
                        unavailable_items.append(
                            f"{product_name} (требуется: {quantity}, в наличии: {available_quantity})")
                    else:
                        available_items.append((product_name, quantity))

            if unavailable_items:
                response = "❌ Невозможно оформить заказ:\n"
                for item in unavailable_items:
                    response += f"• {item}\n"
                response += "\nПожалуйста, измените количество или удалите эти товары из корзины."
                await update.message.reply_text(response)
            elif available_items:
                # Сохраняем детали заказа в контексте для возможного возврата
                order_details = ""
                total_price = 0

                for product_name, quantity in available_items:
                    cursor.execute("SELECT price FROM products WHERE name = ?", (product_name,))
                    result = cursor.fetchone()
                    if result:
                        price = result[0]
                        item_total = price * quantity
                        total_price += item_total
                        order_details += f"• {product_name} - {quantity} шт. × {price} руб.\n"

                        # Обновляем количество на складе
                        cursor.execute(
                            "UPDATE products SET quantity = quantity - ? WHERE name = ?",
                            (quantity, product_name)
                        )

                # Сохраняем заказ в истории пользователя
                if 'orders' not in context.user_data:
                    context.user_data['orders'] = []

                order_data = {
                    'items': available_items,
                    'total': total_price,
                    'details': order_details
                }
                context.user_data['orders'].append(order_data)

                conn.commit()

                response = f"✅ Заказ оформлен!\n\nСостав заказа:\n{order_details}\n💰 Итого: {total_price} руб.\n\nЗаказ будет доставлен в течение 2 часов."

                # Очищаем корзину после оформления заказа
                cart[user_id] = {}

                keyboard = [["🔙 В главное меню"]]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                await update.message.reply_text(response, reply_markup=reply_markup)

            conn.close()
        else:
            await update.message.reply_text("Корзина пуста, добавьте товары")

    elif text == "🛒 Моя корзина":
        await show_cart(update, user_id)

    # Обработка удаления товара из корзины (например: "1-" или "2-")
    elif text.endswith('-') and text[:-1].isdigit():
        if cart[user_id]:
            item_index = int(text[:-1]) - 1
            cart_items = list(cart[user_id].items())

            if 0 <= item_index < len(cart_items):
                product_name, quantity = cart_items[item_index]

                if quantity > 1:
                    cart[user_id][product_name] -= 1
                    await update.message.reply_text(
                        f"✅ Удален 1 шт. {product_name}\nОсталось: {cart[user_id][product_name]} шт.")
                else:
                    del cart[user_id][product_name]
                    await update.message.reply_text(f"✅ Товар {product_name} полностью удален из корзины")
            else:
                await update.message.reply_text(f"❌ Нет товара с номером {item_index + 1} в корзине")

    # Очистка корзины
    elif text == "❌ Очистить корзины":
        cart[user_id] = {}
        await update.message.reply_text("✅ Корзина очищена")

    # Добавить еще товары
    elif text == "➕ Добавить еще товары":
        keyboard = [
            ["Все товары", "Фрукты", "Овощи"],
            ["🔙 Назад"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Выберите категорию:", reply_markup=reply_markup)

    # Кнопка "Назад"
    elif text == "🔙 Назад":
        await catalog_command(update, context)

    # Кнопка "🔙 В главное меню"
    elif text == "🔙 В главное меню":
        # Выход из режима продавца
        if user_id in seller_sessions:
            seller_sessions[user_id] = False
        await start_command(update, context)

    # Остальные обработчики...
    elif text == "Фрукты":
        conn = sqlite3.connect('../shop.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, price, quantity FROM products WHERE category = 'Фрукты'")
        products = cursor.fetchall()
        conn.close()

        if products:
            response = "🍎 Фрукты:\n\n"
            # Сохраняем список товаров для этого пользователя
            user_product_lists[user_id] = []

            for i, (name, price, quantity) in enumerate(products, 1):
                response += f"{i}. {name} - {price} руб. (осталось: {quantity} шт.)\n"
                user_product_lists[user_id].append((name, price, quantity))

            response += "\n👇 Чтобы добавить товар, напишите его номер (1, 2, 3...):"
            keyboard = [["🔙 Назад"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(response, reply_markup=reply_markup)
        else:
            await update.message.reply_text("Фруктов пока нет")

    elif text == "Овощи":
        conn = sqlite3.connect('../shop.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, price, quantity FROM products WHERE category = 'Овощи'")
        products = cursor.fetchall()
        conn.close()

        if products:
            response = "🥦 Овощи:\n\n"
            # Сохраняем список товаров для этого пользователя
            user_product_lists[user_id] = []

            for i, (name, price, quantity) in enumerate(products, 1):
                response += f"{i}. {name} - {price} руб. (осталось: {quantity} шт.)\n"
                user_product_lists[user_id].append((name, price, quantity))

            response += "\n👇 Чтобы добавить товар, напишите его номер (1, 2, 3...):"
            keyboard = [["🔙 Назад"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(response, reply_markup=reply_markup)
        else:
            await update.message.reply_text("Овощей пока нет")

    # Остальные существующие обработчики...
    elif text == "Наличие в магазине":
        conn = sqlite3.connect('../shop.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, quantity FROM products WHERE quantity > 0")
        products = cursor.fetchall()
        conn.close()

        if products:
            response = "📊 Наличие товаров:\n\n"
            for i, (name, quantity) in enumerate(products, 1):
                response += f"{i}. {name} - {quantity} шт.\n"
        else:
            response = "Все товары закончились"

        await update.message.reply_text(response)

    elif text == "Новые продукты":
        conn = sqlite3.connect('../shop.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, price, description FROM products ORDER BY id DESC LIMIT 3")
        products = cursor.fetchall()
        conn.close()

        if products:
            response = "🆕 Новые продукты:\n\n"
            for i, (name, price, description) in enumerate(products, 1):
                response += f"{i}. {name} - {price} руб.\n  {description}\n\n"
        else:
            response = "Новых продуктов пока нет"

        await update.message.reply_text(response)

    elif text == "Для покупателя":
        keyboard = [
            ["🛒 Моя корзина"],
            ["🔄 Возврат товара", "⭐ Оставить отзыв"],
            ["📁 Категории товаров"],
            ["🔙 В главное меню"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Раздел для покупателя. Выберите что вас интересует:",
            reply_markup=reply_markup
        )

    elif text == "📁 Категории товаров":
        conn = sqlite3.connect('../shop.db')
        cursor = conn.cursor()
        cursor.execute("SELECT category, COUNT(*) as count FROM products GROUP BY category")
        categories = cursor.fetchall()
        conn.close()

        response = "📁 Категории товаров:\n\n"
        for category, count in categories:
            response += f"• {category} - {count} товаров\n"

        response += "\nВыберите категорию в каталоге для просмотра товаров"

        keyboard = [["Каталог", "🔙 Назад"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(response, reply_markup=reply_markup)

    elif text == "🔄 Возврат товара":
        await handle_return_request(update, context)

    elif text == "⭐ Оставить отзыв":
        await handle_review_request(update, context)

    # Если ни один из обработчиков не сработал
    else:
        await update.message.reply_text("Я не понял ваш запрос. Пожалуйста, используйте кнопки меню.")

async def show_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('../shop.db')
    cursor = conn.cursor()

    # Общее количество товаров
    cursor.execute("SELECT COUNT(*), SUM(quantity) FROM products")
    total_products, total_items = cursor.fetchone()

    # Товары с низким запасом
    cursor.execute("SELECT name, quantity FROM products WHERE quantity < 10 ORDER BY quantity ASC")
    low_stock = cursor.fetchall()

    # Категории товаров
    cursor.execute("SELECT category, SUM(quantity) FROM products GROUP BY category")
    categories = cursor.fetchall()

    conn.close()

    response = "📦 Склад\n\n"
    response += f"📊 Общая статистика:\n"
    response += f"• Всего товаров: {total_products}\n"
    response += f"• Общее количество: {total_items or 0} шт.\n\n"

    response += "📁 По категориям:\n"
    for category, qty in categories:
        response += f"• {category}: {qty} шт.\n"

    if low_stock:
        response += "\n⚠️ Требуется пополнение:\n"
        for name, qty in low_stock:
            response += f"• {name}: {qty} шт.\n"
    else:
        response += "\n✅ Все товары в наличии"

    await update.message.reply_text(response)

async def manage_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["➕ Добавить товар", "🗑️ Удалить товар"],
        ["📋 Список товаров"],
        ["🔙 Назад к продавцу"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "📝 Управление товарами. Выберите действие:",
        reply_markup=reply_markup
    )

async def manage_suppliers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["➕ Добавить поставщика", "🗑️ Удалить поставщика"],
        ["📋 Список поставщиков", "✅ Активные поставщики"],
        ["⭐ Лучшие поставщики"],
        ["🔙 Назад к продавцу"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👥 Управление поставщиками. Выберите действие:",
        reply_markup=reply_markup
    )

async def show_product_list_for_seller(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('../shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, category, price, quantity FROM products ORDER BY id")
    products = cursor.fetchall()
    conn.close()

    if products:
        response = "📋 Список товаров (с ID):\n\n"
        for product in products:
            response += f"ID: {product[0]}\n"
            response += f"Название: {product[1]}\n"
            response += f"Категория: {product[2]}\n"
            response += f"Цена: {product[3]} руб.\n"
            response += f"Количество: {product[4]} шт.\n"
            response += "─" * 30 + "\n\n"
    else:
        response = "📋 Список товаров пуст"

    keyboard = [["🔙 Назад к продавцу"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(response, reply_markup=reply_markup)

async def show_supplier_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('../shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, contact_person, phone, email, address, rating, is_active FROM suppliers ORDER BY id")
    suppliers = cursor.fetchall()
    conn.close()

    if suppliers:
        response = "📋 Список поставщиков:\n\n"
        for supplier in suppliers:
            response += f"ID: {supplier[0]}\n"
            response += f"Название: {supplier[1]}\n"
            response += f"Контактное лицо: {supplier[2]}\n"
            response += f"Телефон: {supplier[3]}\n"
            response += f"Email: {supplier[4]}\n"
            response += f"Адрес: {supplier[5]}\n"
            response += f"Рейтинг: {supplier[6]}\n"
            status = "✅ Активен" if supplier[7] == 1 else "❌ Не активен"
            response += f"Статус: {status}\n"
            response += "─" * 30 + "\n\n"
    else:
        response = "📋 Список поставщиков пуст"

    keyboard = [["🔙 Назад к поставщикам"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(response, reply_markup=reply_markup)

async def show_active_suppliers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('../shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, contact_person, phone, rating FROM suppliers WHERE is_active = 1 ORDER BY name")
    suppliers = cursor.fetchall()
    conn.close()

    if suppliers:
        response = "✅ Активные поставщики:\n\n"
        for supplier in suppliers:
            response += f"🏢 {supplier[0]}\n"
            response += f"👤 Контакт: {supplier[1]}\n"
            response += f"📞 Телефон: {supplier[2]}\n"
            response += f"⭐ Рейтинг: {supplier[3]}\n"
            response += "─" * 20 + "\n\n"
    else:
        response = "Нет активных поставщиков"

    keyboard = [["🔙 Назад к поставщикам"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(response, reply_markup=reply_markup)

async def show_top_suppliers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('../shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, rating, contact_person, phone FROM suppliers WHERE is_active = 1 AND rating >= 4.5 ORDER BY rating DESC")
    suppliers = cursor.fetchall()
    conn.close()

    if suppliers:
        response = "⭐ Лучшие поставщики (рейтинг ≥ 4.5):\n\n"
        for supplier in suppliers:
            stars = "⭐" * int(supplier[1]) + "☆" * (5 - int(supplier[1]))
            response += f"{stars} {supplier[1]}\n"
            response += f"🏢 {supplier[0]}\n"
            response += f"👤 {supplier[2]}\n"
            response += f"📞 {supplier[3]}\n"
            response += "─" * 20 + "\n\n"
    else:
        response = "Нет поставщиков с высоким рейтингом"

    keyboard = [["🔙 Назад к поставщикам"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(response, reply_markup=reply_markup)

async def manage_about_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем список разделов из базы данных
    conn = sqlite3.connect('../shop.db')
    cursor = conn.cursor()

    cursor.execute("SELECT section FROM about_us ORDER BY id")
    sections = cursor.fetchall()
    conn.close()

    if not sections:
        response = "ℹ️ **Управление информацией о магазине**\n\n"
        response += "Разделы еще не созданы. Сначала добавьте разделы через базу данных."

        keyboard = [["🔙 Назад к продавцу"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(response, reply_markup=reply_markup)
        return

    response = "ℹ️ **Управление информацией о магазине**\n\n"
    response += "Выберите раздел для редактирования:\n\n"

    keyboard = []
    for section in sections:
        # Отображаем названия разделов в более читаемом виде
        section_name = section[0]
        display_name = section_name.replace('_', ' ').title()
        keyboard.append([f"✏️ Раздел: {section_name}"])

    keyboard.append(["🔙 Назад к продавцу"])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(response, reply_markup=reply_markup)

async def handle_return_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Проверяем, есть ли у пользователя заказы
    if 'orders' not in context.user_data or not context.user_data['orders']:
        await update.message.reply_text(
            "У вас пока нет заказов для возврата.\n"
            "Сначала оформите заказ в нашем магазине."
        )
        return

    # Показываем последний заказ
    last_order = context.user_data['orders'][-1]

    response = "🔄 Запрос на возврат товара\n\n"
    response += "Ваш последний заказ:\n"
    response += last_order['details']
    response += f"\n💰 Сумма: {last_order['total']} руб.\n\n"

    response += "Пожалуйста, напишите причину возврата товара:\n"
    response += "(например: товар испорчен, не соответствует описанию, передумал и т.д.)"

    # Сохраняем состояние пользователя
    user_states[user_id] = {
        'type': 'waiting_for_return_reason',
        'order_details': last_order['details']
    }

    await update.message.reply_text(response)

async def handle_review_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Получаем список товаров для отзыва
    conn = sqlite3.connect('../shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM products ORDER BY name")
    products = cursor.fetchall()
    conn.close()

    if not products:
        await update.message.reply_text("Пока нет товаров для отзыва")
        return

    # Создаем клавиатуру с товарами
    keyboard = []
    for product in products:
        keyboard.append([InlineKeyboardButton(product[0], callback_data=f"review_product:{product[0]}")])

    keyboard.append([InlineKeyboardButton("Наш магазин в целом", callback_data="review_product:general")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "⭐ Оставить отзыв\n\n"
        "Выберите товар для отзыва или напишите отзыв о нашем магазине в целом:",
        reply_markup=reply_markup
    )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data.startswith("review_product:"):
        product = query.data.split(":")[1]

        # Создаем клавиатуру для оценки
        keyboard = [
            [
                InlineKeyboardButton("⭐", callback_data=f"rating:{product}:1"),
                InlineKeyboardButton("⭐⭐", callback_data=f"rating:{product}:2"),
                InlineKeyboardButton("⭐⭐⭐", callback_data=f"rating:{product}:3"),
                InlineKeyboardButton("⭐⭐⭐⭐", callback_data=f"rating:{product}:4"),
                InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data=f"rating:{product}:5"),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        if product == "general":
            await query.edit_message_text(
                "⭐ Отзыв о нашем магазине\n\n"
                "Пожалуйста, оцените наш магазин:",
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                f"⭐ Отзыв о товаре: {product}\n\n"
                "Пожалуйста, оцените товар:",
                reply_markup=reply_markup
            )

    elif query.data.startswith("rating:"):
        parts = query.data.split(":")
        product = parts[1]
        rating = int(parts[2])

        user_states[user_id] = {
            'type': 'waiting_for_review',
            'product': product if product != "general" else None,
            'rating': rating
        }

        if product == "general":
            await query.edit_message_text(
                f"Вы поставили оценку: {'⭐' * rating}\n\n"
                "Теперь напишите ваш отзыв о нашем магазине:\n"
                "(что вам понравилось, что можно улучшить и т.д.)"
            )
        else:
            await query.edit_message_text(
                f"Вы поставили товару '{product}' оценку: {'⭐' * rating}\n\n"
                "Теперь напишите ваш отзыв об этом товаре:\n"
                "(качество, вкус, свежесть, соответствие описанию и т.д.)"
            )

async def show_cart(update: Update, user_id: int):
    if user_id in cart and cart[user_id]:
        response = "🛒 Ваша корзина:\n\n"
        total_price = 0
        item_count = 1

        conn = sqlite3.connect('../shop.db')
        cursor = conn.cursor()

        for product_name, quantity in cart[user_id].items():
            cursor.execute("SELECT price FROM products WHERE name = ?", (product_name,))
            result = cursor.fetchone()
            if result:
                price = result[0]
                item_total = price * quantity
                total_price += item_total
                response += f"{item_count}. {product_name} - {quantity} шт. × {price} руб. = {item_total} руб.\n"
                item_count += 1

        conn.close()

        response += f"\n💰 Итого: {total_price} руб.\n\n"
        response += "Чтобы удалить товар, напишите его номер и минус (например: 1- или 2-)"

        keyboard = [
            ["✅ Оформить заказ", "❌ Очистить корзину"],
            ["➕ Добавить еще товары", "🔙 Назад"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(response, reply_markup=reply_markup)
    else:
        keyboard = [["➕ Добавить еще товары", "🔙 Назад"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Ваша корзина пуста", reply_markup=reply_markup)

def main():
    # Инициализируем базу данных
    init_database()

    # ЗАМЕНИТЕ ТОКЕН НА ВАШ РЕАЛЬНЫЙ ТОКЕН
    TOKEN = "8533297173:AAGvNL7zpOjWYFDAQrVoV8VYkGowCf7Ly-A"

    # Создаем приложение
    application = Application.builder().token(TOKEN).build()

    # Добавляем обработчик команды /start
    application.add_handler(CommandHandler("start", start_command))

    # Добавляем обработчик команды /about (на всякий случай)
    application.add_handler(CommandHandler("about", about_command))

    # /catalog
    application.add_handler(CommandHandler("catalog", catalog_command))

    # Добавляем обработчик callback запросов
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Добавляем обработчик текстовых сообщений (кнопок)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    print("Бот запущен...")
    print(f"Пароль для продавца: {SELLER_PASSWORD}")
    print("База данных создана: shop.db")
    print("Ожидание сообщений...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()