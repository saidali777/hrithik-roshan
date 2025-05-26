import logging
import os
from collections import defaultdict

from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ChatJoinRequestHandler,
    ContextTypes,
    CommandHandler,
)
from telegram.constants import ParseMode

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store pending join requests per chat_id
pending_requests = defaultdict(list)

# --- Bot Handler Function ---
async def auto_approve_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.chat_join_request:
        chat_id = update.chat_join_request.chat.id
        user = update.chat_join_request.from_user

        # Instead of auto-approving here, store pending and notify user
        pending_requests[chat_id].append(update.chat_join_request)
        logger.info(f"Stored join request from {user.id} in chat {chat_id} (pending)")

        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"👋 Join request from {user.mention_html()} is pending approval.\n"
                    f"An admin can approve all pending requests with /accept"
                ),
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.error(f"Failed to notify pending join request: {e}")

# --- Accept Command Handler ---
async def accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    # Only allow in groups/supergroups
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("This command can only be used in groups.")
        return

    # Check if user is admin
    member = await chat.get_member(user.id)
    if not member.status in ['administrator', 'creator']:
        await update.message.reply_text("You must be an admin to use this command.")
        return

    requests_to_approve = pending_requests.get(chat.id, [])

    if not requests_to_approve:
        await update.message.reply_text("No pending join requests to approve.")
        return

    approved_users = []
    for join_request in requests_to_approve:
        try:
            await join_request.approve()
            approved_users.append(join_request.from_user.mention_html())
        except Exception as e:
            logger.error(f"Failed to approve join request: {e}")

    # Clear the list after approving
    pending_requests[chat.id] = []

    if approved_users:
        await update.message.reply_text(
            f"✅ Approved join requests for:\n" + "\n".join(approved_users),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    else:
        await update.message.reply_text("Failed to approve join requests.")

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
        "👋 Hello! I'm your friendly join request approver bot.\n\n"
        "✅ Add me to any group with join request approval enabled.\n"
        "Use /accept in your group to approve all pending join requests at once.\n\n"
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
application.add_handler(CommandHandler("accept", accept))

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
