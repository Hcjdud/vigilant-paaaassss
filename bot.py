# bot.py
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
SITE_URL = os.environ.get('SITE_URL', 'https://vailae.onrender.com')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет сообщение с кнопкой WebApp"""
    keyboard = [[
        InlineKeyboardButton(
            text="🚀 Открыть Vailae",
            web_app=WebAppInfo(url=SITE_URL)
        )
    ]]
    
    await update.message.reply_text(
        "👋 Добро пожаловать в Vailae!\n\n"
        "Нажми кнопку ниже, чтобы открыть приложение:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь"""
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start - Открыть Vailae\n"
        "/help - Помощь"
    )

def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set!")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    print(f"✅ Bot started! Open https://t.me/{(app.bot.username)}")
    app.run_polling()

if __name__ == '__main__':
    main()
