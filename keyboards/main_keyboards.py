from telegram import ReplyKeyboardMarkup

def get_main_menu_keyboard():

    keyboard = [
        ["🛒 Каталог", "📋 Новинки"],
        ["ℹ️ О нас"],
        ["👤 Личный кабинет"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_buyer_menu_keyboard():

    keyboard = [
        ["🛍️ Товары по категориям"],
        ["📦 Мои заказы", "⭐ Отзывы"],
        ["🔄 Возврат товара", "❓ Помощь"],
        ["🔙 Главное меню"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_seller_menu_keyboard():

    keyboard = [
        ["📦 Управление складом", "📝 Товары"],
        ["ℹ️ Управление 'О нас'", "📊 Статистика"],
        ["👥 Клиенты"],
        ["🔙 Главное меню"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard():

    keyboard = [["🔙 Назад"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_catalog_keyboard():

    keyboard = [
        ["🍎 Фрукты", "🥦 Овощи"],
        ["🔙 Главное меню"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)