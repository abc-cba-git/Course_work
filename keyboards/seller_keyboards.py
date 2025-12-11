from telegram import ReplyKeyboardMarkup

def get_seller_products_keyboard():

    keyboard = [
        ["➕ Добавить товар"],
        ["🗑️ Удалить товар", "📋 Список товаров"],
        ["🔙 В меню продавца"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_stock_management_keyboard():

    keyboard = [
        ["Добавить товар", "Удалить товар"]
        ["📊 Статистика"],
        ["🔙 В меню продавца"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_about_management_keyboard(sections):

    keyboard = []
    for section in sections:
        keyboard.append([f"✏️ {section}"])
    keyboard.append(["🔙 В меню продавца"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)