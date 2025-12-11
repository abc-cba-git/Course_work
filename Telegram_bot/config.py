# Конфигурация бота
import os
from dotenv import load_dotenv

load_dotenv()

# Настройки бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "8533297173:AAGvNL7zpOjWYFDAQrVoV8VYkGowCf7Ly-A")
SELLER_PASSWORD = "123"

# Настройки базы данных
DATABASE_NAME = "shop.db"