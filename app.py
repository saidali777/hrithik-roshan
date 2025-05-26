import logging
import os

from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes
from telegram.constants import ParseMode
from telegram.ext import Dispatcher

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Telegram Bot Logic ---
async def auto_approve_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.chat_join_request:
        await update.chat_join_request.approve()
        logger.info(f"Approved join request from {update.chat_join_request.from_user.id} in chat {update.chat_join_request.chat.id}")

        try:
            await context.bot.send_message(
                chat_id=update.chat_join_request.chat.id,
                text=f"Welcome, {update.chat_join_request.from_user.mention_html()}! Your join request has been approved.",
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Sent welcome message to {update.chat_join_request.from_user.id}")
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")

# --- Create Telegram Application ---
def create_telegram_application():
    bot_token = os.environ.get('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN environment variable not set. Please set it to run the bot.")
        return None

    application = ApplicationBuilder().token(bot_token).build()
    application.add_handler(ChatJoinRequestHandler(auto_approve_join_request))
    return application

telegram_app = create_telegram_application()

# --- Flask App for Gunicorn Deployment ---
app = Flask(__name__)

@app.route('/')
def index():
    return "Telegram bot is running!"

@app.route('/webhook', methods=['POST'])
async def webhook():
    if telegram_app:
        try:
            update = Update.de_json(request.get_json(force=True), telegram_app.bot)
            await telegram_app.update_queue.put(update)
            return "OK", 200
        except Exception as e:
            logger.error(f"Error handling update: {e}")
            return "Error", 500
    else:
        return "Bot not configured", 500
