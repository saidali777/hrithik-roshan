import logging
import os

from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes, CommandHandler
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

# --- Start Command Handler ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_username = context.bot.username
    keyboard = [
        [InlineKeyboardButton("➕ Add Bot to Group", url=f"https://t.me/{bot_username}?startgroup=true")],
        [InlineKeyboardButton("👥 Support Group", url="https://t.me/colonel_support")],
        [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/YOUR_USERNAME_HERE")]  # Replace with your Telegram username
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    intro_text = (
        "👋 Hello! I'm your friendly auto-pending request approver bot.\n\n"
        "✅ Add me to any group with join request approval enabled, and I’ll automatically approve pending users!\n\n"
        "Use the buttons below to get started:"
    )

    await update.message.reply_text(intro_text, reply_markup=reply_markup)

# --- Build Telegram Application ---
bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    raise RuntimeError("BOT_TOKEN environment variable not set.")

application = ApplicationBuilder().token(bot_token).build()
application.add_handler(ChatJoinRequestHandler(auto_approve_join_request))
application.add_handler(CommandHandler("start", start))

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
