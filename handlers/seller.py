from telegram import Update
from telegram.ext import ContextTypes
from keyboards.main_keyboards import get_main_menu_keyboard, get_back_keyboard
from database.db_operations import SellerOperations, ProductOperations, AboutOperations
import config

from keyboards.main_keyboards import get_seller_menu_keyboard
from keyboards.seller_keyboards import get_stock_management_keyboard, get_seller_products_keyboard, \
    get_about_management_keyboard

user_states = {}


async def seller_login(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if SellerOperations.is_seller(user_id):
        # Продавец уже авторизован
        await show_seller_menu(update, context)
        return

    user_states[user_id] = {
        'type': 'waiting_for_seller_password'
    }

    await update.message.reply_text(
        "🔐 **Авторизация продавца**\n\n"
        "Пожалуйста, введите пароль для доступа к панели продавца:"
    )


async def handle_seller_password(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_states or user_states[user_id].get('type') != 'waiting_for_seller_password':
        return

    if text == config.SELLER_PASSWORD:

        user_name = update.effective_user.full_name
        SellerOperations.add_seller(user_id, user_name)

        del user_states[user_id]
        await show_seller_menu(update, context)
    elif text.lower() == 'отмена':
        del user_states[user_id]
        await update.message.reply_text(
            "❌ Авторизация отменена",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ Неверный пароль. Попробуйте еще раз или напишите 'отмена'"
        )


async def show_seller_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = get_seller_menu_keyboard()
    await update.message.reply_text(
        "👨‍💼 **Панель продавца**\n\n"
        "Выберите раздел для управления:",
        reply_markup=keyboard
    )


async def show_stock_info(update: Update, context: ContextTypes.DEFAULT_TYPE):

    stock_info = SellerOperations.get_stock_info()

    response = "📦 **Информация о складе**\n\n"
    response += f"📊 **Общая статистика:**\n"
    response += f"• Всего товаров: {stock_info['total_products']}\n"
    response += f"• Общее количество: {stock_info['total_quantity']} шт.\n\n"

    response += "📁 **По категориям:**\n"
    for category, quantity in stock_info['categories']:
        response += f"• {category}: {quantity} шт.\n"

    if stock_info['low_stock']:
        response += "\n⚠️ **Товары с низким запасом:**\n"
        for name, quantity in stock_info['low_stock']:
            response += f"• {name}: {quantity} шт.\n"
    else:
        response += "\n✅ **Все товары в достаточном количестве**"

    await update.message.reply_text(response, reply_markup=get_stock_management_keyboard())


async def manage_products(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📝 **Управление товарами**\n\n"
        "Выберите действие:",
        reply_markup=get_seller_products_keyboard()
    )


async def show_product_list(update: Update, context: ContextTypes.DEFAULT_TYPE):

    products = ProductOperations.get_all_products()

    if not products:
        await update.message.reply_text(
            "📋 Список товаров пуст",
            reply_markup=get_seller_products_keyboard()
        )
        return

    response = "📋 **Список товаров:**\n\n"

    for product in products:
        product_id, name, category, price, description, quantity, is_new, created_at = product
        response += f"🆔 **ID: {product_id}**\n"
        response += f"📦 {name}\n"
        response += f"📁 Категория: {category}\n"
        response += f"💰 Цена: {price} руб.\n"
        response += f"📦 Количество: {quantity} шт.\n"

        if is_new:
            response += "🏷️ Статус: НОВИНКА\n"

        response += f"📅 Добавлен: {created_at[:10]}\n"
        response += "─" * 30 + "\n\n"

    await update.message.reply_text(response, reply_markup=get_seller_products_keyboard())


async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    user_states[user_id] = {
        'type': 'adding_product',
        'step': 1
    }

    await update.message.reply_text(
        "➕ **Добавление нового товара**\n\n"
        "Введите название товара:"
    )


async def manage_about_info(update: Update, context: ContextTypes.DEFAULT_TYPE):

    sections = AboutOperations.get_all_sections()

    if not sections:
        await update.message.reply_text(
            "ℹ️ Раздел 'О нас' еще не настроен",
            reply_markup=get_back_keyboard()
        )
        return

    section_names = [section[0] for section in sections]

    await update.message.reply_text(
        "ℹ️ **Управление разделом 'О нас'**\n\n"
        "Выберите раздел для редактирования:",
        reply_markup=get_about_management_keyboard(section_names)
    )


async def edit_about_section(update: Update, context: ContextTypes.DEFAULT_TYPE, section_name):

    user_id = update.effective_user.id

    # Получаем текущее содержание
    sections = AboutOperations.get_all_sections()
    current_content = ""

    for section, content in sections:
        if section == section_name:
            current_content = content
            break

    user_states[user_id] = {
        'type': 'editing_about_section',
        'section': section_name
    }

    await update.message.reply_text(
        f"✏️ **Редактирование раздела: {section_name}**\n\n"
        f"Текущее содержание:\n{current_content}\n\n"
        "Введите новое содержание:"
    )