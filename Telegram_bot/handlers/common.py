from telegram import Update
from telegram.ext import ContextTypes
from keyboards.main_keyboards import get_main_menu_keyboard
import config


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    welcome_text = f"""
👋 Привет, {user.full_name}!

Добро пожаловать в {config.SHOP_NAME}!

🛒 Здесь вы можете:
• Просмотреть каталог товаров
• Сделать заказ
• Узнать о нас больше

Выберите действие в меню ниже:
"""

    await update.message.reply_text(welcome_text, reply_markup=get_main_menu_keyboard())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    help_text = f"""
🆘 **Помощь**

📞 Контакты поддержки:
• Телефон: {config.CONTACT_PHONE}
• Адрес: {config.CONTACT_ADDRESS}

❓ **Частые вопросы:**

**Как сделать заказ?**
1. Нажмите "🛒 Каталог"
2. Выберите категорию товаров
3. Добавьте товары в корзину
4. Перейдите в "👤 Личный кабинет" для оформления

**Как отследить заказ?**
Статус заказа будет отправлен вам в Telegram после оформления

**Как вернуть товар?**
Напишите нам в поддержку или воспользуйтесь функцией возврата в личном кабинете

**Есть ли доставка?**
Да, мы осуществляем доставку в течение 2-3 часов

**Какие способы оплаты?**
• Наличными при получении
• Картой онлайн
• Переводом на карту
"""

    await update.message.reply_text(help_text, parse_mode='Markdown')


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    from database.db_operations import AboutOperations

    sections = AboutOperations.get_all_sections()

    about_text = ""
    for section_name, content in sections:
        about_text += f"{content}\n\n"

    await update.message.reply_text(about_text, parse_mode='Markdown')


async def contacts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    contacts_text = f"""
📞 **Контактная информация**

📍 Адрес: {config.CONTACT_ADDRESS}
📱 Телефон: {config.CONTACT_PHONE}
📧 Email: info@freshfoods.ru

"""

    await update.message.reply_text(contacts_text, parse_mode='Markdown')