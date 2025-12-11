import json

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from keyboards.buyer_keyboards import *
from keyboards.main_keyboards import get_main_menu_keyboard, get_back_keyboard, get_catalog_keyboard
from database.db_operations import ProductOperations, ReviewOperations
import config

from Telegram_bot.keyboards.buyer_keyboards import get_cart_keyboard

# Глобальные словари для хранения состояния пользователей
user_carts = {}
user_states = {}


async def buyer_catalog_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🛒 **Каталог товаров**\n\nВыберите категорию:",
        reply_markup=get_catalog_keyboard(),
        parse_mode='Markdown'
    )


async def show_new_products(update: Update, context: ContextTypes.DEFAULT_TYPE):

    new_products = ProductOperations.get_new_products()

    if not new_products:
        await update.message.reply_text(
            "🌟 Пока нет новых товаров. Загляните позже!",
            reply_markup=get_back_keyboard()
        )
        return

    response = "🌟 **Новые поступления:**\n\n"

    for product in new_products:
        product_id, name, category, price, description, quantity, is_new, created_at = product
        response += f"🆕 **{name}**\n"
        response += f"📁 Категория: {category}\n"
        response += f"💰 Цена: {price} руб.\n"
        response += f"📝 {description}\n"
        response += f"📦 В наличии: {quantity} шт.\n"
        response += "─" * 30 + "\n\n"

    keyboard = [
        ["🛒 В каталог", "⭐ Посмотреть отзывы"],
        ["🔙 Главное меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')


async def show_products_by_category(update: Update, context: ContextTypes.DEFAULT_TYPE, category=None):

    if category is None:
        category = update.message.text.replace("📁 ", "")

    products = ProductOperations.get_products_by_category(category)

    if not products:
        await update.message.reply_text(
            f"В категории '{category}' пока нет товаров",
            reply_markup=get_back_keyboard()
        )
        return

    response = f"📁 **{category}**\n\n"
    user_id = update.effective_user.id

    # Сохраняем список товаров для этого пользователя
    user_states[user_id] = {
        'type': 'viewing_products',
        'products': [],
        'category': category
    }

    for i, product in enumerate(products, 1):
        product_id, name, category, price, description, quantity, is_new, created_at = product
        response += f"{i}. **{name}**\n"
        response += f"   💰 {price} руб.\n"
        response += f"   📝 {description}\n"
        response += f"   📦 Осталось: {quantity} шт.\n"

        if is_new:
            response += "   🆕 **НОВИНКА!**\n"

        user_states[user_id]['products'].append(product_id)


        response += f"   [Подробнее](https://t.me/{context.bot.username}?start=product_{product_id})\n\n"

    response += "\n👇 Напишите номер товара, чтобы добавить его в корзину"

    keyboard = [
        ["🛒 В корзину", "⭐ Оставить отзыв"],
        ["🔙 Назад к категориям"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')


async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    text = update.message.text

    if not text.isdigit():
        await update.message.reply_text("Пожалуйста, введите номер товара (цифру)")
        return

    product_index = int(text) - 1

    if user_id not in user_states or 'products' not in user_states[user_id]:
        await update.message.reply_text("Сначала выберите категорию товаров")
        return

    if not 0 <= product_index < len(user_states[user_id]['products']):
        await update.message.reply_text(f"Нет товара с номером {text}")
        return

    product_id = user_states[user_id]['products'][product_index]
    product = ProductOperations.get_product_by_id(product_id)

    if not product:
        await update.message.reply_text("Товар не найден")
        return


    if user_id not in user_carts:
        user_carts[user_id] = {}

    product_name = product[1]
    product_price = product[3]


    if product_id in user_carts[user_id]:
        user_carts[user_id][product_id]['quantity'] += 1
    else:
        user_carts[user_id][product_id] = {
            'name': product_name,
            'price': product_price,
            'quantity': 1
        }

    cart_item = user_carts[user_id][product_id]

    await update.message.reply_text(
        f"✅ **{product_name}** добавлен в корзину!\n"
        f"Количество: {cart_item['quantity']} шт.\n"
        f"Сумма: {cart_item['quantity'] * cart_item['price']} руб."
    )


async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in user_carts or not user_carts[user_id]:
        await update.message.reply_text(
            "🛒 Ваша корзина пуста",
            reply_markup=get_cart_keyboard()
        )
        return

    response = "🛒 **Ваша корзина:**\n\n"
    total = 0

    for product_id, item in user_carts[user_id].items():
        item_total = item['quantity'] * item['price']
        total += item_total
        response += f"• {item['name']}\n"
        response += f"  Количество: {item['quantity']} шт.\n"
        response += f"  Цена: {item['price']} руб. × {item['quantity']} = {item_total} руб.\n"
        response += f"  [Удалить](https://t.me/{context.bot.username}?start=remove_{product_id})\n\n"

    response += f"💰 **Итого: {total} руб.**\n\n"

    if total < 500:
        response += f"⚠️ Минимальная сумма заказа: 500 руб.\nДобавьте товаров еще на {500 - total} руб.\n"

    await update.message.reply_text(
        response,
        reply_markup=get_cart_keyboard(),
        parse_mode='Markdown'
    )


async def place_order(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    user_name = update.effective_user.full_name

    if user_id not in user_carts or not user_carts[user_id]:
        await update.message.reply_text("Ваша корзина пуста")
        return

    # Проверяем наличие товаров
    unavailable_items = []
    order_items = []
    total = 0

    for product_id, item in user_carts[user_id].items():
        product = ProductOperations.get_product_by_id(product_id)
        if not product:
            unavailable_items.append(f"{item['name']} - товар не найден")
            continue

        available_quantity = product[5]  # quantity field
        if available_quantity < item['quantity']:
            unavailable_items.append(
                f"{item['name']} (нужно {item['quantity']}, в наличии {available_quantity})"
            )
        else:
            item_total = item['quantity'] * item['price']
            total += item_total
            order_items.append({
                'product_id': product_id,
                'name': item['name'],
                'quantity': item['quantity'],
                'price': item['price'],
                'total': item_total
            })

    if unavailable_items:
        response = "❌ **Невозможно оформить заказ:**\n\n"
        for item in unavailable_items:
            response += f"• {item}\n"
        response += "\nПожалуйста, измените состав корзины"
        await update.message.reply_text(response)
        return

    if total < 500:
        await update.message.reply_text(
            f"Минимальная сумма заказа 500 руб.\nВаша сумма: {total} руб.\n"
            f"Добавьте товаров еще на {500 - total} руб."
        )
        return

    # Сохраняем заказ
    from database.db_operations import db
    conn = db.get_connection()
    cursor = conn.cursor()

    # Обновляем количество на складе
    for item in order_items:
        cursor.execute(
            "UPDATE products SET quantity = quantity - ? WHERE id = ?",
            (item['quantity'], item['product_id'])
        )

    # Сохраняем заказ
    items_json = json.dumps(order_items)
    cursor.execute('''
        INSERT INTO orders (user_id, user_name, items, total_price, status)
        VALUES (?, ?, ?, ?, 'new')
    ''', (user_id, user_name, items_json, total))

    order_id = cursor.lastrowid
    conn.commit()
    conn.close()


    user_carts[user_id] = {}


    order_details = "✅ **Заказ оформлен!**\n\n"
    order_details += f"📦 Номер заказа: #{order_id}\n"
    order_details += f"👤 Клиент: {user_name}\n\n"
    order_details += "**Состав заказа:**\n"

    for item in order_items:
        order_details += f"• {item['name']} - {item['quantity']} шт. × {item['price']} руб.\n"

    order_details += f"\n💰 **Сумма: {total} руб.**\n\n"
    order_details += "⏱️ **Доставка:** в течение 2-3 часов\n"
    order_details += "📞 **Связь:** с вами свяжется наш оператор\n"
    order_details += "\nСпасибо за заказ! 🛒"

    await update.message.reply_text(
        order_details,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )