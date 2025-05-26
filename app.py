import logging
import os

from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes
from telegram.constants import ParseMode

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Bot Handler Function ---
async def auto_approve_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.chat_join_request:
        await update.chat_join_request.approve()
        user = update.chat_join_request.from_user
        chat = update.chat_join_request.chat

        logger.info(f"Approved join request from {user.id} in chat {chat.id}")

        try:
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"Welcome, {user.mention_html()}! Your join request has been approved.",
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Sent welcome message to {user.id}")
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")

# --- Build Telegram Application ---
bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    raise RuntimeError("BOT_TOKEN environment variable not set.")

application = ApplicationBuilder().token(bot_token).build()
application.add_handler(ChatJoinRequestHandler(auto_approve_join_request))

# --- Flask App ---
app = Flask(__name__)

@app.route('/')
def index():
    return "🤖 Telegram bot is running!", 200

@app.route('/webhook', methods=['POST'])
async def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.update_queue.put(update)
        return "OK", 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Webhook error", 500
