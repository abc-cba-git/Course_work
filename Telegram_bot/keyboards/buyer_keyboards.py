from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def get_product_categories_keyboard(categories):
    """Клавиатура с категориями товаров"""
    keyboard = []
    for category in categories:
        keyboard.append([f"📁 {category}"])
    keyboard.append(["🔙 Назад"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cart_keyboard():
    """Клавиатура корзины"""
    keyboard = [
        ["✅ Оформить заказ", "🗑️ Очистить корзину"],
        ["➕ Добавить товары", "🔙 Назад"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_order_confirmation_keyboard():
    """Клавиатура подтверждения заказа"""
    keyboard = [
        ["✅ Подтвердить заказ", "✏️ Изменить заказ"],
        ["🔙 Назад к корзине"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_rating_keyboard(product_name):
    """Inline клавиатура для оценки"""
    keyboard = [
        [
            InlineKeyboardButton("⭐", callback_data=f"rate:{product_name}:1"),
            InlineKeyboardButton("⭐⭐", callback_data=f"rate:{product_name}:2"),
            InlineKeyboardButton("⭐⭐⭐", callback_data=f"rate:{product_name}:3"),
            InlineKeyboardButton("⭐⭐⭐⭐", callback_data=f"rate:{product_name}:4"),
            InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data=f"rate:{product_name}:5"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)