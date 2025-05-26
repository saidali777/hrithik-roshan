import logging
import os
import asyncio
import threading
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    ChatJoinRequestHandler,
    CommandHandler,
)

# --- Logging Setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- Data Stores ---
pending_requests = {}
auto_accept_chats = set()

# --- Handlers ---
async def auto_approve_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.chat_join_request:
        return

    chat_id = update.chat_join_request.chat.id
    user = update.chat_join_request.from_user

    # Store join request
    if chat_id not in pending_requests:
        pending_requests[chat_id] = []
    pending_requests[chat_id].append(update.chat_join_request)

    logger.info(f"Join request from {user.id} in chat {chat_id} received.")

    if chat_id in auto_accept_chats:
        try:
            await update.chat_join_request.approve()
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Welcome, {user.mention_html()}! Your join request has been approved.",
                parse_mode=ParseMode.HTML,
            )
            pending_requests[chat_id].remove(update.chat_join_request)
            logger.info(f"Auto-approved join request from {user.id} in chat {chat_id}.")
        except Exception as e:
            logger.error(f"Failed to auto-approve join request from {user.id}: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_username = context.bot.username
    keyboard = [
        [InlineKeyboardButton("➕ Add Bot to Group", url=f"https://t.me/{bot_username}?startgroup=true")],
        [InlineKeyboardButton("👥 Support Group", url="https://t.me/colonel_support")],
        [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/YOUR_USERNAME_HERE")],  # Replace this
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    intro_text = (
        "👋 Hello! I'm your friendly auto-join request approval bot.\n\n"
        "✅ Add me to groups with join requests enabled and I can automatically approve users!\n\n"
        "Use /accept command in a group to start auto-approving all pending join requests instantly.\n\n"
        "Use the buttons below to add me or visit support."
    )

    await update.message.reply_text(intro_text, reply_markup=reply_markup)

async def accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ This command can only be used in groups.")
        return

    bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
    if not bot_member.can_invite_users:
        await update.message.reply_text(
            "❌ I need 'Invite Users' permission to approve join requests. Please promote me as admin with full rights."
        )
        return

    auto_accept_chats.add(chat.id)

    count = 0
    if chat.id in pending_requests:
        for join_request in pending_requests[chat.id][:]:
            try:
                await join_request.approve()
                user = join_request.from_user
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=f"✅ Welcome, {user.mention_html()}!",
                    parse_mode=ParseMode.HTML,
                )
                pending_requests[chat.id].remove(join_request)
                count += 1
            except Exception as e:
                logger.error(f"Error approving join request for user {join_request.from_user.id}: {e}")

    await update.message.reply_text(f"✅ Auto-accept enabled.\nApproved {count} pending requests.")

# --- Flask + Telegram App Setup ---
bot_token = os.getenv("BOT_TOKEN")
if not bot_token:
    raise RuntimeError("BOT_TOKEN environment variable not set.")

application = ApplicationBuilder().token(bot_token).build()
application.add_handler(ChatJoinRequestHandler(auto_approve_join_request))
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("accept", accept))

# --- Flask App ---
app = Flask(__name__)

@app.route("/")
def index():
    return "🤖 Telegram bot is running!", 200

@app.route("/webhook", methods=["POST"])
async def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.update_queue.put(update)
        return "OK", 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Webhook error", 500

# --- Start Telegram Application in Background ---
def run_telegram():
    asyncio.run(application.initialize())
    application.post_init()
    application.start()

threading.Thread(target=run_telegram).start()
